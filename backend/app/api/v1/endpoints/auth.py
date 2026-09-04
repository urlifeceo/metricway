from datetime import datetime

import clickhouse_connect
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.core.auth import create_access_token, verify_password, hash_password, get_current_user
from app.core.clickhouse import get_ch_client
from app.core.config import settings
from app.schemas.auth import RegisterRequest

router = APIRouter(prefix="/auth", tags=["auth"])

ADMIN_SEED = {
    "username": "admin",
    "hashed_password": "$2b$12$7eowmiXHaZMuAhNTO8yLyOrvcG8Wy1urnlmXcwkUSuGwGUtTei8oq",
}


def seed_admin() -> None:
    client = clickhouse_connect.get_client(
        host=settings.CH_HOST,
        port=settings.CH_PORT,
        username=settings.CH_USER,
        password=settings.CH_PASSWORD,
        database=settings.CH_DATABASE,
        connect_timeout=5,
        send_receive_timeout=5,
    )
    result = client.query(
        "SELECT count() FROM tgmetrics.users WHERE username = {username:String}",
        parameters={"username": ADMIN_SEED["username"]},
    )
    if result.result_rows[0][0] == 0:
        client.insert(
            "tgmetrics.users",
            [[ADMIN_SEED["username"], ADMIN_SEED["hashed_password"], datetime.now()]],
            column_names=["username", "hashed_password", "updated_at"],
        )


def _get_hashed_password(client, username: str) -> str | None:
    result = client.query(
        """
        SELECT argMax(hashed_password, updated_at) AS hashed_password
        FROM tgmetrics.users
        WHERE username = {username:String}
        GROUP BY username
        """,
        parameters={"username": username},
    )
    if not result.result_rows:
        return None
    return result.result_rows[0][0]


@router.post("/register", status_code=201)
def register(request: RegisterRequest):
    client = get_ch_client()
    if _get_hashed_password(client, request.username) is not None:
        raise HTTPException(status_code=409, detail="Username already taken")

    client.insert(
        "tgmetrics.users",
        [[request.username, hash_password(request.password), datetime.now()]],
        column_names=["username", "hashed_password", "updated_at"],
    )
    return {"status": "created"}


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    client = get_ch_client()
    hashed = _get_hashed_password(client, form.username)
    if hashed is None or not verify_password(form.password, hashed):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": form.username})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def me(user=Depends(get_current_user)):
    return {"username": user["username"]}
