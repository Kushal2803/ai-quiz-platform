from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import relationship # pyright: ignore[reportMissingImports]
from datetime import datetime
from app.models import Base


class User(Base):
    __tablename__ = "users"

    id          = Column(Integer, primary_key=True, index=True)
    username    = Column(String(50), unique=True, nullable=False)
    email       = Column(String(100), unique=True, nullable=False)
    password    = Column(String(200), nullable=False)
    is_admin    = Column(Boolean, default=False)
    created_at  = Column(DateTime, default=datetime.utcnow)

    scores      = relationship("Score", back_populates="user")


class Question(Base):
    __tablename__ = "questions"

    id              = Column(Integer, primary_key=True, index=True)
    question_text   = Column(Text, nullable=False)
    option_a        = Column(String(200), nullable=False)
    option_b        = Column(String(200), nullable=False)
    option_c        = Column(String(200), nullable=False)
    option_d        = Column(String(200), nullable=False)
    correct_answer  = Column(String(1), nullable=False)
    difficulty      = Column(String(10), default="medium")
    topic           = Column(String(100))
    news_source     = Column(String(200))
    explanation     = Column(Text)
    created_at      = Column(DateTime, default=datetime.utcnow)

    quiz_id         = Column(Integer, ForeignKey("quizzes.id"))
    quiz            = relationship("Quiz", back_populates="questions")


class Quiz(Base):
    __tablename__ = "quizzes"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(200), nullable=False)
    date        = Column(DateTime, default=datetime.utcnow)
    is_active   = Column(Boolean, default=True)

    questions   = relationship("Question", back_populates="quiz")
    scores      = relationship("Score", back_populates="quiz")


class Score(Base):
    __tablename__ = "scores"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"))
    quiz_id      = Column(Integer, ForeignKey("quizzes.id"))
    score        = Column(Integer, default=0)
    total        = Column(Integer, default=0)
    completed_at = Column(DateTime, default=datetime.utcnow)

    user         = relationship("User", back_populates="scores")
    quiz         = relationship("Quiz", back_populates="scores")