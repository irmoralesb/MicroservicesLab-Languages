from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base
import uuid
import datetime


class UsageDataModel(Base):
    __tablename__ = "usage_data"
    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid.uuid4()))
    model_company: Mapped[str] = mapped_column(String(20))
    model_name: Mapped[str] = mapped_column(String(40))
    input_calculated_token_count: Mapped[int | None] = mapped_column(nullable=True) # TODO: Remove Nullable
    input_token_count: Mapped[int] = mapped_column()
    output_token_count: Mapped[int] = mapped_column()
    total_token_count: Mapped[int] = mapped_column()
    usage_date: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True) # TODO: Remove Nullable 


class TranslationRequestModel(Base):
    __tablename__ = "translation_requests"
    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid.uuid4()), nullable= True)
    text_to_translate: Mapped[str] = mapped_column(String(4000))
    original_text_language: Mapped[str] = mapped_column(String(10))
    translated_text: Mapped[str] = mapped_column(String(4000))
    target_text_language: Mapped[str] = mapped_column(String(10))
    is_success_request: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_message: Mapped[str] = mapped_column(String(4000), nullable=True)
