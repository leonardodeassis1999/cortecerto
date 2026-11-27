"""Testes do fluxo do cliente: T03, T04, T05, T06 e T07 (SQLite em memória)."""
from datetime import date, datetime, time, timedelta

import pytest
from flask import g

from app import create_app
from app.extensions import db
from app.models import (TIPO_BARBEIRO, TIPO_CLIENTE, Agendamento, Barbeiro,
                        HorarioTrabalho, Servico, Usuario)
from config import Config


class ConfigTeste(Config):
    TESTING = True
    SECRET_KEY = "chave-de-teste"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    WTF_CSRF_ENABLED = False


def proxima_segunda():
    hoje = date.today()
    return hoje + timedelta(days=(7 - hoje.weekday()) % 7 or 7)


def _usuario(nome, email, tipo=TIPO_CLIENTE):
    u = Usuario(nome=nome, email=email, telefone="49988887777", tipo=tipo)
    u.definir_senha("123456")
    return u


@pytest.fixture()
def app():
    app = create_app(ConfigTeste)

    @app.before_request
    def _isolar_requisicoes():
        # No teste o contexto fica aberto o tempo todo; sem isto o usuário logado
        # de uma requisição vazaria para a seguinte (não acontece no servidor real).
        g.pop("_login_user", None)

    with app.app_context():
        db.create_all()
        barbeiro = Barbeiro(usuario=_usuario("Alex", "alex@teste.com", TIPO_BARBEIRO))
        barbeiro.horarios = [
            HorarioTrabalho(dia_semana=0, hora_inicio=time(8), hora_fim=time(12)),
            HorarioTrabalho(dia_semana=0, hora_inicio=time(14), hora_fim=time(18)),
        ]
        db.session.add_all([
            barbeiro,
            _usuario("Ana", "ana@teste.com"),
            _usuario("Bia", "bia@teste.com"),
            Servico(nome="Corte", duracao_minutos=30, preco=35),
            Servico(nome="Corte + Barba", duracao_minutos=60, preco=55),
            Servico(nome="Antigo", duracao_minutos=30, preco=10, ativo=False),
        ])
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


def entrar(app, email):
    c = app.test_client()
    c.post("/login", data={"email": email, "senha": "123456"})
    return c


def _ids(servico="Corte"):
    return (Servico.query.filter_by(nome=servico).first().id, Barbeiro.query.first().id)


def reservar(c, hora, servico="Corte", data=None, remarcar=None):
    s, b = _ids(servico)
    dados = {"servico": s, "barbeiro": b,
             "data": (data or proxima_segunda()).isoformat(), "hora": hora}
    if remarcar:
        dados["remarcar"] = remarcar
    return c.post("/agendar/confirmar", data=dados, follow_redirects=True)


def texto(r):
    return r.get_data(as_text=True)


# ------------------------------------------------------------ acesso e T04

def test_barbeiro_nao_acessa_agendamento(app):
    assert entrar(app, "alex@teste.com").get("/agendar/").status_code == 302   # SE09


def test_t04_lista_servicos_ativos_e_barbeiros(app):
    html = texto(entrar(app, "ana@teste.com").get("/agendar/"))
    assert "Corte + Barba" in html and "Alex" in html
    assert "Antigo" not in html                      # serviço inativo não aparece


def test_t05_sem_escolher_servico_e_barbeiro_volta_ao_t04_se04(app):
    r = entrar(app, "ana@teste.com").get("/agendar/data", follow_redirects=True)
    assert "Preencha todos os campos" in texto(r)


# ------------------------------------------------------------ T05 e T06

def test_t05_mostra_livres_e_ocupados_em_cinza(app):
    c = entrar(app, "ana@teste.com")
    reservar(c, "09:00")
    s, b = _ids()
    html = texto(c.get(f"/agendar/data?servico={s}&barbeiro={b}&data={proxima_segunda().isoformat()}"))
    assert 'value="08:00"' in html and "disabled" not in html.split('value="08:00"')[1][:20]
    assert "disabled" in html.split('value="09:00"')[1][:20]          # ocupado
    assert 'value="12:00"' not in html                                  # almoço


def test_t05_dia_sem_expediente_mostra_se05(app):
    s, b = _ids()
    terca = (proxima_segunda() + timedelta(days=1)).isoformat()
    html = texto(entrar(app, "ana@teste.com").get(f"/agendar/data?servico={s}&barbeiro={b}&data={terca}"))
    assert "Sem horários nesta data" in html


def test_t05_data_alem_de_30_dias_rn11(app):
    s, b = _ids()
    longe = (date.today() + timedelta(days=31)).isoformat()
    html = texto(entrar(app, "ana@teste.com").get(f"/agendar/data?servico={s}&barbeiro={b}&data={longe}"))
    assert "até 30 dias" in html and 'name="hora"' not in html


