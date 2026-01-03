# """
# Centralized Prometheus metrics definitions.
# Define all metrics here to avoid duplication across modules.
# """
from prometheus_client import Counter, Histogram, Gauge, Info
import logging


logger = logging.getLogger(__name__)

# <<   Application info metric   >>
app_info = Info('lab_languages_service', 'Application information')
app_info.info({
    'version': '0.1.0',
    'service': 'translation-api'
})

# <<   HTTP metrics (complementary to automatic instrumentation)   >>
http_request_total = Counter(
    'http_request_total',
    'Total HTTP requests by method, endpoint, and status',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# <<   Translation-specific metrics   >>
translation_requests_total = Counter(
    'translation_requests_total',
    'Total number of translation requests',
    ['source_language', 'target_language', 'status']
)

translation_duration_seconds = Histogram(
    'translation_duration_seconds',
    'Time spent processing translation requests',
    ['target_language', 'status'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

translation_text_length = Histogram(
    'translation_text_length_characters',
    'Length of text being translated',
    ['target_language'],
    buckets=[10, 50, 100, 500, 1000, 5000, 10000]
)

# <<   LLM-specific metrics   >>
llm_tokens_used = Counter(
    'llm_tokens_used_total',
    'Total number of LLM tokens consumed',
    ['model_name', 'token_type']  # token_type: input, output
)

llm_api_calls_total = Counter(
    'llm_api_calls_total',
    'Total number of LLM API calls',
    ['model_name', 'status']  # status: success, error
)

llm_api_duration_seconds = Histogram(
    'llm_api_duration_seconds',
    'Duration of LLM API calls',
    ['model_name'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0]
)

# <<   Database metrics   >>
database_connections_active = Gauge(
    'database_connections_active',
    'Number of active database connections'
)

database_operations_total = Counter(
    'database_operations_total',
    'Total number of database operations',
    # operation_type: insert, update, select, delete
    ['operation_type', 'table', 'status']
)

database_operation_duration_seconds = Histogram(
    'database_operation_duration_seconds',
    'Duration of database operations',
    ['operation_type', 'table'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

# <<   Error tracking   >>
application_errors_total = Counter(
    'application_errors_total',
    'Total number of application errors',
    ['error_type', 'endpoint']
)


def record_translation_metrics(
    target_language: str,
    duration: float,
    status: str,
    text_length: int,
    source_language: str = 'auto'
):
    """
    Record all translation-related metrics in one call.
    This ensures consistent metric recording and reduces code duplication.

    Args:
        target_language: The target language code
        duration: Time taken for translation in seconds
        status: Translation status ('success' or 'error')
        text_length: Length of input text in characters
        source_language: Source language code (default: 'auto')
    """
    try:
        translation_requests_total.labels(
            source_language=source_language,
            target_language=target_language,
            status=status
        ).inc()

        translation_duration_seconds.labels(
            target_language=target_language,
            status=status
        ).observe(duration)

        translation_text_length.labels(
            target_language=target_language
        ).observe(text_length)
    except Exception as e:
        logger.error(f"Error recording translation metrics: {e}")


def record_llm_metrics(
    model_name: str,
    input_tokens: int,
    output_tokens: int,
    duration: float,
    status: str
):
    """
    Record all LLM-related metrics in one call.

    Args:
        model_name: Name of the LLM model used
        input_tokens: Number of input tokens consumed
        output_tokens: Number of output tokens generated
        duration: API call duration in seconds
        status: Call status ('success' or 'error')
    """
    try:
        llm_tokens_used.labels(
            model_name=model_name,
            token_type='input'
        ).inc(input_tokens)

        llm_tokens_used.labels(
            model_name=model_name,
            token_type='output'
        ).inc(output_tokens)

        llm_api_calls_total.labels(
            model_name=model_name,
            status=status
        ).inc()

        llm_api_duration_seconds.labels(
            model_name=model_name
        ).observe(duration)
    except Exception as e:
        logger.error(f"Error recording LLM metrics: {e}")


def record_database_metrics(
    operation_type: str,
    table: str,
    duration: float,
    status: str = 'success'
):
    """
    Record database operation metrics.

    Args:
        operation_type: Type of operation ('insert', 'update', 'select', 'delete')
        table: Table name
        duration: Operation duration in seconds
        status: Operation status ('success' or 'error')
    """
    try:
        database_operations_total.labels(
            operation_type=operation_type,
            table=table,
            status=status
        ).inc()

        database_operation_duration_seconds.labels(
            operation_type=operation_type,
            table=table
        ).observe(duration)
    except Exception as e:
        logger.error(f"Error recording database metrics: {e}")


def database_connections_activating():
    try:
        database_connections_active.inc(1)
    except Exception as e:
        logger.error(f"Error recording database metrics: {e}")


def database_connections_deactivating():
    try:
        database_connections_active.dec(1)
    except Exception as e:
        logger.error(f"Error recording database metrics: {e}")
