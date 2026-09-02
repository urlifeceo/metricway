from datetime import datetime, date
from typing import List
from fastapi import APIRouter, Query, HTTPException
from app.core.clickhouse import get_ch_client
from app.schemas.analytics import (
    DAUResponse,
    FinancialMetricsResponse,
    UTMMetric,
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

    return FinancialMetricsResponse(
        total_revenue=total_revenue,
        paying_users=paying_users,
        total_users=total_users,
        arpu=arpu,
        arppu=arppu,
        conversion_rate=conversion_rate,
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


@router.get("/retention", response_model=List[CohortRetention])
def get_retention(
    project_token: str,
    from_date: datetime = Query(default_factory=get_default_from_date),
    to_date: datetime = Query(default_factory=datetime.now),
):
    client = get_ch_client()

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
                    toString(u.first_seen_date) AS cohort_day,
                    dateDiff('day', u.first_seen_date, e.ts) AS day_number,
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
                    toString(first_seen_date) AS cohort_day,
                    uniqExact(user_id) AS cohort_size
                FROM users_cohorts
                GROUP BY cohort_day
            ),

            active_per_day AS (
                SELECT
                    cohort_day,
                    day_number,
                    uniqExact(user_id) AS active_users
                FROM retention_raw
                GROUP BY cohort_day, day_number
            )

        SELECT
            c.cohort_day,
            c.cohort_size,
            groupArray(a.day_number) AS active_days,
            groupArray(a.active_users) AS active_users
        FROM cohort_sizes AS c
        LEFT JOIN active_per_day AS a ON c.cohort_day = a.cohort_day
        GROUP BY c.cohort_day, c.cohort_size
        ORDER BY c.cohort_day ASC
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

    for cohort_day, cohort_size, days, counts in result.result_rows:
        retention = {
            int(d): (
                round((cnt / cohort_size) * 100, 2)
                if cohort_size > 0 and cnt is not None
                else 0.0
            )
            for d, cnt in zip(days, counts)
        }

        retention_list.append(
            CohortRetention(
                cohort_date=str(cohort_day),
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