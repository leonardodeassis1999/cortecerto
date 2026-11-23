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
    agora = datetime(2026, 11, 22, 10, 0)
    u.bloqueado_ate = agora + timedelta(minutes=15)
    assert u.esta_bloqueado(agora)
    assert not u.esta_bloqueado(agora + timedelta(minutes=16))
