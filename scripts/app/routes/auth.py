"""T01 Login, T02 Cadastro e saída do sistema."""
from datetime import datetime

from flask import Blueprint, current_app, flash, redirect, render_template, url_for
from flask_login import login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.forms import CadastroForm, LoginForm, MSG_EMAIL_USADO, limpar_telefone
from app.models import TIPO_CLIENTE, Usuario
from app.routes.decoradores import redirecionar_se_logado

bp = Blueprint("auth", __name__)


@bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    ja_logado = redirecionar_se_logado()
    if ja_logado:
        return ja_logado

    form = CadastroForm()
    if form.validate_on_submit():
        # Cadastro público cria sempre um CLIENTE (RN10: só o admin cria barbeiros)
        usuario = Usuario(
            nome=form.nome.data,
            email=form.email.data,
            telefone=limpar_telefone(form.telefone.data),
            tipo=TIPO_CLIENTE,
        )
        usuario.definir_senha(form.senha.data)
        db.session.add(usuario)
        try:
            db.session.commit()
        except IntegrityError:
            # Outro cadastro com o mesmo e-mail chegou primeiro (RN15 no banco)
            db.session.rollback()
            form.email.errors.append(MSG_EMAIL_USADO)
        else:
            flash("Conta criada! Faça login para continuar.", "success")
            return redirect(url_for("auth.login"))
    return render_template("auth/cadastro.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    ja_logado = redirecionar_se_logado()
    if ja_logado:
        return ja_logado

    form = LoginForm()
    if form.validate_on_submit():
        cfg = current_app.config
        agora = datetime.now()
        minutos = cfg["MINUTOS_BLOQUEIO_LOGIN"]
        msg_bloqueada = f"Conta bloqueada por {minutos} minutos"     # SE02
        usuario = Usuario.query.filter_by(email=form.email.data).first()

        if usuario and usuario.esta_bloqueado(agora):
            flash(msg_bloqueada, "danger")                            # RN13
        elif usuario and usuario.conferir_senha(form.senha.data):
            usuario.registrar_login_ok()
            db.session.commit()
            login_user(usuario)
            return redirecionar_se_logado()
        else:
            mensagem = "E-mail ou senha inválidos"                    # SE01
            if usuario:
                bloqueou = usuario.registrar_falha_login(
                    cfg["MAX_TENTATIVAS_LOGIN"], minutos, agora)
                db.session.commit()
                if bloqueou:
                    mensagem = msg_bloqueada
            flash(mensagem, "danger")
    return render_template("auth/login.html", form=form)


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Você saiu do sistema.", "info")
    return redirect(url_for("auth.login"))
