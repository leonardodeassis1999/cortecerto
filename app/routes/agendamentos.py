"""T07 Meus agendamentos: ver, remarcar e cancelar (RF07 e RF08) - só o cliente."""
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user

from app.agenda import mensagem_prazo_expirado, prazo_de_alteracao_ok
from app.extensions import db
from app.models import (STATUS_CANCELADO, STATUS_CONFIRMADO, TIPO_CLIENTE,
                        Agendamento)
from app.routes.decoradores import perfil_exigido

bp = Blueprint("agendamentos", __name__, url_prefix="/meus-agendamentos")


def _meu_agendamento_confirmado(agendamento_id):
    """Devolve (agendamento, erro). Só o dono mexe, e só enquanto estiver Confirmado."""
    agendamento = db.get_or_404(Agendamento, agendamento_id)
    if agendamento.cliente_id != current_user.id:
        return None, "Acesso negado"                                        # SE09
    if agendamento.status != STATUS_CONFIRMADO:
        return None, "Este agendamento não pode mais ser alterado"
    return agendamento, None


@bp.route("/")
@perfil_exigido(TIPO_CLIENTE)
def lista():
    agendamentos = (Agendamento.query.filter_by(cliente_id=current_user.id)
                    .order_by(Agendamento.data.desc(), Agendamento.hora_inicio.desc())
                    .all())
    agora = datetime.now()
    # Só aparecem Remarcar e Cancelar para o que ainda está Confirmado e não começou
    pode_alterar = {a.id for a in agendamentos
                    if a.status == STATUS_CONFIRMADO and a.inicio > agora}
    return render_template("agendamentos/lista.html", agendamentos=agendamentos,
                           pode_alterar=pode_alterar)


@bp.route("/<int:agendamento_id>/remarcar")
@perfil_exigido(TIPO_CLIENTE)
def remarcar(agendamento_id):
    """Vai para o T05 já com serviço e barbeiro do agendamento (só data e hora mudam)."""
    agendamento, erro = _meu_agendamento_confirmado(agendamento_id)
    if not erro and not prazo_de_alteracao_ok(agendamento):
        erro = mensagem_prazo_expirado()                                    # SE08, RN06
    if erro:
        flash(erro, "danger")
        return redirect(url_for("agendamentos.lista"))
    return redirect(url_for("agendar.data_horario", servico=agendamento.servico_id,
                            barbeiro=agendamento.barbeiro_id, remarcar=agendamento.id))


@bp.route("/<int:agendamento_id>/cancelar", methods=["POST"])
@perfil_exigido(TIPO_CLIENTE)
def cancelar(agendamento_id):
    agendamento, erro = _meu_agendamento_confirmado(agendamento_id)
    if not erro and not prazo_de_alteracao_ok(agendamento):
        erro = mensagem_prazo_expirado()                                    # SE08, RN06
    if erro:
        flash(erro, "danger")
    else:
        # RN08: Cancelado não entra mais no cálculo de ocupados, então o horário volta a ficar livre
        agendamento.status = STATUS_CANCELADO
        db.session.commit()
        flash("Agendamento cancelado. O horário voltou a ficar livre.", "success")
    return redirect(url_for("agendamentos.lista"))
