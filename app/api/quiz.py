from fastapi import APIRouter, Depends, HTTPException  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Session  # pyright: ignore[reportMissingImports]
from sqlalchemy import func  # pyright: ignore[reportMissingImports]
from datetime import datetime, date
from app.models import get_db
from app.models.models import Question, Quiz, Score, User
from app.services.quiz_generator import generate_questions_from_news, SAMPLE_NEWS
from pydantic import BaseModel  # pyright: ignore[reportMissingImports]
import asyncio

router = APIRouter(prefix="/api/quiz", tags=["Quiz"])


@router.post("/generate")
async def generate_quiz(db: Session = Depends(get_db)):
    today = date.today()
    existing = db.query(Quiz).filter(
        func.date(Quiz.date) == today
    ).first()

    if existing:
        return {"message": "Today's quiz already exists!", "quiz_id": existing.id}

    try:
        # Generate 10 questions using real news + Gemini
        questions_data = await generate_questions_from_news(num_questions=10)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

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

    return {
        "message": "Quiz generated successfully with real world news!",
        "quiz_id": quiz.id,
        "total_questions": len(questions_data),
        "date": str(today)
    }


@router.delete("/reset-today")
def reset_today_quiz(db: Session = Depends(get_db)):
    today = date.today()
    quiz = db.query(Quiz).filter(
        func.date(Quiz.date) == today
    ).first()
    if quiz:
        db.query(Question).filter(Question.quiz_id == quiz.id).delete()
        db.delete(quiz)
        db.commit()
    return {"message": "Today's quiz deleted. You can generate a new one!"}


@router.get("/today")
def get_today_quiz(db: Session = Depends(get_db)):
    today = date.today()
    quiz = db.query(Quiz).filter(
        func.date(Quiz.date) == today,
        Quiz.is_active == True
    ).first()

    if not quiz:
        raise HTTPException(
            status_code=404,
            detail="No quiz found for today. Generate one first!"
        )

    questions = []
    for q in quiz.questions:
        questions.append({
            "id": q.id,
            "question_text": q.question_text,
            "option_a": q.option_a,
            "option_b": q.option_b,
            "option_c": q.option_c,
            "option_d": q.option_d,
            "difficulty": q.difficulty,
            "topic": q.topic,
            "explanation": q.explanation,
            "correct_answer": q.correct_answer
        })

    return {
        "quiz_id": quiz.id,
        "title": quiz.title,
        "date": str(quiz.date.date()),
        "total_questions": len(questions),
        "questions": questions
    }


@router.get("/history")
def get_quiz_history(db: Session = Depends(get_db)):
    """Return all past quizzes - data is never lost."""
    quizzes = db.query(Quiz).order_by(Quiz.date.desc()).limit(30).all()
    return [{
        "quiz_id": q.id,
        "title": q.title,
        "date": str(q.date.date()),
        "total_questions": len(q.questions)
    } for q in quizzes]


@router.get("/leaderboard")
def get_leaderboard(db: Session = Depends(get_db)):
    scores = db.query(Score, User).join(
        User, Score.user_id == User.id
    ).order_by(Score.score.desc()).limit(10).all()

    leaderboard = []
    for i, (score, user) in enumerate(scores):
        leaderboard.append({
            "rank": i + 1,
            "username": user.username,
            "score": score.score,
            "total": score.total,
            "percentage": round((score.score / score.total) * 100) if score.total > 0 else 0
        })

    return {"leaderboard": leaderboard}


@router.get("/{quiz_id}")
def get_quiz_by_id(quiz_id: int, db: Session = Depends(get_db)):
    """Get any past quiz by ID."""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions = []
    for q in quiz.questions:
        questions.append({
            "id": q.id,
            "question_text": q.question_text,
            "option_a": q.option_a,
            "option_b": q.option_b,
            "option_c": q.option_c,
            "option_d": q.option_d,
            "difficulty": q.difficulty,
            "topic": q.topic,
            "explanation": q.explanation,
            "correct_answer": q.correct_answer
        })

    return {
        "quiz_id": quiz.id,
        "title": quiz.title,
        "date": str(quiz.date.date()),
        "total_questions": len(questions),
        "questions": questions
    }


class AnswerSubmit(BaseModel):
    quiz_id: int
    user_name: str
    answers: dict


@router.post("/submit")
def submit_quiz(payload: AnswerSubmit, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == payload.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    user = db.query(User).filter(User.username == payload.user_name).first()
    if not user:
        user = User(
            username=payload.user_name,
            email=f"{payload.user_name}@guest.com",
            password="guest"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    correct = 0
    results = []
    for question in quiz.questions:
        user_answer = payload.answers.get(str(question.id), "").upper()
        is_correct = user_answer == question.correct_answer.upper()
        if is_correct:
            correct += 1
        results.append({
            "question_id": question.id,
            "question": question.question_text,
            "your_answer": user_answer,
            "correct_answer": question.correct_answer,
            "is_correct": is_correct,
            "explanation": question.explanation
        })

    total = len(quiz.questions)
    percentage = round((correct / total) * 100) if total > 0 else 0

    score = Score(
        user_id=user.id,
        quiz_id=quiz.id,
        score=correct,
        total=total
    )
    db.add(score)
    db.commit()

    return {
        "user": payload.user_name,
        "score": correct,
        "total": total,
        "percentage": percentage,
        "results": results
    }