def test_t06_mostra_resumo_com_duracao_e_preco(app):
    s, b = _ids("Corte + Barba")
    d = proxima_segunda().isoformat()
    html = texto(entrar(app, "ana@teste.com").get(
        f"/agendar/confirmacao?servico={s}&barbeiro={b}&data={d}&hora=14:00"))
    assert "14:00 às 15:00" in html and "60 minutos" in html and "55,00" in html
    assert "(segunda)" in html


def test_t06_sem_horario_volta_ao_t05(app):
    s, b = _ids()
    r = entrar(app, "ana@teste.com").get(
        f"/agendar/confirmacao?servico={s}&barbeiro={b}&data={proxima_segunda().isoformat()}",
        follow_redirects=True)
    assert "Preencha todos os campos" in texto(r)


# ------------------------------------------------------------ confirmar (RN01 a RN04, RN11, RN12)

def test_confirma_agendamento_e_vai_para_t07_rn03(app):
    r = reservar(entrar(app, "ana@teste.com"), "09:00", servico="Corte + Barba")
    html = texto(r)
    assert "Agendamento confirmado!" in html and "T07 Meus agendamentos" in html
    a = Agendamento.query.one()
    assert a.hora_inicio == time(9, 0) and a.hora_fim == time(10, 0)
    assert a.status == "Confirmado" and a.cliente.email == "ana@teste.com"


def test_dois_clientes_no_mesmo_horario_rn01_se06(app):
    reservar(entrar(app, "ana@teste.com"), "09:00")
    r = reservar(entrar(app, "bia@teste.com"), "09:00")
    assert "Este horário não está mais disponível" in texto(r)
    assert Agendamento.query.count() == 1


def test_sobreposicao_parcial_e_bloqueada(app):
    reservar(entrar(app, "ana@teste.com"), "09:00", servico="Corte + Barba")   # 09-10
    r = reservar(entrar(app, "bia@teste.com"), "09:30")
    assert "não está mais disponível" in texto(r)
    assert Agendamento.query.count() == 1


def test_fora_do_expediente_e_dia_sem_expediente_rn02(app):
    c = entrar(app, "ana@teste.com")
    assert "não está mais disponível" in texto(reservar(c, "12:30"))
    terca = proxima_segunda() + timedelta(days=1)
    assert "não está mais disponível" in texto(reservar(c, "09:00", data=terca))
    assert Agendamento.query.count() == 0


def test_limite_de_3_agendamentos_ativos_rn12_se07(app):
    c = entrar(app, "ana@teste.com")
    for hora in ("08:00", "09:00", "10:00"):
        reservar(c, hora)
    r = reservar(c, "11:00")
    assert "Você já tem 3 agendamentos ativos" in texto(r)
    assert Agendamento.query.count() == 3


def test_data_passada_e_mais_de_30_dias_recusadas(app):
    c = entrar(app, "ana@teste.com")
    assert "a partir de hoje" in texto(reservar(c, "09:00", data=date.today() - timedelta(days=1)))
    assert "até 30 dias" in texto(reservar(c, "09:00", data=date.today() + timedelta(days=31)))
    assert Agendamento.query.count() == 0


def test_servico_e_barbeiro_inativos_sao_recusados(app):
    c = entrar(app, "ana@teste.com")
    assert "indisponível" in texto(reservar(c, "09:00", servico="Antigo"))
    Barbeiro.query.first().ativo = False
    db.session.commit()
    assert "indisponível" in texto(reservar(c, "09:00"))
    assert Agendamento.query.count() == 0


def test_dados_invalidos_nao_quebram_o_sistema(app):
    r = entrar(app, "ana@teste.com").post("/agendar/confirmar",
                                          data={"servico": "x", "hora": "abc"}, follow_redirects=True)
    assert r.status_code == 200 and "Preencha todos os campos" in texto(r)


# ------------------------------------------------------------ T07: cancelar (RN06, RN08)

def _criar_direto(email, dt, status="Confirmado", servico="Corte"):
    """Cria um agendamento no banco sem passar pelas regras (para testar prazos)."""
    cliente = Usuario.query.filter_by(email=email).first()
    s, b = _ids(servico)
    dur = db.session.get(Servico, s).duracao_minutos
    a = Agendamento(cliente_id=cliente.id, barbeiro_id=b, servico_id=s, data=dt.date(),
                    hora_inicio=dt.time().replace(second=0, microsecond=0),
                    hora_fim=(dt + timedelta(minutes=dur)).time().replace(second=0, microsecond=0),
                    status=status)
    db.session.add(a)
    db.session.commit()
    return a


