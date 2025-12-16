from pydantic import BaseModel


class TranslateRequest(BaseModel):
    text_to_translate: str
