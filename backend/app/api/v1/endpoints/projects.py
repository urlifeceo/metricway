from fastapi import APIRouter
from app.core.clickhouse import get_ch_client

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/link-chat")
def link_project_chat(project_token: str, chat_id: int, name: str = "My Project"):
    ch_client = get_ch_client()
    query = """
    INSERT INTO tgmetrics.projects (project_token, name, alert_chat_id, is_active, updated_at)
    VALUES ({project_token:String}, {name:String}, {chat_id:Int64}, 1, now())
    """
    ch_client.query(
        query,
        parameters={
            "project_token": project_token,
            "name": name,
            "chat_id": chat_id
        }
    )
    return {"status": "ok"}