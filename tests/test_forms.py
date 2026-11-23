"""Testes das validações de telefone e e-mail (sem banco)."""
from app.forms import REGEX_EMAIL, limpar_telefone, telefone_valido


def test_limpar_telefone_deixa_so_numeros():
    assert limpar_telefone("(49) 98869-6644") == "49988696644"
    assert limpar_telefone(None) == ""


def test_telefone_com_ddd_valido():
    assert telefone_valido("(49) 98869-6644")   # celular, 11 dígitos
    assert telefone_valido("4933221100")        # fixo, 10 dígitos


def test_telefone_sem_ddd_ou_curto_e_invalido():
    assert not telefone_valido("988696644")     # sem DDD
    assert not telefone_valido("123")
    assert not telefone_valido("")


def test_email_formato_valido_e_invalido():
    assert REGEX_EMAIL.match("leo@gmail.com")
    assert not REGEX_EMAIL.match("leo@gmail")
    assert not REGEX_EMAIL.match("leo gmail.com")
    assert not REGEX_EMAIL.match("@gmail.com")
