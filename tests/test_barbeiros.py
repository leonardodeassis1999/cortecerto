"""Testes da T11 (barbeiros e horários) com banco SQLite em memória."""
from datetime import date, time, timedelta

import pytest

from app import create_app
from app.extensions import db
from app.models import (TIPO_ADMIN, TIPO_CLIENTE, Agendamento, Barbeiro,
                        HorarioTrabalho, Servico, Usuario)
from config import Config


class ConfigTeste(Config):
    TESTING = True
    SECRET_KEY = "chave-de-teste"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    WTF_CSRF_ENABLED = False


@pytest.fixture()
def app():
    app = create_app(ConfigTeste)
    with app.app_context():
        db.create_all()
        admin = Usuario(nome="Admin", email="admin@teste.com",
                        telefone="49999990000", tipo=TIPO_ADMIN)
        admin.definir_senha("123456")
        db.session.add(admin)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def admin(app):
    c = app.test_client()
    c.post("/login", data={"email": "admin@teste.com", "senha": "123456"})
    return c


DADOS = {"nome": "João Silva", "email": "joao@teste.com",
         "telefone": "(49) 98888-7777", "senha": "123456", "especialidade": "Degradê"}


def criar_barbeiro(admin, **extra):
    admin.post("/admin/barbeiros/novo", data={**DADOS, **extra})
    return Barbeiro.query.join(Usuario).filter(Usuario.email == DADOS["email"]).first()


def test_cliente_nao_acessa_barbeiros(app):
    cliente = Usuario(nome="Ana", email="ana@teste.com", telefone="49988887777",
                      tipo=TIPO_CLIENTE)
    cliente.definir_senha("123456")
    db.session.add(cliente)
    db.session.commit()
    c = app.test_client()
    c.post("/login", data={"email": "ana@teste.com", "senha": "123456"})
    r = c.get("/admin/barbeiros/")
    assert r.status_code == 302                     # SE09: acesso negado


def test_sem_login_vai_para_o_login(app):
    r = app.test_client().get("/admin/barbeiros/")
    assert r.status_code == 302 and "/login" in r.headers["Location"]


def test_cadastra_barbeiro_com_senha_em_hash(admin):
    b = criar_barbeiro(admin)
    assert b is not None
    assert b.usuario.tipo == "barbeiro"
    assert b.usuario.telefone == "49988887777"        # só números
    assert b.usuario.senha_hash != "123456"
    assert b.usuario.conferir_senha("123456")


def test_campos_obrigatorios(admin):
    r = admin.post("/admin/barbeiros/novo", data={})
    assert "Preencha todos os campos" in r.get_data(as_text=True)
    assert Barbeiro.query.count() == 0


def test_email_repetido_e_recusado(admin):
    criar_barbeiro(admin)
    r = admin.post("/admin/barbeiros/novo", data={**DADOS, "nome": "Outro"})
    assert "Este e-mail já está em uso" in r.get_data(as_text=True)
    assert Barbeiro.query.count() == 1


def test_edicao_sem_senha_mantem_a_senha(admin):
    b = criar_barbeiro(admin)
    admin.post(f"/admin/barbeiros/{b.id}/editar",
               data={**DADOS, "nome": "João Novo", "senha": ""})
    db.session.refresh(b.usuario)
    assert b.usuario.nome == "João Novo"
    assert b.usuario.conferir_senha("123456")


def test_edicao_nao_acusa_email_do_proprio_barbeiro(admin):
    b = criar_barbeiro(admin)
    r = admin.post(f"/admin/barbeiros/{b.id}/editar", data={**DADOS, "senha": ""})
    assert r.status_code == 302                       # salvou e voltou para a lista


def test_alternar_ativo(admin):
    b = criar_barbeiro(admin)
    admin.post(f"/admin/barbeiros/{b.id}/alternar")
    db.session.refresh(b)
    assert b.ativo is False


