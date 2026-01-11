from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base
import uuid
import datetime


class UsageDataModel(Base):
    __tablename__ = "usage_data"
    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(
        String(36), default=lambda: str(uuid.uuid4()))
    model_company: Mapped[str] = mapped_column(String(20))
    model_name: Mapped[str] = mapped_column(String(40))
    input_calculated_token_count: Mapped[int | None] = mapped_column(
        nullable=True)  # TODO: Remove Nullable
    input_token_count: Mapped[int] = mapped_column()
    output_token_count: Mapped[int] = mapped_column()
    total_token_count: Mapped[int] = mapped_column()
    usage_date: Mapped[datetime.datetime | None] = mapped_column(
        DateTime, nullable=True)  # TODO: Remove Nullable


class TranslationRequestModel(Base):
    __tablename__ = "translation_requests"
    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(
        String(36), default=lambda: str(uuid.uuid4()), nullable=True)
    text_to_translate: Mapped[str] = mapped_column(String(4000))
    original_text_language: Mapped[str] = mapped_column(String(10))
    translated_text: Mapped[str] = mapped_column(String(4000))
    target_text_language: Mapped[str] = mapped_column(String(10))
    is_success_request: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_message: Mapped[str] = mapped_column(String(4000), nullable=True)

    @classmethod
    def from_success(cls, transaction_id: str, text_to_translate: str, original_text_language: str, translated_text: str, translated_to_language: str):
        translation_request = cls()
        translation_request.is_success_request = True
        translation_request.transaction_id = transaction_id
        translation_request.text_to_translate = text_to_translate
        translation_request.original_text_language = original_text_language
        translation_request.translated_text = translated_text
        translation_request.target_text_language = translated_to_language
        translation_request.error_message = ""
        return translation_request

    @classmethod
    def from_error(cls, transaction_id: str, text_to_translate: str, translated_to_language: str, error_message: str):
        translation_error = cls()
        translation_error.is_success_request = False
        translation_error.transaction_id = transaction_id
        translation_error.text_to_translate = text_to_translate
        translation_error.target_text_language = translated_to_language
        translation_error.error_message = error_message
        return translation_error
