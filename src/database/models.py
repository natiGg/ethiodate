import datetime
from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, String, Float, Enum as SQLAlchemyEnum
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class UserStatus(enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    BANNED = "banned"

class ReportStatus(enum.Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    DISMISSED = "dismissed"

class User(Base):
    __tablename__ = "users"

    telegram_id = Column(BigInteger, primary_key=True, index=True)
    telegram_username = Column(String, nullable=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)
    gender_preference = Column(String, nullable=False)
    current_country = Column(String, nullable=False)
    current_city = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    origin_region = Column(String, nullable=False)
    willing_to_relocate = Column(Boolean, default=False)
    bio = Column(String)
    date_of_birth = Column(String) # Storing as YYYY-MM-DD
    star_sign = Column(String)
    language_pref = Column(String, default="en")
    status = Column(SQLAlchemyEnum(UserStatus), default=UserStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    photos = relationship("Photo", back_populates="user", cascade="all, delete-orphan")

class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    telegram_file_id = Column(String, nullable=False)
    sort_order = Column(Integer, default=0)
    is_primary = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="photos")

class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    to_user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    is_like = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    user_a_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    user_b_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    reported_user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    reason = Column(String, nullable=False)
    status = Column(SQLAlchemyEnum(ReportStatus), default=ReportStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
