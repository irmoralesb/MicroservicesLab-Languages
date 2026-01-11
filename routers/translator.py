"""
Router in charge of translation between two languages
"""
import logging
import time
import uuid
from typing import Annotated
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from databases.database import get_monitored_db_session
from databases.models import UsageDataModel, TranslationRequestModel
from llm_tools import llm_factory
from llm_tools.api_responses import APIResponse
from llm_tools.llm_interface import LLMInterface
from llm_tools.anthropic_tools.responses import AnthropicTranslatorResponse
from llm_tools.openai_tools.responses import OpenAITranslatorResponse
from monitoring.metrics import (
    application_errors_total,
    record_database_metrics,
    record_llm_metrics,
    record_translation_metrics,
)

from . import translator_schemas as schema

router = APIRouter(
    prefix="/api/v1/translator",
    tags=["translator"]
)


def get_db():
    with get_monitored_db_session() as db:
        yield db


def get_llm_factory() -> llm_factory.LLMFactory:
    """Dependency that provides an LLM factory instance."""
    return llm_factory.LLMFactory()


@router.post("/translate", status_code=status.HTTP_200_OK)
async def translate_endpoint(request_body: schema.TranslateEndpointRequest,
                             llm_factory: Annotated[llm_factory.LLMFactory, Depends(get_llm_factory)],
                             db: Annotated[Session, Depends(get_db)]):
    # Start timing for performance monitoring
    start_time = time.time()
    llm_start_time = None

    transaction_id = uuid.uuid4()

    # Create LLM interface dynamically from request parameters
    llm_tool: LLMInterface = llm_factory.create_llm(
        request_body.llm_provider,
        request_body.llm_model
    )

    try:
        # Time the LLM API call separately
        llm_start_time = time.time()
        translation_response: APIResponse = llm_tool.translate_text(
            request_body.text_to_translate, request_body.translate_to_language)
        llm_duration = time.time() - llm_start_time

        logger = logging.getLogger(__name__)
        logger.info(f"LLM - Time in seconds: {llm_duration}")
    except Exception as e:
        # Record LLM API failure
        if llm_start_time:
            llm_duration = time.time() - llm_start_time
            record_llm_metrics(
                model_name='gpt-4o-mini',
                input_tokens=0,
                output_tokens=0,
                duration=llm_duration,
                status='error'
            )
        application_errors_total.labels(
            error_type='llm_api_error',
            endpoint='/api/v1/translator/translate'
        ).inc()
        raise HTTPException(
            status_code=500, detail="Translation service unavailable")

    # Inserting data into db
    usage_data = UsageDataModel()
    usage_data.transaction_id = str(transaction_id)
    usage_data.model_name = request_body.llm_model
    usage_data.model_company = request_body.llm_provider
    usage_data.input_calculated_token_count = 0
    usage_data.input_token_count = translation_response.usage.input_tokens
    usage_data.output_token_count = translation_response.usage.output_tokens
    usage_data.total_token_count = translation_response.usage.input_tokens + \
        translation_response.usage.output_tokens
    usage_data.usage_date = datetime.now(timezone.utc)

    translation_request_data: TranslationRequestModel

    if translation_response.is_success:
        translation_request_data = TranslationRequestModel.from_success(
            transaction_id=str(transaction_id),
            text_to_translate=request_body.text_to_translate,
            original_text_language=translation_response.data.text_language,
            translated_text=translation_response.data.translated_text,
            translated_to_language=request_body.translate_to_language
        )
    else:
        translation_request_data = TranslationRequestModel.from_error(
            transaction_id=str(transaction_id),
            text_to_translate=request_body.text_to_translate,
            translated_to_language=request_body.translate_to_language,
            error_message=translation_response.error.message
        )

    db_start = time.time()
    try:
        db_start = time.time()
        db.add(usage_data)
        db.add(translation_request_data)
        db_duration = time.time() - db_start

        # Record database operation metrics
        record_database_metrics(
            operation_type='insert',
            table='usage_data',
            duration=db_duration,
            status='success'
        )

    except Exception as e:
        db_duration = time.time() - db_start if 'db_start' in locals() else 0
        record_database_metrics(
            operation_type='insert',
            table='usage_data',
            duration=db_duration,
            status='error'
        )
        application_errors_total.labels(
            error_type='database_error',
            endpoint='/api/v1/translator/translate'
        ).inc()
        raise HTTPException(
            status_code=500, detail="Failed to save usage data")

    # Calculate total duration
    total_duration = time.time() - start_time
    text_length = len(request_body.text_to_translate)

    # Record LLM metrics using centralized function (single point)
    record_llm_metrics(
        model_name='gpt-4o-mini',
        input_tokens=translation_response.usage.input_tokens,
        output_tokens=translation_response.usage.output_tokens,
        duration=llm_duration,
        status='success' if translation_response.is_success else 'error'
    )

    if translation_response.is_success:
        # Record successful translation metrics using centralized function
        record_translation_metrics(
            target_language=request_body.translate_to_language,
            duration=total_duration,
            status='success',
            text_length=text_length,
            source_language='auto'
        )

        return {"message": f"{translation_response.data.translated_text}"}

    # Record failed translation metrics
    record_translation_metrics(
        target_language=request_body.translate_to_language,
        duration=total_duration,
        status='error',
        text_length=text_length,
        source_language='auto'
    )

    application_errors_total.labels(
        error_type='translation_failed',
        endpoint='/api/v1/translator/translate'
    ).inc()

    # Return an error response
    error_message = translation_response.error.message
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message)
