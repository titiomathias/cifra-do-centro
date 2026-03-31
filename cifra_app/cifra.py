from __future__ import annotations
import re, sys, argparse

import unicodedata

def _norm(s):
    """Remove acentos para comparacao interna."""
    return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode()

_VALUES_RAW = {
    "coisinha": 1, "coisa": 2, "coiso": 3, "trem": 5,
    "negocio": 7, "bagulho": 11, "troco": 13, "parada": 16,
    "birosca": 32, "zica": 64, "fulero": -1,
}
_MODIFIERS_RAW = {"meio": 0.5, "dobro": 2.0, "triplo": 3.0, "um monte": 10.0}
_OPERATORS = {"e": 1, "a": 1, "o": 2}

ASCII_MIN, ASCII_MAX = 33, 126

# versoes com acento para output bonito
_PRETTY = {"negocio": "neg\u00f3cio", "troco": "tro\u00e7o", "ne": "n\u00e9", "ai": "a\u00ed", "dai": "da\u00ed"}


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
    """Decodifica Cifra do Centro para texto legivel."""
    tokens = _tokenize(cifra)
    result = []
    buf = []
    next_upper = [False]

    def flush(sep):
        if sep == "dai":
            buf.clear(); next_upper[0] = False; return
        if not buf: return
        val = _eval_expr(list(buf)); buf.clear()
        char = chr(val)
        if next_upper[0]:
            char = char.upper() if char.isalpha() else char  # regra 6
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
    ("dobro zica", 128), ("triplo birosca", 96), ("zica", 64),
    ("birosca", 32), ("parada", 16), ("troco", 13), ("bagulho", 11),
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
    """Codifica texto para Cifra do Centro. Suporta ASCII 32-126."""
    out = []
    last = len(text) - 1
    for i, ch in enumerate(text):
        av = ord(ch)
        if ch == " ":
            out.append("dai"); continue
        if av < ASCII_MIN or av > ASCII_MAX:
            raise ValueError(f"'{ch}' (ASCII {av}) fora da faixa {ASCII_MIN}-{ASCII_MAX}")
        upper = ch.isupper() and ch.isalpha()
        target = av + 32 if upper else av
        sep = "ne" if i == last else "ai"
        out.append(f"{'vixe ' if upper else ''}{_encode_int(target)} {sep}")
    if out and out[-1] == "dai":
        out.append("ne")
    return _prettify(" ".join(out))


if __name__ == "__main__":
    p = argparse.ArgumentParser(prog="cifra_do Centro", description="Cifra do Centro v1.1")
    p.add_argument("modo", choices=["encode", "decode"])
    p.add_argument("texto")
    a = p.parse_args()
    try:
        print(encode(a.texto) if a.modo == "encode" else decode(a.texto))
    except ValueError as e:
        print(f"Erro: {e}", file=sys.stderr); sys.exit(1)
