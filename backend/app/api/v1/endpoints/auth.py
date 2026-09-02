from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.core.auth import create_access_token, verify_password, hash_password

router = APIRouter(prefix="/auth", tags=["auth"])

FAKE_USER = {
    "username": "admin",
    "hashed_password": "$2b$12$7eowmiXHaZMuAhNTO8yLyOrvcG8Wy1urnlmXcwkUSuGwGUtTei8oq"
}
# $4HHseD45vg6v7J

@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    if form.username != FAKE_USER["username"]:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not verify_password(form.password, FAKE_USER["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": form.username})
    return {"access_token": token, "token_type": "bearer"}
