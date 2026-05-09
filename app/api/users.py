from fastapi import APIRouter, Depends, HTTPException # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Session # pyright: ignore[reportMissingImports]
from app.models import get_db
from app.models.models import User
from pydantic import BaseModel # pyright: ignore[reportMissingImports]
import bcrypt

router = APIRouter(prefix="/api/users", tags=["Users"])

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str


@router.post("/register")
def register(payload: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already taken!")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered!")

    user = User(
        username=payload.username,
        email=payload.email,
        password=hash_password(payload.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {
        "message": "Account created successfully!",
        "username": user.username,
        "id": user.id
    }


@router.post("/login")
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Wrong username or password!")
    return {
        "message": "Login successful!",
        "username": user.username,
        "id": user.id,
        "is_admin": user.is_admin
    }


@router.get("/profile/{username}")
def profile(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found!")
    from app.models.models import Score
    scores = db.query(Score).filter(Score.user_id == user.id).all()
    total_quizzes = len(scores)
    best = max([s.score for s in scores], default=0)
    avg = round(sum([s.score/s.total*100 for s in scores if s.total>0])/total_quizzes) if total_quizzes else 0
    recent_scores = db.query(Score).filter(Score.user_id == user.id).order_by(Score.completed_at.desc()).limit(5).all()
    history = []
    for s in recent_scores:
        history.append({
            "quiz_title": s.quiz.title if s.quiz else "Unknown Quiz",
            "score": s.score,
            "total": s.total,
            "percentage": round((s.score / s.total) * 100) if s.total > 0 else 0,
            "date": str(s.completed_at.date())
        })

    return {
        "username": user.username,
        "email": user.email,
        "total_quizzes": total_quizzes,
        "best_score": best,
        "average_percentage": avg,
        "recent_history": history
    }


@router.get("/all")
def all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": u.id, "username": u.username, "email": u.email} for u in users]