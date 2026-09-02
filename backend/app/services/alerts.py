import logging
from aiogram import Bot
from app.core.config import settings
from app.core.clickhouse import get_ch_client

logger = logging.getLogger(__name__)

def get_active_projects() -> list[dict]:
    ch_client = get_ch_client()
    query = """
    SELECT 
        project_token,
        name,
        alert_chat_id
    FROM tgmetrics.projects FINAL
    WHERE is_active = 1 AND alert_chat_id != 0
    """
    rows = ch_client.query(query).result_rows
    return [
        {"token": row[0], "name": row[1], "chat_id": row[2]} 
        for row in rows
    ]

def get_daily_metrics(project_token: str) -> dict:
    ch_client = get_ch_client()
    
    # 1. Быстрый забор DAU и Выручки из daily_stats (агрегаты через Merge)
    stats_query = """
    SELECT
        bitmapCardinality(groupBitmapMerge(active_users)) AS dau,
        sum(revenue) AS revenue
    FROM tgmetrics.daily_stats
    WHERE project_token = {project_token:String}
      AND date = yesterday()
    """
    stats_result = ch_client.query(
        stats_query, 
        parameters={"project_token": project_token}
    ).first_row

    dau = stats_result[0] if stats_result else 0
    revenue = stats_result[1] if stats_result else 0.0

    # 2. Топ UTM за вчера
    utm_query = """
    SELECT 
        utm_source,
        countIf(event_name = 'payment_success') AS pays
    FROM tgmetrics.events
    WHERE project_token = {project_token:String}
      AND toDate(ts) = yesterday()
      AND utm_source != ''
    GROUP BY utm_source
    ORDER BY pays DESC
    LIMIT 1
    """
    utm_result = ch_client.query(
        utm_query, 
        parameters={"project_token": project_token}
    ).first_row
    
    top_utm = utm_result[0] if utm_result else "N/A"

    return {
        "dau": dau,
        "revenue": revenue,
        "top_utm": top_utm
    }

async def send_daily_reports():
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN missing. Skipping daily alerts.")
        return

    projects = get_active_projects()
    if not projects:
        return

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    
    try:
        for project in projects:
            try:
                metrics = get_daily_metrics(project["token"])
                
                message = (
                    f"<b>📊 Ежедневный отчёт: {project['name']}</b>\n\n"
                    f"👥 <b>DAU (вчера):</b> {metrics['dau']}\n"
                    f"💰 <b>Выручка:</b> ${metrics['revenue']:,.2f}\n"
                    f"🎯 <b>Топ UTM-источник:</b> {metrics['top_utm']}"
                )

                await bot.send_message(
                    chat_id=project["chat_id"], 
                    text=message, 
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Failed to send alert for project {project['token']}: {e}")
    finally:
        await bot.session.close()