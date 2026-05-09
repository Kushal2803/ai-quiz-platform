from fastapi import FastAPI  # pyright: ignore[reportMissingImports]
from fastapi.middleware.cors import CORSMiddleware  # pyright: ignore[reportMissingImports]
from fastapi.staticfiles import StaticFiles  # pyright: ignore[reportMissingImports]
from fastapi.responses import FileResponse  # pyright: ignore[reportMissingImports]
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # pip install apscheduler
from datetime import date, datetime
import os
import asyncio

app = FastAPI(
    title="AI Quiz Platform",
    description="Daily AI-powered quiz with real world news",
    version="2.0.0"
)

# ✅ CORS - allows mobile apps and any browser to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from app.api import quiz, users
app.include_router(quiz.router)
app.include_router(users.router)

# ✅ Serve frontend (HTML) as static files
if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse("frontend/index.html")
else:
    @app.get("/")
    def root():
        return {
            "message": "🧠 AI Quiz Platform is LIVE!",
            "version": "2.0",
            "docs": "/docs",
            "today_quiz": "/api/quiz/today",
            "generate_quiz": "POST /api/quiz/generate"
        }


# ✅ AUTO-GENERATE quiz every day at 7:00 AM
scheduler = AsyncIOScheduler()

async def auto_generate_daily_quiz():
    """Automatically generates today's quiz every morning."""
    print(f"[TIME] Auto-generating daily quiz at {datetime.now()}")
    try:
        from app.models import SessionLocal
        from app.models.models import Quiz
        from app.services.quiz_generator import generate_questions_from_news
        from app.models.models import Question
        from sqlalchemy import func

        db = SessionLocal()
        today = date.today()

        existing = db.query(Quiz).filter(
            func.date(Quiz.date) == today
        ).first()

        if existing:
            print("[OK] Today's quiz already exists, skipping.")
            db.close()
            return

        questions_data = await generate_questions_from_news(num_questions=10)

        quiz = Quiz(
            title=f"Daily World Quiz - {today.strftime('%B %d, %Y')}",
            date=datetime.now(),
            is_active=True
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)

        for q in questions_data:
            question = Question(
                question_text=q["question_text"],
                option_a=q["option_a"],
                option_b=q["option_b"],
                option_c=q["option_c"],
                option_d=q["option_d"],
                correct_answer=q["correct_answer"].upper(),
                difficulty=q.get("difficulty", "medium"),
                topic=q.get("topic", "General"),
                explanation=q.get("explanation", ""),
                quiz_id=quiz.id
            )
            db.add(question)

        db.commit()
        db.close()
        print(f"[OK] Auto-generated quiz with {len(questions_data)} questions!")

    except Exception as e:
        print(f"[ERROR] Auto-generation failed: {e}")


@app.on_event("startup")
async def startup_event():
    # Create DB tables
    from app.models.models import Base
    from app.models import engine
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created/verified")

    # Start daily scheduler - generates quiz at 7:00 AM every day
    scheduler.add_job(
        auto_generate_daily_quiz,
        "cron",
        hour=7,
        minute=0,
        id="daily_quiz"
    )
    scheduler.start()
    print("[OK] Daily quiz scheduler started (runs at 7:00 AM)")


@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()


@app.get("/health")
def health():
    """Health check endpoint - keeps Railway alive."""
    return {"status": "healthy", "time": str(datetime.now())}
