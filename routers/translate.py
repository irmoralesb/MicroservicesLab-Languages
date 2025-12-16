"""
Router in charge of translation between two languages
"""
from fastapi import APIRouter, Depends
from openai import OpenAI
from dependencies.openai import get_openai_client
from . import translate_schemas as schema


router = APIRouter(
    prefix="/api/v1/translate",
    tags=["translate"]
)


@router.post("/")
async def translate_endpoint(requestBody: schema.TranslateRequest, client: OpenAI = Depends(get_openai_client)):
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
