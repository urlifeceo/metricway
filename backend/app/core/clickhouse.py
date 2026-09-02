import clickhouse_connect
from app.core.config import settings


def get_ch_client():
    return clickhouse_connect.get_client(
        host=settings.CH_HOST,
        port=settings.CH_PORT,
        username=settings.CH_USER,
        password=settings.CH_PASSWORD,
        database=settings.CH_DATABASE,
    )