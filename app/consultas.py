"""Consultas reutilizadas por várias telas."""
from datetime import datetime

from sqlalchemy import and_, or_

from app.models import STATUS_CONFIRMADO, Agendamento


def contar_agendamentos_futuros(**filtros) -> int:
    """Conta agendamentos Confirmados que ainda não aconteceram.

    Ex.: contar_agendamentos_futuros(servico_id=3)
    Usada nas regras RN14 / SE10 (não excluir com agendamentos futuros).
    """
    agora = datetime.now()
    consulta = Agendamento.query.filter_by(status=STATUS_CONFIRMADO, **filtros)
    consulta = consulta.filter(
        or_(
            Agendamento.data > agora.date(),
            and_(Agendamento.data == agora.date(),
                 Agendamento.hora_inicio >= agora.time()),
        )
    )
    return consulta.count()
