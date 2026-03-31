import pytest
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from cifra import encode, decode, _tokenize, _eval_expr, _encode_int, ASCII_MIN, ASCII_MAX


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def roundtrip(text: str) -> bool:
    return decode(encode(text)) == text


# ─────────────────────────────────────────────────────────────────────────────
# 1. Tokenizer
# ─────────────────────────────────────────────────────────────────────────────

class TestTokenizer:

    def test_simples(self):
        assert _tokenize("coisa e coiso") == ["coisa", "e", "coiso"]

    def test_strip_e_lowercase(self):
        assert _tokenize("  COISA E COISO  ") == ["coisa", "e", "coiso"]

    def test_acentos_normalizados(self):
        tokens = _tokenize("negócio e troço")
        assert tokens == ["negocio", "e", "troco"]

    def test_um_monte_como_token_unico(self):
        assert _tokenize("um monte birosca") == ["um monte", "birosca"]

    def test_um_monte_com_espacos_extras(self):
        assert _tokenize("um  monte birosca") == ["um monte", "birosca"]

    def test_separadores_presentes(self):
        tokens = _tokenize("zica aí coisa né")
        assert tokens == ["zica", "ai", "coisa", "ne"]


# ─────────────────────────────────────────────────────────────────────────────
# 2. Avaliador de expressão
# ─────────────────────────────────────────────────────────────────────────────

class TestEvalExpr:

    def test_valor_simples(self):
        assert _eval_expr(["zica"]) == 64

    def test_adicao(self):
        assert _eval_expr(["zica", "e", "coisa"]) == 66        # 64+2

    def test_subtracao(self):
        assert _eval_expr(["zica", "a", "coisinha"]) == 63     # 64-1

    def test_multiplicacao(self):
        assert _eval_expr(["coisa", "o", "trem"]) == 10        # 2×5

    def test_precedencia_mult_sobre_soma(self):
        # zica e coisa o trem = 64 + (2×5) = 74, não (64+2)×5
        assert _eval_expr(["zica", "e", "coisa", "o", "trem"]) == 74

    def test_precedencia_mult_sobre_sub(self):
        # parada a coisa o coiso = 16 - (2×3) = 10
        assert _eval_expr(["parada", "a", "coisa", "o", "coiso"]) == 10

    def test_modificador_dobro(self):
        assert _eval_expr(["dobro", "birosca"]) == 64           # 32×2

    def test_modificador_meio(self):
        assert _eval_expr(["meio", "birosca"]) == 16            # 32÷2

    def test_modificador_triplo(self):
        assert _eval_expr(["triplo", "coiso"]) == 9             # 3×3

    def test_modificador_um_monte(self):
        assert _eval_expr(["um monte", "coisa"]) == 20          # 2×10

    def test_modificador_meio_arredonda_baixo(self):
        assert _eval_expr(["meio", "coiso"]) == 1               # 3÷2 → 1

    def test_fulero(self):
        assert _eval_expr(["zica", "e", "fulero"]) == 63        # 64+(−1)

    def test_triplo_birosca(self):
        assert _eval_expr(["triplo", "birosca"]) == 96          # 32×3

    def test_token_desconhecido_levanta_erro(self):
        with pytest.raises(ValueError, match="Token desconhecido"):
            _eval_expr(["palavrainventada"])

    def test_modificador_sem_valor_levanta_erro(self):
        with pytest.raises(ValueError, match="sem valor seguinte"):
            _eval_expr(["dobro"])

    def test_modificador_seguido_de_operador_levanta_erro(self):
        with pytest.raises(ValueError, match="sem valor seguinte"):
            _eval_expr(["dobro", "e"])


# ─────────────────────────────────────────────────────────────────────────────
# 3. Exemplos da spec
# ─────────────────────────────────────────────────────────────────────────────

