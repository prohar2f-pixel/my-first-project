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
def get_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    gens = (
        db.query(Generation)
        .filter(Generation.user_id == user.id)
        .order_by(Generation.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": g.id,
            "prompt": g.prompt,
            "image_urls": g.image_urls,
            "settings": g.settings,
            "created_at": g.created_at.isoformat(),
        }
        for g in gens
    ]

@app.get("/api/gallery")
def get_gallery(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    gens = (
        db.query(Generation)
        .filter(Generation.user_id == user.id)
        .order_by(Generation.created_at.desc())
        .all()
    )
    return {"images": [url for g in gens for url in g.image_urls]}

class CreateUserRequest(BaseModel):
    username: str
    password: str
    credits: int = 0

@app.post("/api/admin/users")
def create_user(req: CreateUserRequest, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        credits=req.credits,
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username, "credits": user.credits}

class UpdateCreditsRequest(BaseModel):
    credits: int

@app.put("/api/admin/users/{user_id}/credits")
def update_credits(user_id: int, req: UpdateCreditsRequest, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.credits = req.credits
    db.commit()
    return {"id": user.id, "username": user.username, "credits": user.credits}

@app.get("/api/admin/users")
def list_users(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).filter(User.is_admin == False).all()
    return [
        {"id": u.id, "username": u.username, "credits": u.credits, "created_at": u.created_at.isoformat()}
        for u in users
    ]
