"""
Router in charge of translation between two languages
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session
from openai import OpenAI
from starlette.status import HTTP_202_ACCEPTED
from dependencies.openai import calculate_tokens_count, get_openai_client
from . import translate_schemas as schema
from databases.database import SessionLocal
from databases.models import TokenData

router = APIRouter(
    prefix="/api/v1/translate",
    tags=["translate"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/{id}")
async def get_translation(id: int, db: Session = Depends(get_db)):
    token_data = db.query(TokenData).filter(TokenData.id == id).first()
    if not token_data:
        raise HTTPException(status_code=404, detail="Translation not found")

    return token_data


@router.delete("/{id}")
async def delete_translation(id: int, db: Session = Depends(get_db)):
    db.query(TokenData).filter(TokenData.id ==
                               id).delete(synchronize_session=False)
    db.commit()
    return HTTP_202_ACCEPTED


@router.post("/")
async def translate_endpoint(requestBody: schema.TranslateRequest, client: OpenAI = Depends(get_openai_client), db: Session = Depends(get_db)):
    role_description = """
    You are a translation machine, you are tasked with translate any text you are given to Spanish language.
    You only have to return the translated text
    """
    input_tokens = calculate_tokens_count(
        requestBody.text_to_translate, "gpt-4o-mini")

    request = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": f"{role_description}"},
                  {"role": "user", "content": requestBody.text_to_translate}]
    )

    output = request.choices[0].message.content
    output_tokens = calculate_tokens_count(output, "gpt-4o-mini")

    new_token_data = TokenData(
        input_text=requestBody.text_to_translate,
        input_token_count=input_tokens,
        output_text=output,
        output_token_count=output_tokens
    )

    db.add(new_token_data)
    db.commit()
    db.refresh(new_token_data)

    return {"message": f"{output} . Input tokens:{input_tokens}/Output tokens{output_tokens}:"}
