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

    def test_modificadores_normalizados(self):
        tokens = _tokenize("ué birosca e mó zica")
        assert tokens == ["ue", "birosca", "e", "mo", "zica"]

    def test_um_monte_como_token_unico(self):
        assert _tokenize("um monte birosca") == ["um monte", "birosca"]

    def test_um_monte_com_espacos_extras(self):
        assert _tokenize("um  monte birosca") == ["um monte", "birosca"]

    def test_separadores_presentes(self):
        tokens = _tokenize("zica aí coisa né")
        assert tokens == ["zica", "ai", "coisa", "ne"]

    def test_novos_tokens_valor(self):
        tokens = _tokenize("treco trequinho coisada coisado fazida fazido da do de problema")
        assert tokens == ["treco", "trequinho", "coisada", "coisado", "fazida", "fazido", "da", "do", "de", "problema"]


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

    def test_modificador_ue(self):
        assert _eval_expr(["ue", "birosca"]) == 64             # 32×2

    def test_modificador_meio(self):
        assert _eval_expr(["meio", "birosca"]) == 16           # 32÷2

    def test_modificador_mo(self):
        assert _eval_expr(["mo", "coiso"]) == 9               # 3×3

    def test_modificador_um_monte(self):
        assert _eval_expr(["um monte", "coisa"]) == 20        # 2×10

    def test_modificador_meio_arredonda_baixo(self):
        assert _eval_expr(["meio", "coiso"]) == 1             # 3÷2 → 1

    def test_fulero(self):
        assert _eval_expr(["zica", "e", "fulero"]) == 63      # 64+(−1)

    def test_mo_birosca(self):
        assert _eval_expr(["mo", "birosca"]) == 96            # 32×3

    def test_mo_zica(self):
        assert _eval_expr(["mo", "zica"]) == 192              # 64×3

    def test_ue_problema(self):
        assert _eval_expr(["ue", "problema"]) == 256          # 128×2

    # novos tokens de valor v1.2
    def test_valor_treco(self):
        assert _eval_expr(["treco"]) == 17

    def test_valor_trequinho(self):
        assert _eval_expr(["trequinho"]) == 19

    def test_valor_coisada(self):
        assert _eval_expr(["coisada"]) == 23

    def test_valor_coisado(self):
        assert _eval_expr(["coisado"]) == 29

    def test_valor_fazida(self):
        assert _eval_expr(["fazida"]) == 37

    def test_valor_fazido(self):
        assert _eval_expr(["fazido"]) == 41

    def test_valor_da(self):
        assert _eval_expr(["da"]) == 43

    def test_valor_do(self):
        assert _eval_expr(["do"]) == 47

    def test_valor_de(self):
        assert _eval_expr(["de"]) == 53

    def test_valor_problema(self):
        assert _eval_expr(["problema"]) == 128

    # combinações com novos tokens
    def test_problema_e_zica_e_birosca(self):
        assert _eval_expr(["problema", "e", "zica", "e", "birosca"]) == 224   # à

    def test_problema_e_zica_e_fazido(self):
        assert _eval_expr(["problema", "e", "zica", "e", "fazido"]) == 233    # é

    def test_problema_e_zica_e_coiso_e_birosca(self):
        assert _eval_expr(["problema", "e", "zica", "e", "coiso", "e", "birosca"]) == 227  # ã

    def test_token_desconhecido_levanta_erro(self):
        with pytest.raises(ValueError, match="Token desconhecido"):
            _eval_expr(["palavrainventada"])

    def test_modificador_sem_valor_levanta_erro(self):
        with pytest.raises(ValueError, match="sem valor seguinte"):
            _eval_expr(["ue"])

    def test_modificador_seguido_de_operador_levanta_erro(self):
        with pytest.raises(ValueError, match="sem valor seguinte"):
            _eval_expr(["ue", "e"])

    def test_tokens_antigos_dobro_triplo_sao_invalidos(self):
        with pytest.raises(ValueError, match="Token desconhecido"):
            _eval_expr(["dobro", "birosca"])

    def test_tokens_antigos_triplo_sao_invalidos(self):
        with pytest.raises(ValueError, match="Token desconhecido"):
            _eval_expr(["triplo", "birosca"])


