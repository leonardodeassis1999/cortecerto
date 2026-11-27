"""Telas iniciais de cada perfil. O conteúdo entra nas próximas etapas."""
from flask import Blueprint, render_template
from flask_login import current_user

from app.consultas import proximo_agendamento

from app.models import TIPO_ADMIN, TIPO_BARBEIRO, TIPO_CLIENTE
from app.routes.decoradores import perfil_exigido

bp = Blueprint("paineis", __name__)


@bp.route("/inicio")
@perfil_exigido(TIPO_CLIENTE)
def inicio_cliente():              # T03
    return render_template("paineis/inicio_cliente.html",
                           proximo=proximo_agendamento(current_user.id))


@bp.route("/agenda")
@perfil_exigido(TIPO_BARBEIRO, TIPO_ADMIN)
def agenda_barbeiro():             # T08
    return render_template("paineis/agenda_barbeiro.html")


@bp.route("/admin")
@perfil_exigido(TIPO_ADMIN)
def painel_admin():                # T10
    return render_template("paineis/painel_admin.html")
