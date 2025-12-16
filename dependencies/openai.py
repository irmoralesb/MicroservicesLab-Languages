from openai import OpenAI
import os
from dotenv import load_dotenv
import tiktoken


load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_openai_client():
    return client


# response.usage
#{
#   "prompt_tokens": 87,
#   "completion_tokens": 132,
#   "total_tokens": 219
# }


def calculate_tokens_count(text: str, model: str) -> int:
    encoder = tiktoken.encoding_for_model(model)
    tokens = encoder.encode(text)
    return len(tokens)