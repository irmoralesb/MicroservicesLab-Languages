from pydantic import BaseModel, ConfigDict

class TranslateEndpointRequest(BaseModel):
    text_to_translate:str
    translate_to_language:str
# class TranslateRequest(BaseModel):
#     text_to_translate: str


# class TokenDataRequest(BaseModel):
#     id: int
#     input_text: str
#     input_token_count: int
#     output_text: str
#     output_token_count: int


# class DisplayTokenData(BaseModel):
#     input_text: str
#     output_text: str
#     model_config = ConfigDict(from_attributes=True)