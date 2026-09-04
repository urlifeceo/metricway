from datetime import datetime, date
from typing import List
from fastapi import APIRouter, Query, HTTPException
from app.core.clickhouse import get_ch_client
from app.schemas.analytics import (
    DAUResponse,
    ActivityPoint,
    FinancialMetricsResponse,
    UTMMetric,
    TrafficMetric,
    TrafficSpendRequest,
    ProductMapping,
    ProductMappingRequest,
    UnknownProduct,
    FunnelStep,
    CohortRetention,
)
from app.utils.date import (
    get_default_from_date,
    normalize_to_date,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/dau", response_model=List[DAUResponse])
def get_dau(
    project_token: str,
    from_date: datetime = Query(default_factory=get_default_from_date),
    to_date: datetime = Query(default_factory=datetime.now),
):
    to_date = normalize_to_date(to_date)
    client = get_ch_client()
    
    query = """
        SELECT
            toDate(ts) AS date,
            uniqExact(user_id) AS dau
        FROM tgmetrics.events
        WHERE project_token = {project_token:String}
          AND toDate(ts) >= toDate({from_date:DateTime}) 
          AND toDate(ts) <= toDate({to_date:DateTime})
        GROUP BY date
        ORDER BY date ASC
    """
    result = client.query(
        query,
        parameters={
            "project_token": project_token,
            "from_date": from_date,
            "to_date": to_date,
        },
    )

    return [DAUResponse(date=row[0], dau=row[1]) for row in result.result_rows]


@router.get("/activity", response_model=List[ActivityPoint])
def get_activity(
    project_token: str,
    granularity: str = Query("dau", pattern="^(dau|wau|mau)$"),
    from_date: datetime = Query(default_factory=get_default_from_date),
    to_date: datetime = Query(default_factory=datetime.now),
):
    to_date = normalize_to_date(to_date)
    client = get_ch_client()

    bucket_expr = {
        "dau": "toDate(ts)",
        "wau": "toMonday(ts)",
        "mau": "toStartOfMonth(ts)",
    }[granularity]

    query = f"""
        SELECT
            {bucket_expr} AS bucket,
            uniqExact(user_id) AS value
        FROM tgmetrics.events
        WHERE project_token = {{project_token:String}}
          AND toDate(ts) >= toDate({{from_date:DateTime}})
          AND toDate(ts) <= toDate({{to_date:DateTime}})
        GROUP BY bucket
        ORDER BY bucket ASC
    """
    result = client.query(
        query,
        parameters={
            "project_token": project_token,
            "from_date": from_date,
            "to_date": to_date,
        },
    )

    return [ActivityPoint(date=row[0], value=row[1]) for row in result.result_rows]


@router.get("/financials", response_model=FinancialMetricsResponse)
def get_financials(
    project_token: str,
    from_date: datetime = Query(default_factory=get_default_from_date),
    to_date: datetime = Query(default_factory=datetime.now),
):
    to_date = normalize_to_date(to_date)
    client = get_ch_client()
    
    stats_query = """
        SELECT
            sum(amount) AS total_revenue,
            uniqExact(user_id) AS paying_users
        FROM tgmetrics.purchases
        WHERE project_token = {project_token:String}
          AND ts >= {from_date:DateTime} 
          AND ts <= {to_date:DateTime}
    """
    stats_res = client.query(
        stats_query,
        parameters={
            "project_token": project_token,
            "from_date": from_date,
            "to_date": to_date,
        },
    ).first_row

    total_revenue = stats_res[0] or 0.0
    paying_users = stats_res[1] or 0

    users_query = """
        SELECT count() FROM (
            SELECT user_id
            FROM tgmetrics.users_meta
            WHERE project_token = {project_token:String}
            GROUP BY user_id
            HAVING min(first_seen_ts) <= {to_date:DateTime}
               AND max(last_seen_ts) >= {from_date:DateTime}
        )
    """
    users_res = client.query(
        users_query,
        parameters={
            "project_token": project_token,
            "from_date": from_date,
            "to_date": to_date,
        },
    ).first_row

    total_users = users_res[0] if users_res else 0

    arpu = round(total_revenue / total_users, 2) if total_users > 0 else 0.0
    arppu = round(total_revenue / paying_users, 2) if paying_users > 0 else 0.0
    conversion_rate = round((paying_users / total_users) * 100, 2) if total_users > 0 else 0.0

    mrr_query = """
        WITH product_map AS (
            SELECT
                product_id,
                argMax(billing_type, updated_at) AS billing_type
            FROM tgmetrics.products
            WHERE project_token = {project_token:String}
            GROUP BY product_id
        )
        SELECT
            sum(monthly_eq) AS mrr,
            count() AS active_subscriptions
        FROM (
            SELECT
                p.user_id AS user_id,
                max(multiIf(
                    pm.billing_type = 'yearly', p.amount / 12,
                    pm.billing_type = 'monthly', p.amount,
                    0
                )) AS monthly_eq
            FROM tgmetrics.purchases AS p
            LEFT JOIN product_map AS pm ON p.product_id = pm.product_id
            WHERE p.project_token = {project_token:String}
              AND p.ts >= now() - INTERVAL 31 DAY
            GROUP BY user_id
            HAVING monthly_eq > 0
        )
    """
    mrr_res = client.query(
        mrr_query,
        parameters={
            "project_token": project_token,
        },
    ).first_row

    mrr = round(mrr_res[0] or 0.0, 2)
    active_subscriptions = mrr_res[1] or 0
    arr = round(mrr * 12, 2)

    churn_query = """
        WITH product_map AS (
            SELECT
                product_id,
                argMax(billing_type, updated_at) AS billing_type
            FROM tgmetrics.products
            WHERE project_token = {project_token:String}
            GROUP BY product_id
        )
        SELECT
            count() AS sub_users,
            countIf(last_sub_ts < now() - INTERVAL 31 DAY) AS churned
        FROM (
            SELECT
                p.user_id AS user_id,
                max(p.ts) AS last_sub_ts
            FROM tgmetrics.purchases AS p
            INNER JOIN product_map AS pm ON p.product_id = pm.product_id
            WHERE p.project_token = {project_token:String}
              AND pm.billing_type IN ('monthly', 'yearly')
            GROUP BY user_id
        )
    """
    churn_res = client.query(
        churn_query,
        parameters={
            "project_token": project_token,
        },
    ).first_row

    sub_users_ever = churn_res[0] or 0
    churned = churn_res[1] or 0
    churn_rate = round((churned / sub_users_ever) * 100, 2) if sub_users_ever > 0 else 0.0

    forecast_ltv = round(arppu / (churn_rate / 100), 2) if churn_rate > 0 else arppu

    spend_query = """
        SELECT sum(spend) AS total_spend
        FROM (
            SELECT
                utm_source,
                argMax(spend, updated_at) AS spend
            FROM tgmetrics.traffic_costs
            WHERE project_token = {project_token:String}
            GROUP BY utm_source
        )
    """
    spend_res = client.query(
        spend_query,
        parameters={
            "project_token": project_token,
        },
    ).first_row

    total_spend = spend_res[0] or 0.0
    cac = round(total_spend / paying_users, 2) if paying_users > 0 and total_spend > 0 else 0.0
    ltv_cac_ratio = round(forecast_ltv / cac, 2) if cac > 0 else 0.0

    cr_first_query = """
        SELECT
            count() AS new_users,
            countIf(has_purchase = 1) AS new_buyers
        FROM (
            SELECT
                nu.user_id AS user_id,
                (pb.user_id != 0) AS has_purchase
            FROM (
                SELECT user_id
                FROM tgmetrics.users_meta
                WHERE project_token = {project_token:String}
                GROUP BY user_id
                HAVING min(first_seen_ts) >= {from_date:DateTime}
                   AND min(first_seen_ts) <= {to_date:DateTime}
            ) AS nu
            LEFT JOIN (
                SELECT DISTINCT user_id
                FROM tgmetrics.purchases
                WHERE project_token = {project_token:String}
            ) AS pb ON nu.user_id = pb.user_id
        )
    """
    cr_first_res = client.query(
        cr_first_query,
        parameters={
            "project_token": project_token,
            "from_date": from_date,
            "to_date": to_date,
        },
    ).first_row

    new_users = cr_first_res[0] or 0
    new_buyers = cr_first_res[1] or 0
    cr_first = round((new_buyers / new_users) * 100, 2) if new_users > 0 else 0.0

    cr_repeat_query = """
        SELECT
            uniqExact(user_id) AS paying,
            uniqExactIf(user_id, payments >= 2) AS repeat
        FROM (
            SELECT
                user_id,
                count() AS payments
            FROM tgmetrics.purchases
            WHERE project_token = {project_token:String}
              AND ts >= {from_date:DateTime}
              AND ts <= {to_date:DateTime}
            GROUP BY user_id
        )
    """
    cr_repeat_res = client.query(
        cr_repeat_query,
        parameters={
            "project_token": project_token,
            "from_date": from_date,
            "to_date": to_date,
        },
    ).first_row

    paying = cr_repeat_res[0] or 0
    repeat = cr_repeat_res[1] or 0
    cr_repeat = round((repeat / paying) * 100, 2) if paying > 0 else 0.0

    return FinancialMetricsResponse(
        total_revenue=total_revenue,
        paying_users=paying_users,
        total_users=total_users,
        arpu=arpu,
        arppu=arppu,
        conversion_rate=conversion_rate,
        mrr=mrr,
        arr=arr,
        active_subscriptions=active_subscriptions,
        churn_rate=churn_rate,
        forecast_ltv=forecast_ltv,
        ltv_cac_ratio=ltv_cac_ratio,
        cr_first=cr_first,
        cr_repeat=cr_repeat,
    )


@router.get("/utm", response_model=List[UTMMetric])
def get_utm_performance(
    project_token: str,
    from_date: datetime = Query(default_factory=get_default_from_date),
    to_date: datetime = Query(default_factory=datetime.now),
):
    to_date = normalize_to_date(to_date)
    client = get_ch_client()
    
    query = """
        WITH deduplicated_traffic AS (
            SELECT
                user_id,
                any(utm_source) AS source,
                any(utm_campaign) AS campaign
            FROM tgmetrics.traffic
            WHERE project_token = {project_token:String}
              AND first_seen_ts >= {from_date:DateTime} 
              AND first_seen_ts <= {to_date:DateTime}
            GROUP BY user_id
        )
        SELECT
            t.source AS source,
            t.campaign AS campaign,
            countDistinct(t.user_id) AS acquisitions,
            countDistinct(p.user_id) AS buyers,
            sum(p.amount) AS revenue,
            round((buyers / nullIf(acquisitions, 0)) * 100, 2) AS conversion_rate
        FROM deduplicated_traffic AS t
        LEFT JOIN tgmetrics.purchases AS p 
               ON p.project_token = {project_token:String} 
              AND t.user_id = p.user_id
              AND p.ts >= {from_date:DateTime}
              AND p.ts <= {to_date:DateTime}
        GROUP BY source, campaign
        ORDER BY revenue DESC
    """
    result = client.query(
        query,
        parameters={
            "project_token": project_token,
            "from_date": from_date,
            "to_date": to_date,
        },
    )

    return [
        UTMMetric(
            source=row[0],
            campaign=row[1],
            acquisitions=row[2],
            buyers=row[3],
            revenue=row[4] or 0.0,
            conversion_rate=row[5] or 0.0,
        )
        for row in result.result_rows
    ]


@router.get("/traffic", response_model=List[TrafficMetric])
def get_traffic(
    project_token: str,
    from_date: datetime = Query(default_factory=get_default_from_date),
    to_date: datetime = Query(default_factory=datetime.now),
):
    to_date = normalize_to_date(to_date)
    client = get_ch_client()

    traffic_query = """
        WITH deduplicated_traffic AS (
            SELECT
                user_id,
                any(utm_source) AS source
            FROM tgmetrics.traffic
            WHERE project_token = {project_token:String}
              AND first_seen_ts >= {from_date:DateTime}
              AND first_seen_ts <= {to_date:DateTime}
            GROUP BY user_id
        )
        SELECT
            t.source AS source,
            countDistinct(t.user_id) AS acquisitions,
            countDistinct(p.user_id) AS buyers,
            round((countDistinct(p.user_id) / nullIf(countDistinct(t.user_id), 0)) * 100, 2) AS conversion_rate
        FROM deduplicated_traffic AS t
        LEFT JOIN tgmetrics.purchases AS p
               ON p.project_token = {project_token:String}
              AND t.user_id = p.user_id
              AND p.ts >= {from_date:DateTime}
              AND p.ts <= {to_date:DateTime}
        GROUP BY source
        ORDER BY acquisitions DESC
    """
    traffic_result = client.query(
        traffic_query,
        parameters={
            "project_token": project_token,
            "from_date": from_date,
            "to_date": to_date,
        },
    )

    spend_query = """
        SELECT
            utm_source,
            argMax(spend, updated_at) AS spend
        FROM tgmetrics.traffic_costs
        WHERE project_token = {project_token:String}
        GROUP BY utm_source
    """
    spend_result = client.query(
        spend_query,
        parameters={
            "project_token": project_token,
        },
    )
    spends = {row[0]: (row[1] or 0.0) for row in spend_result.result_rows}

    metrics = []
    for source, acquisitions, buyers, conversion_rate in traffic_result.result_rows:
        spend = spends.get(source, 0.0)
        cac = round(spend / buyers, 2) if buyers > 0 and spend > 0 else 0.0
        metrics.append(
            TrafficMetric(
                source=source,
                acquisitions=acquisitions,
                buyers=buyers,
                conversion_rate=conversion_rate or 0.0,
                spend=spend,
                cac=cac,
            )
        )

    return metrics


@router.put("/traffic/spend")
def update_traffic_spend(request: TrafficSpendRequest):
    if request.spend < 0:
        raise HTTPException(status_code=400, detail="spend must be >= 0")

    client = get_ch_client()
    client.insert(
        "tgmetrics.traffic_costs",
        [[request.project_token, request.source, request.spend, datetime.now()]],
        column_names=["project_token", "utm_source", "spend", "updated_at"],
    )

    return {"status": "ok"}


@router.get("/products", response_model=List[ProductMapping])
def get_products(project_token: str):
    client = get_ch_client()

    query = """
        SELECT
            product_id,
            argMax(billing_type, updated_at) AS billing_type
        FROM tgmetrics.products
        WHERE project_token = {project_token:String}
        GROUP BY product_id
        ORDER BY product_id ASC
    """
    result = client.query(
        query,
        parameters={"project_token": project_token},
    )

    return [
        ProductMapping(product_id=row[0], billing_type=row[1])
        for row in result.result_rows
    ]


@router.put("/products")
def update_product_mapping(request: ProductMappingRequest):
    if request.billing_type not in ("monthly", "yearly", "one_time"):
        raise HTTPException(
            status_code=400,
            detail="billing_type must be one of: monthly, yearly, one_time",
        )

    client = get_ch_client()
    client.insert(
        "tgmetrics.products",
        [[request.project_token, request.product_id, request.billing_type, datetime.now()]],
        column_names=["project_token", "product_id", "billing_type", "updated_at"],
    )

    return {"status": "ok"}


@router.get("/products/unknown", response_model=List[UnknownProduct])
def get_unknown_products(project_token: str):
    client = get_ch_client()

    query = """
        WITH product_map AS (
            SELECT
                product_id,
                argMax(billing_type, updated_at) AS billing_type
            FROM tgmetrics.products
            WHERE project_token = {project_token:String}
            GROUP BY product_id
        )
        SELECT
            p.product_id AS product_id,
            count() AS payments_count,
            argMax(p.amount, p.ts) AS last_amount
        FROM tgmetrics.purchases AS p
        LEFT JOIN product_map AS pm ON p.product_id = pm.product_id
        WHERE p.project_token = {project_token:String}
          AND pm.billing_type = ''
        GROUP BY product_id
        ORDER BY payments_count DESC
    """
    result = client.query(
        query,
        parameters={"project_token": project_token},
    )

    return [
        UnknownProduct(
            product_id=row[0],
            payments_count=row[1],
            last_amount=row[2] or 0.0,
        )
        for row in result.result_rows
    ]


@router.get("/retention", response_model=List[CohortRetention])
def get_retention(
    project_token: str,
    unit: str = Query("day", pattern="^(day|month)$"),
    from_date: datetime = Query(default_factory=get_default_from_date),
    to_date: datetime = Query(default_factory=datetime.now),
):
    to_date = normalize_to_date(to_date)
    client = get_ch_client()

    if unit == "month":
        query = """
            WITH
                [0, 1, 2, 3, 4, 5, 6] AS target_months,

                users_cohorts AS (
                    SELECT
                        user_id,
                        toStartOfMonth(min(first_seen_ts)) AS cohort_month
                    FROM tgmetrics.users_meta
                    WHERE project_token = {project_token:String}
                    GROUP BY user_id
                    HAVING cohort_month >= toStartOfMonth({from_date:DateTime})
                       AND cohort_month <= toStartOfMonth({to_date:DateTime})
                ),

                retention_raw AS (
                    SELECT
                        toString(u.cohort_month) AS cohort_id,
                        dateDiff('month', u.cohort_month, toStartOfMonth(e.ts)) AS period_number,
                        e.user_id AS user_id
                    FROM users_cohorts AS u
                    INNER JOIN tgmetrics.events AS e
                        ON e.project_token = {project_token:String}
                       AND e.user_id = u.user_id
                       AND e.ts >= u.cohort_month
                    WHERE dateDiff('month', u.cohort_month, toStartOfMonth(e.ts)) IN target_months
                ),

                cohort_sizes AS (
                    SELECT
                        toString(cohort_month) AS cohort_id,
                        uniqExact(user_id) AS cohort_size
                    FROM users_cohorts
                    GROUP BY cohort_id
                ),

                active_per_period AS (
                    SELECT
                        cohort_id,
                        period_number,
                        uniqExact(user_id) AS active_users
                    FROM retention_raw
                    GROUP BY cohort_id, period_number
                )

            SELECT
                c.cohort_id,
                c.cohort_size,
                groupArray(a.period_number) AS active_periods,
                groupArray(a.active_users) AS active_users
            FROM cohort_sizes AS c
            LEFT JOIN active_per_period AS a ON c.cohort_id = a.cohort_id
            GROUP BY c.cohort_id, c.cohort_size
            ORDER BY c.cohort_id ASC
        """
    else:
        query = """
            WITH
                [0, 1, 3, 7, 14, 30] AS target_days,

                users_cohorts AS (
                    SELECT 
                        user_id, 
                        toDate(min(first_seen_ts)) AS first_seen_date
                    FROM tgmetrics.users_meta
                    WHERE project_token = {project_token:String}
                    GROUP BY user_id
                    HAVING first_seen_date >= toDate({from_date:DateTime})
                       AND first_seen_date <= toDate({to_date:DateTime})
                ),

                retention_raw AS (
                    SELECT
                        toString(u.first_seen_date) AS cohort_id,
                        dateDiff('day', u.first_seen_date, e.ts) AS period_number,
                        e.user_id AS user_id
                    FROM users_cohorts AS u
                    INNER JOIN tgmetrics.events AS e 
                        ON e.project_token = {project_token:String} 
                       AND e.user_id = u.user_id 
                       AND e.ts >= u.first_seen_date
                    WHERE dateDiff('day', u.first_seen_date, e.ts) IN target_days
                ),

                cohort_sizes AS (
                    SELECT 
                        toString(first_seen_date) AS cohort_id,
                        uniqExact(user_id) AS cohort_size
                    FROM users_cohorts
                    GROUP BY cohort_id
                ),

                active_per_period AS (
                    SELECT
                        cohort_id,
                        period_number,
                        uniqExact(user_id) AS active_users
                    FROM retention_raw
                    GROUP BY cohort_id, period_number
                )

            SELECT
                c.cohort_id,
                c.cohort_size,
                groupArray(a.period_number) AS active_periods,
                groupArray(a.active_users) AS active_users
            FROM cohort_sizes AS c
            LEFT JOIN active_per_period AS a ON c.cohort_id = a.cohort_id
            GROUP BY c.cohort_id, c.cohort_size
            ORDER BY c.cohort_id ASC
        """

    result = client.query(
        query,
        parameters={
            "project_token": project_token,
            "from_date": from_date,
            "to_date": to_date,
        },
    )

    retention_list: List[CohortRetention] = []

    for cohort_id, cohort_size, periods, counts in result.result_rows:
        retention = {
            int(p): (
                round((cnt / cohort_size) * 100, 2)
                if cohort_size > 0 and cnt is not None
                else 0.0
            )
            for p, cnt in zip(periods, counts)
        }

        retention_list.append(
            CohortRetention(
                cohort_date=str(cohort_id),
                cohort_size=cohort_size,
                retention=retention,
            )
        )

    return retention_list


@router.get("/funnel", response_model=List[FunnelStep])
def get_funnel(
    project_token: str,
    steps: List[str] = Query(..., description="Массив шагов"),
    from_date: datetime = Query(default_factory=get_default_from_date),
    to_date: datetime = Query(default_factory=datetime.now),
):
    if not steps:
        return []

    to_date = normalize_to_date(to_date)
    client = get_ch_client()

    conds = []
    for step in steps:
        safe_step = step.replace("'", "''")
        if safe_step.startswith("Inline: "):
            cb_data = safe_step.replace("Inline: ", "")
            conds.append(
                f"(lower(update_type) = 'callbackquery' AND callback_data = '{cb_data}')"
            )
        else:
            conds.append(
                f"((handler = '{safe_step}') OR (lower(update_type) = 'message' AND text = '{safe_step}'))"
            )

    cond_str = ", ".join(conds)

    query = f"""
        SELECT 
            level,
            count() AS count
        FROM (
            SELECT 
                user_id,
                windowFunnel(604800)(toDateTime(ts), {cond_str}) AS max_step
            FROM tgmetrics.events
            WHERE project_token = {{project_token:String}}
              AND ts >= {{from_date:DateTime}} AND ts <= {{to_date:DateTime}}
            GROUP BY user_id
        )
        ARRAY JOIN range(1, max_step + 1) AS level
        GROUP BY level
        ORDER BY level ASC
    """

    result = client.query(
        query,
        parameters={
            "project_token": project_token,
            "from_date": from_date,
            "to_date": to_date,
        },
    )

    counts_map = {row[0]: row[1] for row in result.result_rows}
    step_counts = [counts_map.get(i + 1, 0) for i in range(len(steps))]
    first_step_users = step_counts[0] if step_counts and step_counts[0] > 0 else 0

    return [
        FunnelStep(
            step_name=steps[i],
            users_count=count,
            conversion_rate=round((count / first_step_users) * 100, 2) if first_step_users > 0 else 0.0,
        )
        for i, count in enumerate(step_counts)
    ]


@router.get("/funnel/events", response_model=List[str])
def get_funnel_events(project_token: str):
    client = get_ch_client()
    query = """
        SELECT DISTINCT event_name
        FROM (
            SELECT handler AS event_name
            FROM tgmetrics.events
            WHERE project_token = {project_token:String} AND handler != ''
            
            UNION ALL
            
            SELECT concat('Inline: ', callback_data) AS event_name
            FROM tgmetrics.events
            WHERE project_token = {project_token:String} 
              AND lower(update_type) = 'callbackquery'
              AND callback_data != ''
        )
        ORDER BY event_name ASC
        LIMIT 100
    """
    result = client.query(query, parameters={"project_token": project_token})
    return [row[0] for row in result.result_rows]