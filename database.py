from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import config
import os

# Database setup
config_obj = config.Config()

# Handle Render PostgreSQL
if 'RENDER' in os.environ:
    engine = create_engine(config_obj.DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
else:
    engine = create_engine(config_obj.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255))
    balance = Column(Float, default=0.0)
    total_earned = Column(Float, default=0.0)
    mining_power = Column(Float, default=1.0)
    referrals = Column(Integer, default=0)
    referral_bonus = Column(Float, default=0.0)
    is_mining = Column(Boolean, default=False)
    last_mining = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class Referral(Base):
    __tablename__ = "referrals"
    
    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer)
    referred_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    amount = Column(Float)
    currency = Column(String(50))
    status = Column(String(50), default='pending')
    binance_uid = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Database error: {e}")

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
