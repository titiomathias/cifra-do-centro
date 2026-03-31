# Cifra do Centro

Uma linguagem cifrada em português coloquial onde sequências de palavras genéricas codificam valores Unicode (Latin-1) via expressões aritméticas. Suporte completo a caracteres acentuados do português brasileiro.

## Motivação

Analistas de segurança ofensiva frequentemente não podem mencionar clientes, projetos ou alvos. Conversas do dia a dia recorrem a termos vagos e ambíguos — *aquele negócio*, *o trem lá*, *a parada do cliente*, *o negócio mal configurado*, *o cliente não avisou da coisa*. A Cifra do Centro formaliza exatamente isso: um protocolo de comunicação onde frases coloquiais carregam informação precisa sem revelar nada diretamente.

## Como funciona

Cada caractere é codificado como uma expressão aritmética composta de **palavras-raiz** (valores fixos), **operadores** e **modificadores**, delimitada por **separadores**.

```
vixe zica e birosca e coisinha aí  →  maiúsc(64+32+1=97)  →  'A'
zica e birosca e coisinha aí       →  64+32+1  →  'a'
birosca e coisinha né              →  32+1     →  '!'
problema e zica e coiso e birosca né  →  128+64+3+32  →  'ã'
vixe problema e zica e fazido né   →  maiúsc(128+64+41=233)  →  'É'
```

### Referência rápida

```
── valores (21 palavras) ────────────────────
coisinha=1   coisa=2      coiso=3      trem=5
negócio=7    bagulho=11   troço=13     parada=16
treco=17     trequinho=19 coisada=23   coisado=29
birosca=32   fazida=37    fazido=41    da=43
do=47        de=53        zica=64      problema=128
fulero=−1

── modificadores ────────────────────────────
meio=÷2   ué=×2   mó=×3   um monte=×10

── operadores ───────────────────────────────
e=+  a=−  o=×   (precedência: o > e/a)

── separadores ──────────────────────────────
aí   → delimita caractere
daí  → espaço (único encoding de espaço)
vixe → próxima letra é maiúscula (code point − 32)
né   → fim do texto

── faixa ────────────────────────────────────
code points 33–252 (ASCII imprimível + Latin-1 pt-BR)
```

Não há codificação canônica — qualquer expressão que produza o code point correto é válida.

### Caracteres acentuados pt-BR

`vixe` opera como **code point − 32**, funcionando tanto para letras básicas quanto acentuadas (a diferença maiúsc/minúsc é sempre 32 em Latin-1):

```
ã (227)  →  problema e zica e coiso e birosca
Ã (195)  →  vixe problema e zica e coiso e birosca
é (233)  →  problema e zica e fazido
ç (231)  →  problema e zica e coisa e fazida
```

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
│   └── cifra_bagulhes_spec_v1_2.html
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

Retorna HTTP 422 com `{ "detail": "..." }` para entradas inválidas (texto vazio, code point fora de 33–252, token desconhecido).

## Uso direto

```python
from cifra import encode, decode

encode("São Paulo")
decode("vixe zica e de a coisa aí problema e zica e coiso e birosca aí zica e do né")
```

---

Demo online: [cdc.discloud.app](https://cdc.discloud.app/) — encode e decode direto no navegador.

Spec completa: [`docs/cifra_bagulhes_spec_v1_2.html`](docs/cifra_bagulhes_spec_v1_2.html)