class TestExemplosDaSpec:
    """Expressões validadas pelo encoder real."""

    def test_A_maiusculo(self):
        # 'A' = vixe + expressão de 'a' (ASCII 97 = triplo birosca e coisinha = 96+1)
        assert decode("vixe triplo birosca e coisinha né") == "A"

    def test_a_minusculo(self):
        # ASCII 97 = triplo birosca e coisinha = 96+1
        assert _eval_expr(["triplo", "birosca", "e", "coisinha"]) == 97
        assert decode("triplo birosca e coisinha né") == "a"

    def test_exclamacao(self):
        # ASCII 33 = birosca e coisinha = 32+1
        assert _eval_expr(["birosca", "e", "coisinha"]) == 33
        assert decode("birosca e coisinha né") == "!"

    def test_frase_oi(self):
        # encode("oi") → expressões abaixo
        assert decode(
            "triplo birosca e troço e coisa aí "
            "triplo birosca e negócio e coisa né"
        ) == "oi"

    def test_expressao_com_acento_ou_sem_equivalente(self):
        # negócio e troço com e sem acento devem avaliar igual
        assert _eval_expr(["negocio", "e", "troco"]) == _eval_expr(["negocio", "e", "troco"])


# ─────────────────────────────────────────────────────────────────────────────
# 4. Decoder — separadores
# ─────────────────────────────────────────────────────────────────────────────

class TestDecoderSeparadores:

    # expressões auxiliares para 'a' (97) e 'b' (98)
    ENC_A = "triplo birosca e coisinha"   # 96+1 = 97 → 'a'
    ENC_B = "triplo birosca e coisa"      # 96+2 = 98 → 'b'

    def test_ai_separa_chars(self):
        assert decode(f"{self.ENC_A} aí {self.ENC_B} né") == "ab"

    def test_dai_insere_espaco(self):
        # 'a a': encoder gera aí daí, não apenas daí
        assert decode(f"{self.ENC_A} aí daí {self.ENC_A} né") == "a a"

    def test_ne_encerra_processamento(self):
        # tudo após né é ignorado
        assert decode(f"{self.ENC_A} né zica e coisa") == "a"

    def test_sem_ne_ainda_funciona(self):
        assert decode(self.ENC_A) == "a"

    def test_dai_no_inicio(self):
        assert decode(f"daí {self.ENC_A} né") == " a"

    def test_apenas_espaco(self):
        assert decode("daí né") == " "

    def test_multiplos_espacos(self):
        assert decode(f"{self.ENC_A} aí daí daí {self.ENC_A} né") == "a  a"


# ─────────────────────────────────────────────────────────────────────────────
# 5. Decoder — vixe (maiúsculas, regra 6)
# ─────────────────────────────────────────────────────────────────────────────

class TestVixe:

    ENC_A_LOWER = "triplo birosca e coisinha"   # → 'a'
    ENC_B_LOWER = "triplo birosca e coisa"      # → 'b'

    def test_vixe_letra_vira_maiuscula(self):
        assert decode(f"vixe {self.ENC_A_LOWER} né") == "A"

    def test_sem_vixe_permanece_minusculo(self):
        assert decode(f"{self.ENC_A_LOWER} né") == "a"

    def test_vixe_antes_nao_letra_ignorado(self):
        # '!' ASCII 33 — vixe deve ser ignorado silenciosamente (regra 6)
        assert decode("vixe birosca e coisinha né") == "!"

    def test_vixe_nao_contamina_proximo_char(self):
        assert decode(f"vixe {self.ENC_A_LOWER} aí {self.ENC_B_LOWER} né") == "Ab"

    def test_vixe_consecutivos(self):
        assert decode(
            f"vixe {self.ENC_A_LOWER} aí vixe {self.ENC_B_LOWER} né"
        ) == "AB"

    def test_vixe_aceita_separador_acentuado(self):
        assert decode(f"vixe {self.ENC_A_LOWER} né") == "A"


# ─────────────────────────────────────────────────────────────────────────────
# 6. Encoder
# ─────────────────────────────────────────────────────────────────────────────