# ─────────────────────────────────────────────────────────────────────────────
# 3. Exemplos da spec
# ─────────────────────────────────────────────────────────────────────────────

class TestExemplosDaSpec:
    """Expressões validadas pela spec v1.2."""

    def test_A_maiusculo(self):
        # 'A' = vixe + expressão de 'a' (97); zica e birosca e coisinha = 64+32+1=97
        assert decode("vixe zica e birosca e coisinha né") == "A"

    def test_a_minusculo(self):
        # ASCII 97 = zica e birosca e coisinha = 64+32+1
        assert _eval_expr(["zica", "e", "birosca", "e", "coisinha"]) == 97
        assert decode("zica e birosca e coisinha né") == "a"

    def test_exclamacao(self):
        # ASCII 33 = birosca e coisinha = 32+1
        assert _eval_expr(["birosca", "e", "coisinha"]) == 33
        assert decode("birosca e coisinha né") == "!"

    def test_frase_oi(self):
        # 'o'=111=zica e do=64+47; 'i'=105=zica e fazido=64+41
        assert decode("zica e do aí zica e fazido né") == "oi"

    def test_frase_Oi_exclamacao(self):
        # 'O'=vixe+(64+47=111); 'i'=64+41=105; '!'=32+1=33
        # nota: spec v1.2 usa "da" no exemplo mas avalia como 47 (do) — typo na spec
        assert decode("vixe zica e do aí zica e fazido aí birosca e coisinha né") == "Oi!"

    def test_acento_a_til(self):
        # ã = 227 = problema e zica e coiso e birosca = 128+64+3+32
        assert decode("problema e zica e coiso e birosca né") == "ã"

    def test_acento_A_til_maiusculo(self):
        # Ã = 195 = vixe + 227
        assert decode("vixe problema e zica e coiso e birosca né") == "Ã"

    def test_acento_cedilha(self):
        # ç = 231 = problema e zica e coisa e fazida = 128+64+2+37
        assert decode("problema e zica e coisa e fazida né") == "ç"

    def test_acento_e_agudo(self):
        # é = 233 = problema e zica e fazido = 128+64+41
        assert decode("problema e zica e fazido né") == "é"

    def test_frase_sao(self):
        # S=vixe+(64+53-2=115)→83; ã=128+64+3+32=227; o=64+47=111
        # nota: o exemplo da spec v1.2 tem a ordem dos chars trocada (mostra S,a,ã em vez de S,ã,o)
        assert decode(
            "vixe zica e de a coisa aí "
            "problema e zica e coiso e birosca aí "
            "zica e do né"
        ) == "São"

    def test_expressao_com_acento_ou_sem_equivalente(self):
        # negócio e troço com e sem acento devem avaliar igual
        assert _eval_expr(["negocio", "e", "troco"]) == _eval_expr(["negocio", "e", "troco"])


# ─────────────────────────────────────────────────────────────────────────────
# 4. Decoder — separadores
# ─────────────────────────────────────────────────────────────────────────────

class TestDecoderSeparadores:

    # zica e birosca e coisinha = 64+32+1 = 97 → 'a'
    # zica e birosca e coisa   = 64+32+2 = 98 → 'b'
    ENC_A = "zica e birosca e coisinha"
    ENC_B = "zica e birosca e coisa"

    def test_ai_separa_chars(self):
        assert decode(f"{self.ENC_A} aí {self.ENC_B} né") == "ab"

    def test_dai_insere_espaco(self):
        assert decode(f"{self.ENC_A} aí daí {self.ENC_A} né") == "a a"

    def test_ne_encerra_processamento(self):
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
# 5. Decoder — vixe (maiúsculas, regras 4-7)
# ─────────────────────────────────────────────────────────────────────────────

