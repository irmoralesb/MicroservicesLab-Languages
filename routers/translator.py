"""
Router in charge of translation between two languages
"""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.params import Depends
from sqlalchemy.orm import Session
from starlette.status import HTTP_202_ACCEPTED
from . import translator_schemas as schema
from databases.database import SessionLocal
from databases.models import UsageDataModel, TranslationRequestModel

# from typing import List
from llm_tools import llm_factory
from llm_tools.llm_interface import LLMInterface
from llm_tools.openai_tools.responses import TranslatorResponse
# import logging
import uuid

router = APIRouter(
    prefix="/api/v1/translator",
    tags=["translator"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_llm_interface():
    return llm_factory.LLMFactory().create_llm('openai', "gpt-4o-mini")


@router.post("/translate", status_code=status.HTTP_201_CREATED)
async def translate_endpoint(requestBody: schema.TranslateEndpointRequest, llm_tool: LLMInterface = Depends(get_llm_interface), db: Session = Depends(get_db)):
    transaction_id = uuid.uuid4()
    translation_response: TranslatorResponse = llm_tool.translate_text(
        requestBody.text_to_translate, requestBody.translate_to_language)

    # Inserting data into db

    usage_data = UsageDataModel()
    usage_data.transaction_id = transaction_id
    usage_data.model_name = ""
    usage_data.model_company = ""
    usage_data.input_calculated_token_count = 0
    usage_data.input_token_count = translation_response.usage.input_tokens
    usage_data.output_token_count = translation_response.usage.output_tokens
    usage_data.total_token_count = translation_response.usage.input_tokens + \
        translation_response.usage.output_tokens
    usage_data.usage_date = None

    db.add(usage_data)
    db.commit()
    db.refresh(usage_data)

    if translation_response.is_success:
        return {"message": f"{translation_response.data.translated_text}"}

    # Return an HttpException
    error_message = translation_response.error.message
    return {"error": f"{error_message}"}
