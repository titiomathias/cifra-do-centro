from pydantic import BaseModel, Field

# Limite para /encode: texto plano — 10 000 chars cobre qualquer mensagem razoável
# e evita respostas de ~300 KB de cifra que travariam a VPS de 512 MB.
class EncodeIn(BaseModel):
    text: str = Field(max_length=10_000)

# Limite para /decode: a cifra é ~30× maior que o texto plano,
# então 500 000 chars de cifra equivalem a ~16 000 chars decodificados.
class DecodeIn(BaseModel):
    text: str = Field(max_length=500_000)

class TextOut(BaseModel):
    result: str