def test_cancelar_libera_o_horario_rn08(app):
    c = entrar(app, "ana@teste.com")
    reservar(c, "09:00")
    a = Agendamento.query.one()
    r = c.post(f"/meus-agendamentos/{a.id}/cancelar", follow_redirects=True)
    assert "O horário voltou a ficar livre" in texto(r)
    db.session.refresh(a)
    assert a.status == "Cancelado"
    # outro cliente já consegue o mesmo horário
    assert "Agendamento confirmado!" in texto(reservar(entrar(app, "bia@teste.com"), "09:00"))


def test_cancelar_com_menos_de_2h_e_recusado_se08(app):
    a = _criar_direto("ana@teste.com", datetime.now() + timedelta(hours=1))
    r = entrar(app, "ana@teste.com").post(f"/meus-agendamentos/{a.id}/cancelar", follow_redirects=True)
    assert "Prazo expirado" in texto(r)
    db.session.refresh(a)
    assert a.status == "Confirmado"


def test_cliente_nao_cancela_agendamento_de_outro(app):
    reservar(entrar(app, "ana@teste.com"), "09:00")
    a = Agendamento.query.one()
    r = entrar(app, "bia@teste.com").post(f"/meus-agendamentos/{a.id}/cancelar", follow_redirects=True)
    assert "Acesso negado" in texto(r)
    db.session.refresh(a)
    assert a.status == "Confirmado"


def test_nao_cancela_de_novo_nem_concluido(app):
    a = _criar_direto("ana@teste.com", datetime.now() + timedelta(days=3), status="Cancelado")
    r = entrar(app, "ana@teste.com").post(f"/meus-agendamentos/{a.id}/cancelar", follow_redirects=True)
    assert "não pode mais ser alterado" in texto(r)


# ------------------------------------------------------------ T07: remarcar

def test_remarcar_muda_o_mesmo_agendamento_e_libera_o_antigo(app):
    c = entrar(app, "ana@teste.com")
    reservar(c, "09:00")
    a = Agendamento.query.one()
    r = c.get(f"/meus-agendamentos/{a.id}/remarcar")
    assert r.status_code == 302 and f"remarcar={a.id}" in r.headers["Location"]
    assert "Agendamento remarcado!" in texto(reservar(c, "10:00", remarcar=a.id))
    assert Agendamento.query.count() == 1
    db.session.refresh(a)
    assert a.hora_inicio == time(10, 0) and a.hora_fim == time(10, 30)
    assert "Agendamento confirmado!" in texto(reservar(entrar(app, "bia@teste.com"), "09:00"))


def test_remarcar_para_horario_que_sobrepoe_o_proprio(app):
    c = entrar(app, "ana@teste.com")
    reservar(c, "09:00", servico="Corte + Barba")                      # 09-10
    a = Agendamento.query.one()
    assert "Agendamento remarcado!" in texto(reservar(c, "09:30", servico="Corte + Barba", remarcar=a.id))


def test_remarcar_com_3_ativos_e_permitido(app):
    c = entrar(app, "ana@teste.com")
    for hora in ("08:00", "09:00", "10:00"):
        reservar(c, hora)
    a = Agendamento.query.first()
    assert "Agendamento remarcado!" in texto(reservar(c, "11:00", remarcar=a.id))
    assert Agendamento.query.count() == 3


def test_remarcar_com_menos_de_2h_e_recusado_se08(app):
    a = _criar_direto("ana@teste.com", datetime.now() + timedelta(hours=1))
    r = entrar(app, "ana@teste.com").get(f"/meus-agendamentos/{a.id}/remarcar", follow_redirects=True)
    assert "Prazo expirado" in texto(r)


# ------------------------------------------------------------ T03 e T07 (listas)

def test_t03_mostra_o_proximo_agendamento(app):
    c = entrar(app, "ana@teste.com")
    assert "Próximo agendamento" not in texto(c.get("/inicio"))
    reservar(c, "14:00", servico="Corte + Barba")
    html = texto(c.get("/inicio"))
    assert "Próximo agendamento" in html and "Corte + Barba" in html and "14:00" in html


def test_t07_lista_com_status_e_botoes_so_nos_confirmados(app):
    _criar_direto("ana@teste.com", datetime.now() + timedelta(days=5), "Confirmado")
    _criar_direto("ana@teste.com", datetime.now() - timedelta(days=5), "Concluído")
    _criar_direto("ana@teste.com", datetime.now() + timedelta(days=9), "Cancelado")
    html = texto(entrar(app, "ana@teste.com").get("/meus-agendamentos/"))
    assert "Confirmado" in html and "Concluído" in html and "Cancelado" in html
    assert html.count("Remarcar") == 1                  # só o Confirmado futuro


def test_cliente_so_ve_os_proprios_agendamentos(app):
    reservar(entrar(app, "ana@teste.com"), "09:00")
    assert "Você ainda não tem agendamentos" in texto(entrar(app, "bia@teste.com").get("/meus-agendamentos/"))
