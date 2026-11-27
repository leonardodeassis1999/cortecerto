"""Regras de horários livres e de agendamento (RN01 a RN04, RN06, RN08, RN11, RN12).

As funções 'puras' (sem banco) ficam no começo, para serem fáceis de testar.
As que consultam o banco ficam no fim.
"""
from datetime import date, datetime, time, timedelta

from flask import current_app

from app.consultas import contar_agendamentos_futuros
from app.models import (STATUS_CANCELADO, Agendamento, Barbeiro, HorarioTrabalho,
                        Servico)
from app.utils import periodos_se_sobrepoem

# Mensagens de erro (SE04 a SE08 do protótipo)
MSG_ESCOLHA_OBRIGATORIA = "Preencha todos os campos"                          # SE04
MSG_SEM_HORARIOS = "Sem horários nesta data"                                  # SE05
MSG_HORARIO_INDISPONIVEL = "Este horário não está mais disponível"            # SE06
MSG_LIMITE_ATIVOS = "Você já tem {maximo} agendamentos ativos"                # SE07 (RN12)
MSG_PRAZO_EXPIRADO = ("Prazo expirado: só é possível cancelar ou remarcar "
                      "com {horas} horas de antecedência")                    # SE08 (RN06)
MSG_DATA_PASSADA = "Escolha uma data a partir de hoje"                        # VE08
MSG_DATA_LONGE = "Só é possível agendar até {dias} dias à frente"             # RN11
MSG_ESCOLHA_INVALIDA = "Serviço ou barbeiro indisponível"


def data_dentro_do_prazo(data: date, hoje: date, max_dias: int) -> str | None:
    """RN11: de hoje até 'max_dias' à frente. Devolve a mensagem de erro ou None."""
    if data < hoje:
        return MSG_DATA_PASSADA
    if data > hoje + timedelta(days=max_dias):
        return MSG_DATA_LONGE.format(dias=max_dias)
    return None


def grade_horarios(data: date, periodos, duracao_min: int, ocupados,
                   agora: datetime, passo_min: int, antecedencia_h: int):
    """Monta a grade do dia: lista de (hora de início, livre?) em ordem.

    periodos: expedientes do barbeiro naquele dia  [(inicio, fim), ...]   (RN02)
    ocupados: agendamentos já marcados no dia      [(inicio, fim), ...]   (RN01)
    Entra na grade todo horário em que o serviço INTEIRO cabe no expediente
    (RN02 e RN03). Ele é 'livre' quando:
      - não se sobrepõe a nenhum agendamento já marcado (RN01);
      - começa pelo menos 'antecedencia_h' hora(s) depois de agora (RN04).
    Os não livres aparecem em cinza na tela (como no protótipo T05).
    """
    duracao = timedelta(minutes=duracao_min)
    limite = agora + timedelta(hours=antecedencia_h)
    grade = {}
    for inicio, fim in periodos:
        atual = datetime.combine(data, inicio)
        fim_periodo = datetime.combine(data, fim)
        while atual + duracao <= fim_periodo:
            fim_slot = atual + duracao
            grade[atual.time()] = atual >= limite and not any(
                periodos_se_sobrepoem(atual.time(), fim_slot.time(), oi, of)
                for oi, of in ocupados)
            atual += timedelta(minutes=passo_min)
    return sorted(grade.items())


def horarios_livres(data, periodos, duracao_min, ocupados, agora,
                    passo_min, antecedencia_h) -> list[time]:
    """Só os horários de início livres (RF05)."""
    return [hora for hora, livre in grade_horarios(
        data, periodos, duracao_min, ocupados, agora, passo_min, antecedencia_h) if livre]


def dentro_do_prazo_de_alteracao(inicio: datetime, agora: datetime, horas: int) -> bool:
    """RN06: só dá para cancelar ou remarcar até 'horas' horas antes do horário."""
    return inicio - agora >= timedelta(hours=horas)


# ---------------------------------------------------------------- com banco

def periodos_do_dia(barbeiro_id: int, data: date):
    """Expedientes do barbeiro no dia da semana da data (0=segunda ... 6=domingo)."""
    linhas = HorarioTrabalho.query.filter_by(
        barbeiro_id=barbeiro_id, dia_semana=data.weekday()).all()
    return [(h.hora_inicio, h.hora_fim) for h in linhas]


def ocupados_do_dia(barbeiro_id: int, data: date, ignorar_id: int | None = None):
    """Agendamentos do barbeiro no dia, menos os cancelados (RN08: cancelar libera).

    'ignorar_id' serve para remarcar: o próprio agendamento não ocupa o horário novo.
    """
    consulta = Agendamento.query.filter(
        Agendamento.barbeiro_id == barbeiro_id,
        Agendamento.data == data,
        Agendamento.status != STATUS_CANCELADO,
    )
    if ignorar_id is not None:
        consulta = consulta.filter(Agendamento.id != ignorar_id)
    return [(a.hora_inicio, a.hora_fim) for a in consulta.all()]


def calcular_grade(barbeiro: Barbeiro, servico: Servico, data: date,
                   agora: datetime | None = None, ignorar_id: int | None = None):
    cfg = current_app.config
    return grade_horarios(
        data=data,
        periodos=periodos_do_dia(barbeiro.id, data),
        duracao_min=servico.duracao_minutos,
        ocupados=ocupados_do_dia(barbeiro.id, data, ignorar_id),
        agora=agora or datetime.now(),
        passo_min=cfg["DURACAO_SLOT_MINUTOS"],
        antecedencia_h=cfg["ANTECEDENCIA_MINIMA_HORAS"],
    )


def calcular_livres(barbeiro, servico, data, agora=None, ignorar_id=None) -> list[time]:
    return [hora for hora, livre in
            calcular_grade(barbeiro, servico, data, agora, ignorar_id) if livre]


def prazo_de_alteracao_ok(agendamento: Agendamento, agora: datetime | None = None) -> bool:
    return dentro_do_prazo_de_alteracao(
        agendamento.inicio, agora or datetime.now(),
        current_app.config["PRAZO_CANCELAMENTO_HORAS"])


def mensagem_prazo_expirado() -> str:
    return MSG_PRAZO_EXPIRADO.format(horas=current_app.config["PRAZO_CANCELAMENTO_HORAS"])


def validar_agendamento(cliente_id: int, servico: Servico, barbeiro: Barbeiro,
                        data: date, hora: time, agora: datetime | None = None,
                        ignorar_id: int | None = None):
    """Confere TODAS as regras antes de gravar. Devolve a mensagem de erro ou None.

    Roda de novo no servidor mesmo que a tela só mostre horários livres:
    o cliente pode ter demorado, ou alguém pode ter mexido na URL/formulário.
    Ao remarcar ('ignorar_id'), o agendamento atual não conta no limite (RN12)
    nem ocupa o horário novo (RN01).
    """
    cfg = current_app.config
    agora = agora or datetime.now()
    if not servico.ativo or not barbeiro.ativo:
        return MSG_ESCOLHA_INVALIDA
    erro_data = data_dentro_do_prazo(data, agora.date(), cfg["MAX_DIAS_A_FRENTE"])
    if erro_data:
        return erro_data
    if (ignorar_id is None and
            contar_agendamentos_futuros(cliente_id=cliente_id) >= cfg["MAX_AGENDAMENTOS_ATIVOS"]):
        return MSG_LIMITE_ATIVOS.format(maximo=cfg["MAX_AGENDAMENTOS_ATIVOS"])
    if hora not in calcular_livres(barbeiro, servico, data, agora, ignorar_id):
        return MSG_HORARIO_INDISPONIVEL
    return None
