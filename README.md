# Cifra do Centro

Uma linguagem cifrada em português coloquial onde sequências de palavras genéricas codificam texto via expressões aritméticas sobre ASCII.

## Motivação

Analistas de segurança ofensiva frequentemente não podem mencionar clientes, projetos ou alvos. Conversas do dia a dia recorrem a termos vagos e ambíguos — *aquele negócio*, *o trem lá*, *a parada do cliente*, *o negócio mal configurado*, *o cliente não avisou da coisa*. A Cifra do Centro formaliza exatamente isso: um protocolo de comunicação onde frases coloquiais carregam informação precisa sem revelar nada diretamente.

## Como funciona

Cada caractere é codificado como uma expressão aritmética composta de **palavras-raiz** (valores fixos), **operadores** e **modificadores**, delimitada por **separadores**.

```
vixe zica e coisa aí   →  maiúsc(64 + 2)  →  'A'
dobro birosca e coiso aí   →  (32×2) + 3  →  'a'
birosca e coisinha né   →  32 + 1  →  '!'
```

### Referência rápida

```
── valores ──────────────────────────────────
coisinha=1  coisa=2   coiso=3   trem=5
negócio=7   bagulho=11  troço=13  parada=16
birosca=32  zica=64   fulero=−1

── modificadores ────────────────────────────
meio=÷2  dobro=×2  triplo=×3  um monte=×10

── operadores ───────────────────────────────
e=+  a=−  o=×   (precedência: o > e/a)

── separadores ──────────────────────────────
aí   → delimita caractere
daí  → espaço (único encoding de espaço)
vixe → próxima letra é maiúscula
né   → fim do texto
```

Não há codificação canônica — qualquer expressão que produza o valor ASCII correto é válida.

## Estrutura

```
cifra/
├── cifra_app/
│   ├── cifra.py           # lógica da cifra (fonte de verdade)
│   ├── main.py            # API FastAPI (encode / decode)
│   └── requirements.txt
├── cifra_static/
│   └── index.html         # interface web
├── docs/
│   └── cifra_centro_spec_v1.1.html
└── Dockerfile
```

## Rodar

```bash
cd cifra_app
pip install -r requirements.txt
uvicorn main:app --reload
```

Ou via Docker:

```bash
docker build -t cifra .
docker run -p 8000:8000 cifra
```

Acesse `http://localhost:8000` para a interface web ou `http://localhost:8000/docs` para a API.

## API

| Método | Rota      | Body                     | Retorno               |
|--------|-----------|--------------------------|----------------------|
| POST   | `/encode` | `{ "text": "Oi!" }`      | `{ "result": "..." }` |
| POST   | `/decode` | `{ "text": "vixe ..." }` | `{ "result": "Oi!" }` |
| GET    | `/health` | —                        | `{ "status": "ok" }`  |

## Uso direto

```python
from cifra import encode, decode

encode("Oi!")
decode("vixe dobro birosca e dobro negócio e coiso aí ...")
```

---

Demo online: [cdc.discloud.app](https://cdc.discloud.app/) — encode e decode direto no navegador.

Spec completa: [`docs/cifra_centro_spec_v1.1.html`](docs/cifra_centro_spec_v1.1.html)