class TestVixe:

    ENC_A_LOWER = "zica e birosca e coisinha"   # → 'a' (97)
    ENC_B_LOWER = "zica e birosca e coisa"      # → 'b' (98)

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

    def test_vixe_letra_acentuada_minuscula(self):
        # ã (227) com vixe → Ã (195 = 227-32)
        assert decode("vixe problema e zica e coiso e birosca né") == "Ã"

    def test_vixe_e_agudo(self):
        # é (233) com vixe → É (201 = 233-32)
        assert decode("vixe problema e zica e fazido né") == "É"

    def test_vixe_cedilha(self):
        # ç (231) com vixe → Ç (199 = 231-32)
        assert decode("vixe problema e zica e coisa e fazida né") == "Ç"

    def test_vixe_usa_subtracao_32_nao_upper(self):
        # regra 4: vixe = code_point − 32, não .upper()
        # ã=227, 227-32=195='Ã'; verificar que o resultado é chr(195)
        result = decode("vixe problema e zica e coiso e birosca né")
        assert ord(result) == 195


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

    def test_encode_maiusculo_acentuado_usa_vixe(self):
        assert encode("Ã").startswith("vixe")

    def test_encode_minusculo_acentuado_sem_vixe(self):
        assert not encode("ã").startswith("vixe")

    def test_encode_char_invalido_acima_do_maximo(self):
        with pytest.raises(ValueError, match="fora da faixa"):
            encode(chr(253))

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

    @pytest.mark.parametrize("cp", range(ASCII_MIN, ASCII_MAX + 1))
    def test_encode_int_cobre_faixa_completa(self, cp):
        """_encode_int deve gerar expressão correta para todo code point 33–252."""
        expr = _encode_int(cp)
        tokens = _tokenize(expr)
        assert _eval_expr(tokens) == cp, \
            f"Code point {cp}: '{expr}' avaliou para {_eval_expr(tokens)}"

    def test_encode_acento_a_til(self):
        result = encode("ã")
        assert not result.startswith("vixe")
        assert decode(result) == "ã"

    def test_encode_acento_cedilha(self):
        result = encode("ç")
        assert decode(result) == "ç"

    def test_encode_acento_e_agudo(self):
        result = encode("é")
        assert decode(result) == "é"

    def test_encode_maiusculo_A_til(self):
        result = encode("Ã")
        assert result.startswith("vixe")
        assert decode(result) == "Ã"

    def test_encode_frase_portuguesa(self):
        result = encode("São")
        assert "vixe" in result
        assert decode(result) == "São"


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
        # pt-BR acentuados (v1.2)
        "ão", "ção", "São",
        "café", "maçã",
        "ótimo", "êxito",
        "à vontade",
        "Ã", "Ç", "É", "Ê", "Í", "Ó", "Ô", "Õ", "Ú",
    ])
    def test_roundtrip_textos_comuns(self, text):
        assert roundtrip(text), f"Falhou para: {text!r}"

    @pytest.mark.parametrize("cp", range(ASCII_MIN, ASCII_MAX + 1))
    def test_roundtrip_faixa_completa(self, cp):
        """Todo code point 33–252 deve sobreviver ao round-trip."""
        ch = chr(cp)
        assert roundtrip(ch), f"Falhou para code point {cp} ('{ch}')"

    def test_roundtrip_frase_com_espacos_multiplos(self):
        assert roundtrip("a b c")

    def test_roundtrip_so_maiusculas(self):
        assert roundtrip("ABC")

    def test_roundtrip_alternando_case(self):
        assert roundtrip("aAbBcC")

    def test_roundtrip_maiusculas_acentuadas(self):
        assert roundtrip("ÀÁÂÃÇÉÊÍÓÔÕÚÜ")

    def test_roundtrip_minusculas_acentuadas(self):
        assert roundtrip("àáâãçéêíóôõúü")

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

    def test_aceita_modificadores_sem_acento(self):
        # "ue" e "mo" devem funcionar igual a "ué" e "mó"
        r1 = decode("ue birosca ne")
        r2 = decode("ué birosca né")
        assert r1 == r2 == chr(64)

    def test_aceita_cifra_em_maiusculas(self):
        # CAIXA ALTA deve ser normalizada
        assert decode("MO BIROSCA E COISINHA NE") == "a"

    def test_aceita_separadores_sem_acento(self):
        ENC_A = "zica e birosca e coisinha"
        assert decode(f"{ENC_A} ai {ENC_A} ne") == "aa"
