"""Testes das regras de horários livres (sem banco)."""
from datetime import date, datetime, time

from app.agenda import (MSG_DATA_LONGE, MSG_DATA_PASSADA, data_dentro_do_prazo,
                        horarios_livres)

DIA = date(2026, 12, 7)                      # uma segunda-feira
MANHA_TARDE = [(time(8), time(12)), (time(14), time(18))]
MUITO_ANTES = datetime(2026, 12, 1, 9, 0)    # "agora" bem antes do dia


def livres(duracao=30, ocupados=(), agora=MUITO_ANTES, periodos=MANHA_TARDE):
    return horarios_livres(DIA, periodos, duracao, list(ocupados), agora,
                           passo_min=30, antecedencia_h=1)


def test_servico_de_30_min_gera_horarios_de_meia_em_meia_hora():
    h = livres(30)
    assert h[0] == time(8, 0) and time(11, 30) in h
    assert time(12, 0) not in h and time(13, 30) not in h     # almoço (RN02)
    assert h[-1] == time(17, 30)


def test_servico_precisa_caber_no_expediente_rn03():
    h = livres(60)
    assert time(11, 0) in h
    assert time(11, 30) not in h          # terminaria 12:30, depois do expediente
    assert h[-1] == time(17, 0)


def test_horario_ocupado_nao_aparece_rn01():
    h = livres(30, ocupados=[(time(9), time(9, 30))])
    assert time(9, 0) not in h
    assert time(8, 30) in h and time(9, 30) in h


def test_agendamento_longo_bloqueia_os_horarios_que_se_sobrepoem():
    h = livres(30, ocupados=[(time(9), time(10))])      # 60 min ocupados
    assert time(9, 0) not in h and time(9, 30) not in h
    assert time(10, 0) in h


def test_servico_longo_nao_pode_invadir_horario_ocupado():
    h = livres(60, ocupados=[(time(9), time(9, 30))])
    assert time(8, 30) not in h           # 08:30-09:30 bateria no das 09:00
    assert time(8, 0) in h                # 08:00-09:00 só encosta, pode
    assert time(9, 30) in h


def test_antecedencia_minima_de_1_hora_rn04():
    agora = datetime.combine(DIA, time(9, 10))
    h = livres(30, agora=agora)
    assert time(10, 0) not in h           # 10:00 < 10:10
    assert time(10, 30) in h


def test_dia_sem_expediente_nao_tem_horarios():
    assert livres(30, periodos=[]) == []


def test_prazo_rn11():
    hoje = date(2026, 11, 26)
    assert data_dentro_do_prazo(hoje, hoje, 30) is None
    assert data_dentro_do_prazo(date(2026, 12, 26), hoje, 30) is None   # exatamente 30 dias
    assert data_dentro_do_prazo(date(2026, 12, 27), hoje, 30) == MSG_DATA_LONGE.format(dias=30)
    assert data_dentro_do_prazo(date(2026, 11, 25), hoje, 30) == MSG_DATA_PASSADA


def test_grade_mostra_ocupados_como_nao_livres():
    from app.agenda import grade_horarios
    grade = dict(grade_horarios(DIA, MANHA_TARDE, 30, [(time(9), time(9, 30))],
                                MUITO_ANTES, 30, 1))
    assert grade[time(9, 0)] is False        # ocupado: aparece em cinza
    assert grade[time(8, 30)] is True
    assert time(12, 0) not in grade          # fora do expediente nem entra na grade


def test_prazo_de_cancelamento_rn06():
    from app.agenda import dentro_do_prazo_de_alteracao
    agora = datetime(2026, 12, 7, 10, 0)
    assert dentro_do_prazo_de_alteracao(datetime(2026, 12, 7, 12, 0), agora, 2)      # exatamente 2h
    assert not dentro_do_prazo_de_alteracao(datetime(2026, 12, 7, 11, 59), agora, 2)
    assert dentro_do_prazo_de_alteracao(datetime(2026, 12, 8, 9, 0), agora, 2)
