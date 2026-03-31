from __future__ import annotations
import re, sys, argparse

import unicodedata

def _norm(s):
    """Remove acentos para comparacao interna."""
    return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode()

_VALUES_RAW = {
    "coisinha": 1, "coisa": 2, "coiso": 3, "trem": 5,
    "negocio": 7, "bagulho": 11, "troco": 13, "parada": 16,
    "treco": 17, "trequinho": 19, "coisada": 23, "coisado": 29,
    "birosca": 32, "fazida": 37, "fazido": 41, "da": 43,
    "do": 47, "de": 53, "zica": 64, "problema": 128,
    "fulero": -1,
}
_MODIFIERS_RAW = {"meio": 0.5, "ue": 2.0, "mo": 3.0, "um monte": 10.0}
_OPERATORS = {"e": 1, "a": 1, "o": 2}

ASCII_MIN, ASCII_MAX = 33, 252

# versoes com acento para output bonito
_PRETTY = {
    "negocio": "negócio", "troco": "troço",
    "ne": "né", "ai": "aí", "dai": "daí",
    "ue": "ué", "mo": "mó",
}


def _tokenize(text):
    text = _norm(text.strip().lower())
    text = re.sub(r'\bum\s+monte\b', 'um_monte', text)
    return [t.replace('um_monte', 'um monte') for t in text.split()]


def _eval_expr(tokens):
    resolved = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in _MODIFIERS_RAW:
            scale = _MODIFIERS_RAW[tok]; i += 1
            if i >= len(tokens) or tokens[i] not in _VALUES_RAW:
                raise ValueError(f"Modificador '{tok}' sem valor seguinte")
            resolved.append(int(_VALUES_RAW[tokens[i]] * scale))
        elif tok in _VALUES_RAW:
            resolved.append(_VALUES_RAW[tok])
        elif tok in _OPERATORS:
            resolved.append(tok)
        else:
            raise ValueError(f"Token desconhecido: '{tok}'")
        i += 1

    terms = list(resolved)
    while "o" in terms:
        idx = terms.index("o")
        terms = terms[:idx-1] + [int(terms[idx-1]) * int(terms[idx+1])] + terms[idx+2:]

    acc = int(terms[0])
    i = 1
    while i < len(terms):
        op, operand = terms[i], int(terms[i+1])
        acc = acc + operand if op == "e" else acc - operand
        i += 2
    return acc


def decode(cifra:str):
    tokens = _tokenize(cifra)
    result = []
    buf = []
    next_upper = [False]

    def flush(sep):
        if sep == "dai":
            buf.clear(); next_upper[0] = False; return
        if not buf: return
        val = _eval_expr(list(buf)); buf.clear()
        if next_upper[0]:
            upper_val = val - 32
            # regra 6: se resultado nao for letra, vixe e ignorado silenciosamente
            char = chr(upper_val) if 0 <= upper_val <= 0x10FFFF and chr(upper_val).isalpha() else chr(val)
        else:
            char = chr(val)
        next_upper[0] = False
        result.append(char)

    for tok in tokens:
        if tok == "ne":
            flush("ne"); break
        elif tok == "ai":
            flush("ai")
        elif tok == "dai":
            flush("dai"); result.append(" ")
        elif tok == "vixe":
            next_upper[0] = True
        else:
            buf.append(tok)
    else:
        if buf: flush("ne")

    return "".join(result)


_ATOMS = sorted([
    ("mo zica", 192), ("problema", 128), ("mo birosca", 96),
    ("zica", 64), ("de", 53), ("do", 47), ("da", 43),
    ("fazido", 41), ("fazida", 37), ("birosca", 32),
    ("coisado", 29), ("coisada", 23), ("trequinho", 19),
    ("treco", 17), ("parada", 16), ("troco", 13), ("bagulho", 11),
    ("negocio", 7), ("trem", 5), ("coiso", 3), ("coisa", 2), ("coisinha", 1),
], key=lambda x: -x[1])


def _encode_int(n):
    if n <= 0:
        raise ValueError(f"Valor {n} invalido")
    parts = []
    rem = n
    for expr, val in _ATOMS:
        if val <= 0 or val > rem: continue
        count = rem // val; rem -= count * val
        parts.extend([expr] * count)
        if rem == 0: break
    if rem > 0:
        # tenta subtracao fina: atom maior - diferenca
        for expr, val in reversed(_ATOMS):
            if val > rem:
                diff = val - rem
                if diff <= 13:
                    parts.append(f"{expr} a {_encode_int(diff)}")
                    rem = 0; break
    if rem > 0:
        parts.extend(["coisinha"] * rem)
    return " e ".join(parts)


def _prettify(s):
    """Substitui tokens internos pelos equivalentes com acento."""
    for k, v in _PRETTY.items():
        s = re.sub(rf'\b{k}\b', v, s)
    return s


def encode(text:str):
    out = []
    last = len(text) - 1
    for i, ch in enumerate(text):
        cp = ord(ch)
        if ch == " ":
            out.append("dai"); continue
        if cp < ASCII_MIN or cp > ASCII_MAX:
            raise ValueError(f"'{ch}' (code point {cp}) fora da faixa {ASCII_MIN}-{ASCII_MAX}")
        upper = ch.isupper() and ch.isalpha()
        target = cp + 32 if upper else cp
        sep = "ne" if i == last else "ai"
        out.append(f"{'vixe ' if upper else ''}{_encode_int(target)} {sep}")
    if out and out[-1] == "dai":
        out.append("ne")
    return _prettify(" ".join(out))


if __name__ == "__main__":
    p = argparse.ArgumentParser(prog="cifra_do_centro", description="Cifra do Centro v1.3")
    p.add_argument("modo", choices=["encode", "decode"])
    p.add_argument("texto")
    a = p.parse_args()
    try:
        print(encode(a.texto) if a.modo == "encode" else decode(a.texto))
    except ValueError as e:
        print(f"Erro: {e}", file=sys.stderr); sys.exit(1)
