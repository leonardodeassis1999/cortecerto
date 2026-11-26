"""T11 Barbeiros e horários de trabalho (RF03) - só o administrador (RN10)."""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError

from app.consultas import contar_agendamentos_futuros
from app.extensions import db
from app.forms import MSG_EMAIL_USADO, BarbeiroForm, HorarioForm, limpar_telefone
from app.models import (TIPO_ADMIN, TIPO_BARBEIRO, Agendamento, Barbeiro,
                        HorarioTrabalho, Usuario)
from app.routes.decoradores import perfil_exigido
from app.utils import NOMES_DIAS, parse_hora

bp = Blueprint("barbeiros", __name__, url_prefix="/admin/barbeiros")


@bp.route("/")
@perfil_exigido(TIPO_ADMIN)
def lista():
    barbeiros = (Barbeiro.query.join(Usuario)
                 .order_by(Usuario.nome).all())
    return render_template("barbeiros/lista.html", barbeiros=barbeiros)


@bp.route("/novo", methods=["GET", "POST"])
@perfil_exigido(TIPO_ADMIN)
def novo():
    form = BarbeiroForm()
    if form.validate_on_submit():
        # O barbeiro é um usuário com perfil "barbeiro" + um registro em barbeiros
        usuario = Usuario(
            nome=form.nome.data,
            email=form.email.data,
            telefone=limpar_telefone(form.telefone.data),
            tipo=TIPO_BARBEIRO,
        )
        usuario.definir_senha(form.senha.data)
        usuario.barbeiro = Barbeiro(especialidade=form.especialidade.data or None)
        db.session.add(usuario)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            form.email.errors.append(MSG_EMAIL_USADO)
        else:
            flash("Barbeiro cadastrado. Agora defina os horários de trabalho.", "success")
            return redirect(url_for("barbeiros.horarios", barbeiro_id=usuario.barbeiro.id))
    return render_template("barbeiros/form.html", form=form, titulo="Novo barbeiro")


@bp.route("/<int:barbeiro_id>/editar", methods=["GET", "POST"])
@perfil_exigido(TIPO_ADMIN)
def editar(barbeiro_id):
    barbeiro = db.get_or_404(Barbeiro, barbeiro_id)
    usuario = barbeiro.usuario
    form = BarbeiroForm(usuario_id=usuario.id)
    if request.method == "GET":
        form.nome.data = usuario.nome
        form.email.data = usuario.email
        form.telefone.data = usuario.telefone
        form.especialidade.data = barbeiro.especialidade
    if form.validate_on_submit():
        usuario.nome = form.nome.data
        usuario.email = form.email.data
        usuario.telefone = limpar_telefone(form.telefone.data)
        barbeiro.especialidade = form.especialidade.data or None
        if form.senha.data:                       # vazio = mantém a senha atual
            usuario.definir_senha(form.senha.data)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            form.email.errors.append(MSG_EMAIL_USADO)
        else:
            flash("Barbeiro atualizado.", "success")
            return redirect(url_for("barbeiros.lista"))
    return render_template("barbeiros/form.html", form=form, titulo="Editar barbeiro")


@bp.route("/<int:barbeiro_id>/alternar", methods=["POST"])
@perfil_exigido(TIPO_ADMIN)
def alternar(barbeiro_id):
    """Ativa ou desativa (desativar não apaga: o histórico continua)."""
    barbeiro = db.get_or_404(Barbeiro, barbeiro_id)
    barbeiro.ativo = not barbeiro.ativo
    db.session.commit()
    flash("Barbeiro ativado." if barbeiro.ativo else "Barbeiro desativado.", "success")
    return redirect(url_for("barbeiros.lista"))


@bp.route("/<int:barbeiro_id>/excluir", methods=["POST"])
@perfil_exigido(TIPO_ADMIN)
def excluir(barbeiro_id):
    barbeiro = db.get_or_404(Barbeiro, barbeiro_id)
    usuario = barbeiro.usuario
    if contar_agendamentos_futuros(barbeiro_id=barbeiro.id):
        flash("Não é possível excluir: há agendamentos futuros", "danger")   # SE10
    elif (Agendamento.query.filter_by(barbeiro_id=barbeiro.id).first()
          or Agendamento.query.filter_by(cliente_id=usuario.id).first()):
        flash("Não é possível excluir: o barbeiro tem histórico de agendamentos. "
              "Desative-o.", "danger")
    else:
        db.session.delete(barbeiro)    # os horários saem junto (cascade no model)
        db.session.delete(usuario)
        db.session.commit()
        flash("Barbeiro excluído.", "success")
    return redirect(url_for("barbeiros.lista"))


@bp.route("/<int:barbeiro_id>/horarios", methods=["GET", "POST"])
@perfil_exigido(TIPO_ADMIN)
def horarios(barbeiro_id):
    """Lista os horários da semana e cadastra um novo período (RN02)."""
    barbeiro = db.get_or_404(Barbeiro, barbeiro_id)
    form = HorarioForm(barbeiro_id=barbeiro.id)
    if form.validate_on_submit():
        db.session.add(HorarioTrabalho(
            barbeiro_id=barbeiro.id,
            dia_semana=form.dia_semana.data,
            hora_inicio=parse_hora(form.hora_inicio.data),
            hora_fim=parse_hora(form.hora_fim.data),
        ))
        db.session.commit()
        flash("Horário adicionado.", "success")
        return redirect(url_for("barbeiros.horarios", barbeiro_id=barbeiro.id))

    # Agrupa por dia da semana: {0: [períodos de segunda], 1: [...], ...}
    por_dia = {i: [] for i in range(7)}
    for h in sorted(barbeiro.horarios, key=lambda h: (h.dia_semana, h.hora_inicio)):
        por_dia[h.dia_semana].append(h)
    return render_template("barbeiros/horarios.html", barbeiro=barbeiro, form=form,
                           por_dia=por_dia, nomes_dias=NOMES_DIAS)


@bp.route("/<int:barbeiro_id>/horarios/<int:horario_id>/excluir", methods=["POST"])
@perfil_exigido(TIPO_ADMIN)
def excluir_horario(barbeiro_id, horario_id):
    horario = db.get_or_404(HorarioTrabalho, horario_id)
    if horario.barbeiro_id != barbeiro_id:     # evita apagar horário de outro barbeiro
        flash("Horário não encontrado.", "danger")
    else:
        db.session.delete(horario)
        db.session.commit()
        flash("Horário removido.", "success")
    return redirect(url_for("barbeiros.horarios", barbeiro_id=barbeiro_id))
