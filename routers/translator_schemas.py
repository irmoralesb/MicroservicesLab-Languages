from pydantic import BaseModel, ConfigDict

class TranslateEndpointRequest(BaseModel):
    text_to_translate:str
    translate_to_language:str
