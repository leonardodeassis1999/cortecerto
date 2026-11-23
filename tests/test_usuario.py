"""Testes que não precisam de banco: senha com hash e bloqueio de login (RN13)."""
from datetime import datetime, timedelta

from app.models import Usuario


def test_senha_fica_guardada_como_hash():
    u = Usuario()
    u.definir_senha("segredo123")
    assert u.senha_hash != "segredo123"
    assert u.conferir_senha("segredo123")
    assert not u.conferir_senha("errada")


def test_usuario_sem_bloqueio_nao_esta_bloqueado():
    assert not Usuario().esta_bloqueado()


def test_bloqueio_no_futuro_bloqueia_e_no_passado_libera():
    u = Usuario()
    agora = datetime(2026, 11, 23, 10, 0)
    u.bloqueado_ate = agora + timedelta(minutes=15)
    assert u.esta_bloqueado(agora)
    assert not u.esta_bloqueado(agora + timedelta(minutes=16))


def test_quatro_erros_nao_bloqueiam_e_o_quinto_bloqueia_por_15_minutos():
    u = Usuario()
    agora = datetime(2026, 11, 23, 10, 0)
    for _ in range(4):
        assert u.registrar_falha_login(5, 15, agora) is False
    assert not u.esta_bloqueado(agora)
    assert u.registrar_falha_login(5, 15, agora) is True
    assert u.esta_bloqueado(agora + timedelta(minutes=14))
    assert not u.esta_bloqueado(agora + timedelta(minutes=16))


def test_login_correto_zera_tentativas_e_bloqueio():
    u = Usuario()
    u.tentativas_login = 3
    u.bloqueado_ate = datetime(2030, 1, 1)
    u.registrar_login_ok()
    assert u.tentativas_login == 0
    assert u.bloqueado_ate is None
