from sqlalchemy import Column, Integer, String, Boolean, DateTime
from .database import Base
import uuid


class UsageDataModel(Base):
    __tablename__ = "usage_data"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_id = Column(String(36), default=lambda: str(
        uuid.uuid4()), nullable=True)  # I will change this later!
    model_company = Column(String(20))
    model_name = Column(String(20))
    input_calculated_token_count = Column(
        Integer, nullable=True)  # I will change this later!
    input_token_count = Column(Integer)
    output_token_count = Column(Integer)
    total_token_count = Column(Integer)
    usage_date = Column(DateTime, nullable=True)  # I will change this later!


class TranslationRequestModel(Base):
    __tablename__ = "translation_requests"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_id = Column(
        String(36), default=lambda: str(uuid.uuid4()), nullable=True)
    text_to_translate = Column(String(4000))
    original_text_language = Column(String(10))
    translated_text = Column(String(4000))
    target_text_language = Column(String(10))
    is_success_request = Column(Boolean, nullable=False)
    error_message = Column(String(4000), nullable=True)