class TestEncoder:

    def test_encode_retorna_string(self):
        assert isinstance(encode("a"), str)

    def test_encode_termina_com_ne(self):
        assert encode("oi").strip().endswith("né")

    def test_encode_espaco_usa_dai(self):
        assert "daí" in encode("a b")

    def test_encode_maiusculo_usa_vixe(self):
        assert encode("A").startswith("vixe")

    def test_encode_minusculo_sem_vixe(self):
        assert not encode("a").startswith("vixe")

    def test_encode_char_invalido_levanta_erro(self):
        with pytest.raises(ValueError, match="fora da faixa"):
            encode("ç")

    def test_encode_char_abaixo_do_minimo(self):
        with pytest.raises(ValueError):
            encode("\x01")

    def test_encode_texto_vazio_retorna_vazio(self):
        assert encode("") == ""

    def test_encode_apenas_espaco(self):
        result = encode(" ")
        assert "daí" in result
        assert "né" in result

    def test_encode_int_zero_levanta_erro(self):
        with pytest.raises(ValueError):
            _encode_int(0)

    def test_encode_int_negativo_levanta_erro(self):
        with pytest.raises(ValueError):
            _encode_int(-5)

    @pytest.mark.parametrize("ascii_val", range(ASCII_MIN, ASCII_MAX + 1))
    def test_encode_int_cobre_faixa_completa(self, ascii_val):
        """_encode_int deve gerar expressão correta para todo ASCII 33–126."""
        expr = _encode_int(ascii_val)
        tokens = _tokenize(expr)
        assert _eval_expr(tokens) == ascii_val, \
            f"ASCII {ascii_val}: '{expr}' avaliou para {_eval_expr(tokens)}"


# ─────────────────────────────────────────────────────────────────────────────
# 7. Round-trip
# ─────────────────────────────────────────────────────────────────────────────

class TestRoundtrip:

    @pytest.mark.parametrize("text", [
        "a", "z", "A", "Z",
        "oi", "Oi", "Oi!",
        "hello world",
        "Hello, World!",
        "bagulho top",
        "abc ABC",
        "The quick brown fox",
        "1234567890",
        "!@#$%&*()",
        "aZ bY cX",
    ])
    def test_roundtrip_textos_comuns(self, text):
        assert roundtrip(text), f"Falhou para: {text!r}"

    @pytest.mark.parametrize("ascii_val", range(ASCII_MIN, ASCII_MAX + 1))
    def test_roundtrip_todo_ascii_imprimivel(self, ascii_val):
        """Todo caractere ASCII 33–126 deve sobreviver ao round-trip."""
        ch = chr(ascii_val)
        assert roundtrip(ch), f"Falhou para ASCII {ascii_val} ('{ch}')"

    def test_roundtrip_frase_com_espacos_multiplos(self):
        assert roundtrip("a b c")

    def test_roundtrip_so_maiusculas(self):
        assert roundtrip("ABC")

    def test_roundtrip_alternando_case(self):
        assert roundtrip("aAbBcC")

    def test_roundtrip_idempotente(self):
        # encode->decode->encode deve gerar a mesma cifra
        text = "Oi!"
        c1 = encode(text)
        c2 = encode(decode(c1))
        assert c1 == c2


# ─────────────────────────────────────────────────────────────────────────────
# 8. Decoder — tolerância de entrada
# ─────────────────────────────────────────────────────────────────────────────

class TestDecoderTolerancia:

    def test_aceita_tokens_sem_acento(self):
        # "negocio" sem acento deve funcionar igual a "negócio"
        r1 = decode("negocio ne")
        r2 = decode("negócio né")
        assert r1 == r2

    def test_aceita_tokens_com_acento(self):
        assert decode("negócio né") == chr(7)

    def test_aceita_cifra_em_maiusculas(self):
        # CAIXA ALTA deve ser normalizada
        assert decode("TRIPLO BIROSCA E COISINHA NE") == "a"

    def test_aceita_separadores_sem_acento(self):
        ENC_A = "triplo birosca e coisinha"
        assert decode(f"{ENC_A} ai {ENC_A} ne") == "aa"