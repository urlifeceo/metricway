CREATE DATABASE IF NOT EXISTS tgmetrics;

CREATE TABLE IF NOT EXISTS tgmetrics.events (
    ts DateTime64(3),
    event_id UUID,
    project_token String,
    user_id Int64,
    chat_id Int64,
    handler String,
    update_type String,
    payload String,
    text String DEFAULT JSONExtractString(payload, 'text'),
    callback_data String DEFAULT JSONExtractString(payload, 'callback_data'),
    start_payload String DEFAULT JSONExtractString(payload, 'start_payload'),
    utm_source String DEFAULT JSONExtractString(payload, 'utm_source'),
    utm_campaign String DEFAULT JSONExtractString(payload, 'utm_campaign'),
    referrer String DEFAULT JSONExtractString(payload, 'referrer'),
    error_type String DEFAULT JSONExtractString(payload, 'error_type'),
    error_message String DEFAULT JSONExtractString(payload, 'error_message')
)
ENGINE = MergeTree()
ORDER BY (project_token, user_id, ts)
TTL ts + INTERVAL 90 DAY;

CREATE TABLE IF NOT EXISTS tgmetrics.purchases (
    ts DateTime,
    user_id Int64,
    project_token String,
    amount Float64,
    currency String,
    product_id String,
    payment_provider String DEFAULT ''
)
ENGINE = MergeTree()
ORDER BY (project_token, ts)
TTL ts + INTERVAL 180 DAY;

CREATE TABLE IF NOT EXISTS tgmetrics.errors (
    ts DateTime,
    project_token String,
    user_id Int64,
    error_type String,
    error_message String,
    stack String
)
ENGINE = MergeTree()
ORDER BY (project_token, ts)
TTL ts + INTERVAL 30 DAY;

CREATE TABLE IF NOT EXISTS tgmetrics.users_meta (
    project_token String,
    user_id Int64,
    first_seen_ts SimpleAggregateFunction(min, DateTime),
    last_seen_ts SimpleAggregateFunction(max, DateTime),
    is_paid_user SimpleAggregateFunction(max, UInt8),
    messages_count SimpleAggregateFunction(sum, UInt64)
)
ENGINE = AggregatingMergeTree()
ORDER BY (project_token, user_id);

CREATE TABLE IF NOT EXISTS tgmetrics.traffic (
    project_token String,
    user_id Int64,
    first_seen_ts DateTime,
    start_payload String,
    utm_source String,
    utm_campaign String,
    referrer String
)
ENGINE = ReplacingMergeTree(first_seen_ts)
ORDER BY (project_token, user_id);

CREATE TABLE IF NOT EXISTS tgmetrics.projects
(
    project_token String,
    name String,
    alert_chat_id Int64,
    is_active UInt8 DEFAULT 1,
    updated_at DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY project_token;

CREATE MATERIALIZED VIEW IF NOT EXISTS tgmetrics.mv_users_meta
TO tgmetrics.users_meta
AS SELECT
    project_token,
    user_id,
    min(ts) AS first_seen_ts,
    max(ts) AS last_seen_ts,
    0 AS is_paid_user,
    count() AS messages_count
FROM tgmetrics.events
GROUP BY project_token, user_id;

ALTER TABLE tgmetrics.events ADD INDEX IF NOT EXISTS idx_event_id event_id TYPE bloom_filter() GRANULARITY 1;
ALTER TABLE tgmetrics.events ADD INDEX IF NOT EXISTS idx_handler handler TYPE bloom_filter() GRANULARITY 1;
ALTER TABLE tgmetrics.events ADD INDEX IF NOT EXISTS idx_utm_source utm_source TYPE bloom_filter() GRANULARITY 1;

ALTER TABLE tgmetrics.purchases ADD INDEX IF NOT EXISTS idx_purchases_ts ts TYPE minmax GRANULARITY 1;
ALTER TABLE tgmetrics.errors ADD INDEX IF NOT EXISTS idx_errors_ts ts TYPE minmax GRANULARITY 1;