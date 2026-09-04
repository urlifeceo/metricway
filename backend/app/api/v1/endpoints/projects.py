import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_user, ADMIN_USERNAME
from app.core.clickhouse import get_ch_client
from app.schemas.projects import ProjectCreateRequest, ProjectOut

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
def list_projects(user: dict = Depends(get_current_user)):
    client = get_ch_client()
    username = user["username"]

    if username == ADMIN_USERNAME:
        result = client.query(
            """
            SELECT project_token, argMax(name, updated_at) AS name
            FROM tgmetrics.projects
            GROUP BY project_token
            ORDER BY project_token ASC
            """
        )
    else:
        result = client.query(
            """
            SELECT
                p.project_token AS project_token,
                argMax(p.name, p.updated_at) AS name
            FROM tgmetrics.projects AS p
            INNER JOIN (
                SELECT project_token
                FROM tgmetrics.user_projects
                WHERE username = {username:String}
                GROUP BY project_token
            ) AS up ON p.project_token = up.project_token
            GROUP BY p.project_token
            ORDER BY p.project_token ASC
            """,
            parameters={"username": username},
        )

    return [ProjectOut(project_token=row[0], name=row[1]) for row in result.result_rows]


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(request: ProjectCreateRequest, user: dict = Depends(get_current_user)):
    client = get_ch_client()
    username = user["username"]
    project_token = secrets.token_urlsafe(16)
    now = datetime.now()

    client.insert(
        "tgmetrics.projects",
        [[project_token, request.name, 0, 1, now]],
        column_names=["project_token", "name", "alert_chat_id", "is_active", "updated_at"],
    )
    client.insert(
        "tgmetrics.user_projects",
        [[username, project_token, now]],
        column_names=["username", "project_token", "updated_at"],
    )
    return ProjectOut(project_token=project_token, name=request.name)


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
