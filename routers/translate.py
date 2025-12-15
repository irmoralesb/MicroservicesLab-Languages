"""
Router in charge of translation between two languages
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from openai import OpenAI
from dependencies.openai import get_openai_client


router = APIRouter(
    prefix="/api/v1/translate",
    tags=["translate"]
)


class TranslateRequest(BaseModel):
    text_to_translate: str


@router.post("/")
async def translate_endpoint(requestBody: TranslateRequest, client: OpenAI = Depends(get_openai_client)):
    role_description = """
    You are a translation machine, you are tasked with translate any text you are given to Spanish language.
    You only have to return the translated text
    """
    request = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": f"{role_description}"},
                  {"role": "user", "content": requestBody.text_to_translate}]
    )

    return {"message": f"{request.choices[0].message.content}"}
