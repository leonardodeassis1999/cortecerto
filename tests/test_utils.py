"""Testes de preço e duração (sem banco)."""
from decimal import Decimal

from app.utils import formatar_preco, parse_duracao, parse_preco


def test_parse_preco_aceita_virgula_ponto_e_real():
    assert parse_preco("35,00") == Decimal("35.00")
    assert parse_preco("35.5") == Decimal("35.50")
    assert parse_preco("R$ 40") == Decimal("40.00")


def test_parse_preco_invalido_devolve_none():
    assert parse_preco("abc") is None
    assert parse_preco("") is None
    assert parse_preco(None) is None
    assert parse_preco("NaN") is None
    assert parse_preco("1e999") is None


def test_parse_preco_deixa_passar_zero_e_negativo_para_o_formulario_recusar():
    assert parse_preco("0") == Decimal("0.00")
    assert parse_preco("-5") == Decimal("-5.00")


def test_parse_duracao():
    assert parse_duracao("30") == 30
    assert parse_duracao(" 60 ") == 60
    assert parse_duracao("0") == 0
    assert parse_duracao("-10") == -10
    assert parse_duracao("3,5") is None
    assert parse_duracao("") is None
    assert parse_duracao(None) is None


def test_formatar_preco_no_padrao_brasileiro():
    assert formatar_preco(Decimal("35")) == "35,00"
    assert formatar_preco(Decimal("55.5")) == "55,50"
    assert formatar_preco(None) == ""


def test_parse_hora():
    from datetime import time
    from app.utils import parse_hora
    assert parse_hora("08:00") == time(8, 0)
    assert parse_hora("8:30") == time(8, 30)
    assert parse_hora(" 18:00:00 ") == time(18, 0)
    assert parse_hora("25:00") is None
    assert parse_hora("abc") is None
    assert parse_hora("") is None
    assert parse_hora(None) is None


def test_periodos_se_sobrepoem():
    from datetime import time
    from app.utils import periodos_se_sobrepoem
    t = time
    assert periodos_se_sobrepoem(t(8), t(12), t(10), t(14))        # cruzam
    assert periodos_se_sobrepoem(t(8), t(18), t(10), t(11))        # um dentro do outro
    assert not periodos_se_sobrepoem(t(8), t(12), t(12), t(18))    # só encostam
    assert not periodos_se_sobrepoem(t(8), t(12), t(14), t(18))    # separados
