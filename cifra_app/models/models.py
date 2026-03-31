from pydantic import BaseModel

class TextIn(BaseModel):
    text: str

class TextOut(BaseModel):
    result: str