def test_horario_valido_e_fim_antes_do_inicio(admin):
    b = criar_barbeiro(admin)
    admin.post(f"/admin/barbeiros/{b.id}/horarios",
               data={"dia_semana": 0, "hora_inicio": "08:00", "hora_fim": "12:00"})
    assert HorarioTrabalho.query.count() == 1
    r = admin.post(f"/admin/barbeiros/{b.id}/horarios",
                   data={"dia_semana": 1, "hora_inicio": "18:00", "hora_fim": "08:00"})
    assert "O fim deve ser depois do início" in r.get_data(as_text=True)
    assert HorarioTrabalho.query.count() == 1


def test_horario_sobreposto_no_mesmo_dia_e_recusado(admin):
    b = criar_barbeiro(admin)
    admin.post(f"/admin/barbeiros/{b.id}/horarios",
               data={"dia_semana": 0, "hora_inicio": "08:00", "hora_fim": "12:00"})
    r = admin.post(f"/admin/barbeiros/{b.id}/horarios",
                   data={"dia_semana": 0, "hora_inicio": "11:00", "hora_fim": "15:00"})
    assert "se sobrepõe" in r.get_data(as_text=True)
    # outro dia, ou período que só encosta, é permitido
    admin.post(f"/admin/barbeiros/{b.id}/horarios",
               data={"dia_semana": 1, "hora_inicio": "11:00", "hora_fim": "15:00"})
    admin.post(f"/admin/barbeiros/{b.id}/horarios",
               data={"dia_semana": 0, "hora_inicio": "12:00", "hora_fim": "18:00"})
    assert HorarioTrabalho.query.count() == 3


def test_remove_horario(admin):
    b = criar_barbeiro(admin)
    admin.post(f"/admin/barbeiros/{b.id}/horarios",
               data={"dia_semana": 0, "hora_inicio": "08:00", "hora_fim": "12:00"})
    h = HorarioTrabalho.query.first()
    admin.post(f"/admin/barbeiros/{b.id}/horarios/{h.id}/excluir")
    assert HorarioTrabalho.query.count() == 0


def _agendar(barbeiro, dias):
    cliente = Usuario(nome="Ana", email="ana@teste.com", telefone="49988887777")
    cliente.definir_senha("123456")
    servico = Servico(nome="Corte", duracao_minutos=30, preco=35)
    db.session.add_all([cliente, servico])
    db.session.flush()
    db.session.add(Agendamento(
        cliente_id=cliente.id, barbeiro_id=barbeiro.id, servico_id=servico.id,
        data=date.today() + timedelta(days=dias),
        hora_inicio=time(10, 0), hora_fim=time(10, 30)))
    db.session.commit()


def test_nao_exclui_barbeiro_com_agendamento_futuro(admin):
    b = criar_barbeiro(admin)
    _agendar(b, dias=3)
    r = admin.post(f"/admin/barbeiros/{b.id}/excluir", follow_redirects=True)
    assert "há agendamentos futuros" in r.get_data(as_text=True)     # SE10
    assert db.session.get(Barbeiro, b.id) is not None


def test_nao_exclui_barbeiro_com_historico(admin):
    b = criar_barbeiro(admin)
    _agendar(b, dias=-3)
    r = admin.post(f"/admin/barbeiros/{b.id}/excluir", follow_redirects=True)
    assert "histórico" in r.get_data(as_text=True)
    assert db.session.get(Barbeiro, b.id) is not None


def test_exclui_barbeiro_sem_agendamentos_junto_com_horarios_e_usuario(admin):
    b = criar_barbeiro(admin)
    admin.post(f"/admin/barbeiros/{b.id}/horarios",
               data={"dia_semana": 0, "hora_inicio": "08:00", "hora_fim": "12:00"})
    admin.post(f"/admin/barbeiros/{b.id}/excluir")
    assert Barbeiro.query.count() == 0
    assert HorarioTrabalho.query.count() == 0
    assert Usuario.query.filter_by(email="joao@teste.com").first() is None
