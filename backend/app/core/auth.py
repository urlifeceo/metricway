from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import bcrypt
from app.core.config import settings
from app.core.clickhouse import get_ch_client

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

ADMIN_USERNAME = "admin"

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

# ---- JWT utils ----
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

# ---- Dependency ----
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return {"username": username}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {"username": username}


async def require_project_access(
    request: Request,
    user: dict = Depends(get_current_user),
):
    """Проверяет, что текущий юзер владеет project_token (query или JSON-body)."""
    username = user["username"]
    if username == ADMIN_USERNAME:
        return

    project_token = request.query_params.get("project_token")
    if not project_token:
        try:
            body = await request.json()
        except Exception:
            body = None
        if isinstance(body, dict):
            project_token = body.get("project_token")

    if not project_token:
        raise HTTPException(status_code=400, detail="project_token required")

    client = get_ch_client()
    result = client.query(
        """
        SELECT count()
        FROM tgmetrics.user_projects
        WHERE username = {username:String}
          AND project_token = {project_token:String}
        """,
        parameters={"username": username, "project_token": project_token},
    )
    if result.result_rows[0][0] == 0:
        raise HTTPException(status_code=403, detail="No access to this project")


