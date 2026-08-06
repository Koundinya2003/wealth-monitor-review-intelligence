from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class UserProfile(Base):
    __tablename__ = "user_profile"

    id = Column(Integer, primary_key=True, index=True)
    salary = Column(Float, nullable=False)
    expenses = Column(Float, nullable=False)
    age = Column(Integer, nullable=False)
    goal = Column(String(100), nullable=False)
    risk = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class FinancialPlan(Base):
    __tablename__ = "financial_plan"

    id = Column(Integer, primary_key=True, index=True)
    money_available = Column(Float, nullable=False)
    savings_percent = Column(Float, nullable=False)
    emergency_fund_target = Column(Float, nullable=False)
    suggested_investment = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Database:
    def __init__(self, db_path: str = "wealth_coach.db"):
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_session(self):
        return self.SessionLocal()

    def save_profile(self, salary: float, expenses: float, age: int, goal: str, risk: str):
        session = self.get_session()
        try:
            profile = UserProfile(salary=salary, expenses=expenses, age=age, goal=goal, risk=risk)
            session.add(profile)
            session.commit()
            return profile.id
        finally:
            session.close()

    def save_plan(self, money_available: float, savings_percent: float,
                  emergency_fund_target: float, suggested_investment: float):
        session = self.get_session()
        try:
            plan = FinancialPlan(
                money_available=money_available,
                savings_percent=savings_percent,
                emergency_fund_target=emergency_fund_target,
                suggested_investment=suggested_investment
            )
            session.add(plan)
            session.commit()
        finally:
            session.close()

    def get_latest_profile(self):
        session = self.get_session()
        try:
            return session.query(UserProfile).order_by(UserProfile.created_at.desc()).first()
        finally:
            session.close()

    def get_latest_plan(self):
        session = self.get_session()
        try:
            return session.query(FinancialPlan).order_by(FinancialPlan.created_at.desc()).first()
        finally:
            session.close()

    def delete_latest_profile(self):
        """Delete the latest profile to allow user to start over"""
        session = self.get_session()
        try:
            profile = session.query(UserProfile).order_by(UserProfile.created_at.desc()).first()
            if profile:
                session.delete(profile)
                session.commit()
        finally:
            session.close()


db = Database()
