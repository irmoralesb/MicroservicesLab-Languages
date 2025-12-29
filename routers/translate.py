"""
Router in charge of translation between two languages
"""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.params import Depends
from sqlalchemy.orm import Session
#from openai import OpenAI
from starlette.status import HTTP_202_ACCEPTED
#from dependencies.openai import calculate_tokens_count, get_openai_client
from . import translate_schemas as schema
from databases.database import SessionLocal
from databases.models import TokenData
from typing import List
from llm_tools.llm_tools import llm_factory
from llm_tools.llm_tools.llm_interface import LLMInterface


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

def get_llm_interface():
    return llm_factory.LLMFactory().create_llm('openai',"gpt-4o-mini")


@router.get("/", response_model=List[schema.DisplayTokenData])
def get_all_translations(db: Session = Depends(get_db)):
    token_list = db.query(TokenData).all()
    return token_list


# The response model is used to filter the options to show!!!!!
@router.get("/{id}", response_model=schema.DisplayTokenData)
async def get_translation(id: int, response: Response, db: Session = Depends(get_db)):
    token_data = db.query(TokenData).filter(TokenData.id == id).first()
    if not token_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Translation not found")

    return token_data


@router.delete("/{id}")
async def delete_translation(id: int, db: Session = Depends(get_db)):
    db.query(TokenData).filter(TokenData.id ==
                               id).delete(synchronize_session=False)
    db.commit()
    return HTTP_202_ACCEPTED


@router.post("/", status_code=status.HTTP_201_CREATED)
async def translate_endpoint(requestBody: schema.TranslateRequest, llm_tool: LLMInterface = Depends(get_llm_interface)):
    # role_description = """
    # You are a translation machine, you are tasked with translate any text you are given to Spanish language.
    # You only have to return the translated text
    # """
    # input_tokens = calculate_tokens_count(
    #     requestBody.text_to_translate, "gpt-4o-mini")

    translated_text = llm_tool.translate_text(requestBody.text_to_translate,"spanish")
    return {"message": f"{translated_text}"}

    # output = request.choices[0].message.content
    # output_tokens = calculate_tokens_count(output, "gpt-4o-mini")

    # new_token_data = TokenData(
    #     input_text=requestBody.text_to_translate,
    #     input_token_count=input_tokens,
    #     output_text=output,
    #     output_token_count=output_tokens
    # )

    # db.add(new_token_data)
    # db.commit()
    # db.refresh(new_token_data)

    # return {"message": f"{output} . Input tokens:{input_tokens}/Output tokens{output_tokens}:"}


# @router.post("/", status_code=status.HTTP_201_CREATED)
# async def translate_endpoint(requestBody: schema.TranslateRequest, client: OpenAI = Depends(get_openai_client), db: Session = Depends(get_db)):
#     role_description = """
#     You are a translation machine, you are tasked with translate any text you are given to Spanish language.
#     You only have to return the translated text
#     """
#     input_tokens = calculate_tokens_count(
#         requestBody.text_to_translate, "gpt-4o-mini")

#     request = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[{"role": "system", "content": f"{role_description}"},
#                   {"role": "user", "content": requestBody.text_to_translate}]
#     )

#     output = request.choices[0].message.content
#     output_tokens = calculate_tokens_count(output, "gpt-4o-mini")

#     new_token_data = TokenData(
#         input_text=requestBody.text_to_translate,
#         input_token_count=input_tokens,
#         output_text=output,
#         output_token_count=output_tokens
#     )

#     db.add(new_token_data)
#     db.commit()
#     db.refresh(new_token_data)

#     return {"message": f"{output} . Input tokens:{input_tokens}/Output tokens{output_tokens}:"}


@router.put("/{id}")
def update(id: int, requestBody: schema.TokenDataRequest, db: Session = Depends(get_db)):
    token_data_db = db.query(TokenData).filter(TokenData.id == id).first()
    if not token_data_db:
        raise HTTPException(status_code=404, detail="Not found")

    token_data_db.input_text = requestBody.input_text
    token_data_db.input_token_count = requestBody.input_token_count
    token_data_db.output_text = requestBody.output_text
    token_data_db.output_token_count = requestBody.output_token_count

    db.commit()
    db.refresh(token_data_db)
    return {'Product successfully updated'}
