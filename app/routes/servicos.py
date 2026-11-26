"""T09 Serviços (RF02) - só o administrador (RN10)."""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError

from app.consultas import contar_agendamentos_futuros
from app.extensions import db
from app.forms import MSG_NOME_SERVICO_USADO, ServicoForm
from app.models import TIPO_ADMIN, Agendamento, Servico
from app.routes.decoradores import perfil_exigido
from app.utils import formatar_preco, parse_duracao, parse_preco

bp = Blueprint("servicos", __name__, url_prefix="/admin/servicos")


@bp.route("/")
@perfil_exigido(TIPO_ADMIN)
def lista():
    servicos = Servico.query.order_by(Servico.nome).all()
    return render_template("servicos/lista.html", servicos=servicos)


@bp.route("/novo", methods=["GET", "POST"])
@perfil_exigido(TIPO_ADMIN)
def novo():
    form = ServicoForm()
    if form.validate_on_submit():
        servico = Servico(
            nome=form.nome.data,
            duracao_minutos=parse_duracao(form.duracao_minutos.data),
            preco=parse_preco(form.preco.data),
        )
        db.session.add(servico)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            form.nome.errors.append(MSG_NOME_SERVICO_USADO)
        else:
            flash("Serviço cadastrado.", "success")
            return redirect(url_for("servicos.lista"))
    return render_template("servicos/form.html", form=form, titulo="Novo serviço")


@bp.route("/<int:servico_id>/editar", methods=["GET", "POST"])
@perfil_exigido(TIPO_ADMIN)
def editar(servico_id):
    servico = db.get_or_404(Servico, servico_id)
    form = ServicoForm(servico_id=servico.id)
    if request.method == "GET":
        form.nome.data = servico.nome
        form.duracao_minutos.data = str(servico.duracao_minutos)
        form.preco.data = formatar_preco(servico.preco)
    if form.validate_on_submit():
        servico.nome = form.nome.data
        servico.duracao_minutos = parse_duracao(form.duracao_minutos.data)
        servico.preco = parse_preco(form.preco.data)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            form.nome.errors.append(MSG_NOME_SERVICO_USADO)
        else:
            flash("Serviço atualizado.", "success")
            return redirect(url_for("servicos.lista"))
    return render_template("servicos/form.html", form=form, titulo="Editar serviço")


@bp.route("/<int:servico_id>/alternar", methods=["POST"])
@perfil_exigido(TIPO_ADMIN)
def alternar(servico_id):
    """Ativa ou desativa (desativar não apaga: o histórico continua)."""
    servico = db.get_or_404(Servico, servico_id)
    servico.ativo = not servico.ativo
    db.session.commit()
    flash("Serviço ativado." if servico.ativo else "Serviço desativado.", "success")
    return redirect(url_for("servicos.lista"))


@bp.route("/<int:servico_id>/excluir", methods=["POST"])
@perfil_exigido(TIPO_ADMIN)
def excluir(servico_id):
    servico = db.get_or_404(Servico, servico_id)
    if contar_agendamentos_futuros(servico_id=servico.id):
        flash("Não é possível excluir: há agendamentos futuros", "danger")   # SE10
    elif Agendamento.query.filter_by(servico_id=servico.id).first():
        flash("Não é possível excluir: o serviço tem histórico de agendamentos. "
              "Desative-o.", "danger")
    else:
        db.session.delete(servico)
        db.session.commit()
        flash("Serviço excluído.", "success")
    return redirect(url_for("servicos.lista"))
