from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from models.models import TextIn, TextOut
from cifra import encode, decode

app = FastAPI(
    title="Cifra do Centro",
    version="1.1.0",
    docs_url=None,
    redoc_url=None,
)

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.post("/encode", response_model=TextOut)
def api_encode(body: TextIn):
    if not body.text:
        raise HTTPException(status_code=422, detail="Campo 'text' não pode ser vazio.")
    try:
        return TextOut(result=encode(body.text))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/decode", response_model=TextOut)
def api_decode(body: TextIn):
    if not body.text:
        raise HTTPException(status_code=422, detail="Campo 'text' não pode ser vazio.")
    try:
        return TextOut(result=decode(body.text))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index():
    html_path = STATIC_DIR / "index.html"
    print(html_path)
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="ocorreu um erro inesperado. entre em contato com o responsável.")
    return FileResponse(html_path)
