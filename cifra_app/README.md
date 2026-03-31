# Cifra do Centro — servidor web v1.1

Encode/decode via FastAPI. O Python é a única fonte de verdade para a lógica da cifra.

## Estrutura

```
cifra-do-centro/
├── app/
│   ├── main.py            # FastAPI — endpoints e serve o static/
│   ├── cifra.py           # lógica da cifra (única fonte de verdade)
│   └── requirements.txt
└── static/
    └── index.html         # interface web (chama a API, sem lógica própria)
```

## Instalação

```bash
cd app
pip install -r requirements.txt
```

## Rodar

```bash
cd app
uvicorn main:app --reload
```

Acesse: http://localhost:8000

Documentação automática da API: http://localhost:8000/docs

## Endpoints

| Método | Rota      | Body                    | Retorno               |
|--------|-----------|-------------------------|---------------------- |
| POST   | `/encode` | `{ "text": "Oi!" }`     | `{ "result": "..." }` |
| POST   | `/decode` | `{ "text": "vixe ..." }`| `{ "result": "Oi!" }` |
| GET    | `/health` | —                       | `{ "status": "ok" }`  |
| GET    | `/`       | —                       | página HTML           |

## Erros

Erros de validação retornam HTTP 422 com `{ "detail": "mensagem" }`.

## Usar o módulo diretamente

```python
from cifra import encode, decode

print(encode("Oi!"))
print(decode("vixe triplo birosca e troço e coisa aí ..."))
```

## CLI

```bash
python cifra_do Centro.py encode "Oi!"
python cifra_do Centro.py decode "vixe ..."
```
