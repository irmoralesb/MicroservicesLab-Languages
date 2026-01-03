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
from databases.database import get_monitored_db_session
from monitoring.metrics import record_database_metrics
from llm_tools import llm_factory
from llm_tools.llm_interface import LLMInterface
from llm_tools.openai_tools.responses import TranslatorResponse
import logging
import uuid
import time

# Import centralized metrics functions
from monitoring.metrics import (
    record_translation_metrics,
    record_llm_metrics,
    application_errors_total
)

router = APIRouter(
    prefix="/api/v1/translator",
    tags=["translator"]
)


def get_db():
    with get_monitored_db_session() as db:
        yield db


def get_llm_interface():
    return llm_factory.LLMFactory().create_llm('openai', "gpt-4o-mini")


@router.post("/translate", status_code=status.HTTP_201_CREATED)
async def translate_endpoint(requestBody: schema.TranslateEndpointRequest, llm_tool: LLMInterface = Depends(get_llm_interface), db: Session = Depends(get_db)):
    # Start timing for performance monitoring
    start_time = time.time()
    llm_start_time = None

    transaction_id = uuid.uuid4()

    try:
        # Time the LLM API call separately
        llm_start_time = time.time()
        translation_response: TranslatorResponse = llm_tool.translate_text(
            requestBody.text_to_translate, requestBody.translate_to_language)
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
    usage_data.transaction_id = transaction_id
    usage_data.model_name = ""
    usage_data.model_company = ""
    usage_data.input_calculated_token_count = 0
    usage_data.input_token_count = translation_response.usage.input_tokens
    usage_data.output_token_count = translation_response.usage.output_tokens
    usage_data.total_token_count = translation_response.usage.input_tokens + \
        translation_response.usage.output_tokens
    usage_data.usage_date = None

    try:
        db_start = time.time()
        db.add(usage_data)
        db_duration = time.time() - db_start

        # Record database operation metrics
        record_database_metrics(
            operation_type='insert',
            table='usage_data',
            duration=db_duration,
            status='success'
        )

        # Record LLM metrics using centralized function
        record_llm_metrics(
            model_name='gpt-4o-mini',
            input_tokens=translation_response.usage.input_tokens,
            output_tokens=translation_response.usage.output_tokens,
            duration=llm_duration,
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
        # Record LLM metrics using centralized function
        record_llm_metrics(
            model_name='gpt-4o-mini',
            input_tokens=translation_response.usage.input_tokens,
            output_tokens=translation_response.usage.output_tokens,
            duration=llm_duration,
            status='error'
        )
        application_errors_total.labels(
            error_type='database_error',
            endpoint='/api/v1/translator/translate'
        ).inc()
        raise HTTPException(
            status_code=500, detail="Failed to save usage data")

    # Record LLM metrics using centralized function
    record_llm_metrics(
        model_name='gpt-4o-mini',
        input_tokens=translation_response.usage.input_tokens,
        output_tokens=translation_response.usage.output_tokens,
        duration=llm_duration,
        status='success' if translation_response.is_success else 'error'
    )

    # Calculate total duration
    total_duration = time.time() - start_time
    text_length = len(requestBody.text_to_translate)

    if translation_response.is_success:
        # Record successful translation metrics using centralized function
        record_translation_metrics(
            target_language=requestBody.translate_to_language,
            duration=total_duration,
            status='success',
            text_length=text_length,
            source_language='auto'
        )

        return {"message": f"{translation_response.data.translated_text}"}

    # Record failed translation metrics
    record_translation_metrics(
        target_language=requestBody.translate_to_language,
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
