import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db, engine
from models import Base, User, Generation
from auth import hash_password, verify_password, create_token, decode_token
from runware import generate_images, CREDITS_PER_IMAGE

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    if os.getenv("SEED_ADMIN", "true") == "true":
        db = next(get_db())
        username = os.getenv("ADMIN_USERNAME", "admin")
        if not db.query(User).filter(User.username == username).first():
            db.add(User(
                username=username,
                password_hash=hash_password(os.getenv("ADMIN_PASSWORD", "change-me")),
                is_admin=True,
                credits=0,
            ))
            db.commit()
        db.close()
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_current_user(authorization: str = Header(...), db: Session = Depends(get_db)) -> User:
    try:
        token = authorization.replace("Bearer ", "")
        payload = decode_token(token)
        user = db.query(User).filter(User.id == int(payload["sub"])).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    return user

# --- Auth ---

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {
        "token": create_token(user.id, user.is_admin),
        "username": user.username,
        "is_admin": user.is_admin,
        "credits": user.credits,
    }

# --- Generate ---

class GenerateRequest(BaseModel):
    prompt: str
    negative_prompt: str = ""
    width: int = 1024
    height: int = 1024
    count: int = 1
    cfg_scale: float = 7.0
    steps: int = 28

@app.post("/api/generate")
async def generate(req: GenerateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.is_admin:
        cost = req.count * CREDITS_PER_IMAGE
        if user.credits < cost:
            raise HTTPException(status_code=402, detail="Insufficient credits")

    image_urls = await generate_images(
        prompt=req.prompt,
        negative_prompt=req.negative_prompt,
        width=req.width,
        height=req.height,
        count=req.count,
        cfg_scale=req.cfg_scale,
        steps=req.steps,
    )

    if not user.is_admin:
        user.credits -= req.count * CREDITS_PER_IMAGE

    gen = Generation(
        user_id=user.id,
        prompt=req.prompt,
        negative_prompt=req.negative_prompt,
        settings={"width": req.width, "height": req.height, "cfg_scale": req.cfg_scale, "steps": req.steps},
        image_urls=image_urls,
    )
    db.add(gen)
    db.commit()
    db.refresh(gen)

    return {"id": gen.id, "image_urls": image_urls, "credits": user.credits}

@app.get("/api/history")
def history_placeholder(user: User = Depends(get_current_user)):
    return []

@app.get("/api/gallery")
def gallery_placeholder(user: User = Depends(get_current_user)):
    return {"images": []}

@app.post("/api/admin/users")
def admin_users_placeholder(admin: User = Depends(require_admin)):
    raise HTTPException(status_code=501, detail="Not implemented")

@app.put("/api/admin/users/{user_id}/credits")
def admin_credits_placeholder(user_id: int, admin: User = Depends(require_admin)):
    raise HTTPException(status_code=501, detail="Not implemented")

@app.get("/api/admin/users")
def admin_list_placeholder(admin: User = Depends(require_admin)):
    return []
