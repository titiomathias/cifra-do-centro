import pytest
import sys, os

sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def post_encode(text: str):
    return client.post("/encode", json={"text": text})

def post_decode(text: str):
    return client.post("/decode", json={"text": text})


# ─────────────────────────────────────────────────────────────────────────────
# 1. Health check
# ─────────────────────────────────────────────────────────────────────────────

class TestHealth:

    def test_status_200(self):
        r = client.get("/health")
        assert r.status_code == 200

    def test_corpo_correto(self):
        r = client.get("/health")
        assert r.json() == {"status": "ok"}

    def test_content_type_json(self):
        r = client.get("/health")
        assert "application/json" in r.headers["content-type"]


# ─────────────────────────────────────────────────────────────────────────────
# 2. POST /encode — respostas de sucesso
# ─────────────────────────────────────────────────────────────────────────────

class TestEncodeSuccess:

    def test_status_200(self):
        assert post_encode("oi").status_code == 200

    def test_retorna_campo_result(self):
        data = post_encode("oi").json()
        assert "result" in data

    def test_result_e_string(self):
        data = post_encode("oi").json()
        assert isinstance(data["result"], str)

    def test_cifra_termina_com_ne(self):
        data = post_encode("oi").json()
        assert data["result"].strip().endswith("né")

    def test_maiuscula_gera_vixe(self):
        data = post_encode("A").json()
        assert data["result"].startswith("vixe")

    def test_espaco_gera_dai(self):
        data = post_encode("a b").json()
        assert "daí" in data["result"]

    @pytest.mark.parametrize("text", ["a", "Z", "Oi!", "hello world", "1234"])
    def test_roundtrip_via_api(self, text):
        """Encode seguido de decode via API deve retornar o original."""
        cifra = post_encode(text).json()["result"]
        original = post_decode(cifra).json()["result"]
        assert original == text


# ─────────────────────────────────────────────────────────────────────────────
# 3. POST /encode — erros esperados
# ─────────────────────────────────────────────────────────────────────────────

class TestEncodeErrors:

    def test_texto_vazio_retorna_422(self):
        assert post_encode("").status_code == 422

    def test_texto_vazio_tem_detail(self):
        data = post_encode("").json()
        assert "detail" in data

    def test_char_invalido_retorna_422(self):
        assert post_encode("ç").status_code == 422

    def test_char_invalido_menciona_faixa(self):
        data = post_encode("ç").json()
        assert "faixa" in data["detail"]

    def test_body_sem_campo_text_retorna_422(self):
        r = client.post("/encode", json={})
        assert r.status_code == 422

    def test_body_nao_json_retorna_422(self):
        r = client.post("/encode", content="texto puro", headers={"Content-Type": "text/plain"})
        assert r.status_code == 422

    def test_field_text_nulo_retorna_422(self):
        r = client.post("/encode", json={"text": None})
        assert r.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# 4. POST /decode — respostas de sucesso
# ─────────────────────────────────────────────────────────────────────────────

class TestDecodeSuccess:

    # cifra válida para "oi" gerada pelo encoder
    CIFRA_OI = "triplo birosca e troço e coisa aí triplo birosca e negócio e coisa né"

    def test_status_200(self):
        assert post_decode(self.CIFRA_OI).status_code == 200

    def test_retorna_campo_result(self):
        data = post_decode(self.CIFRA_OI).json()
        assert "result" in data

    def test_decodifica_corretamente(self):
        data = post_decode(self.CIFRA_OI).json()
        assert data["result"] == "oi"

    def test_aceita_cifra_sem_acento(self):
        # separadores sem acento devem ser tolerados
        cifra = "triplo birosca e coisinha ne"
        data = post_decode(cifra).json()
        assert data["result"] == "a"

    def test_aceita_cifra_em_maiusculas(self):
        cifra = "TRIPLO BIROSCA E COISINHA NE"
        data = post_decode(cifra).json()
        assert data["result"] == "a"

    def test_vixe_decodifica_maiuscula(self):
        cifra = "vixe triplo birosca e coisinha né"
        data = post_decode(cifra).json()
        assert data["result"] == "A"


# ─────────────────────────────────────────────────────────────────────────────
# 5. POST /decode — erros esperados
# ─────────────────────────────────────────────────────────────────────────────

class TestDecodeErrors:

    def test_texto_vazio_retorna_422(self):
        assert post_decode("").status_code == 422

    def test_texto_vazio_tem_detail(self):
        data = post_decode("").json()
        assert "detail" in data

    def test_body_sem_campo_text_retorna_422(self):
        r = client.post("/decode", json={})
        assert r.status_code == 422

    def test_token_invalido_retorna_422(self):
        assert post_decode("palavrainventada né").status_code == 422

    def test_modificador_sem_valor_retorna_422(self):
        assert post_decode("dobro né").status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# 6. Contrato do schema de resposta
# ─────────────────────────────────────────────────────────────────────────────

class TestSchema:

    def test_encode_nao_retorna_campos_extras(self):
        data = post_encode("oi").json()
        assert set(data.keys()) == {"result"}

    def test_decode_nao_retorna_campos_extras(self):
        cifra = post_encode("oi").json()["result"]
        data = post_decode(cifra).json()
        assert set(data.keys()) == {"result"}

    def test_erro_retorna_campo_detail(self):
        data = post_encode("").json()
        assert "detail" in data

    def test_metodo_get_em_encode_retorna_405(self):
        r = client.get("/encode")
        assert r.status_code == 405

    def test_metodo_get_em_decode_retorna_405(self):
        r = client.get("/decode")
        assert r.status_code == 405