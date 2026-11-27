"""T04 Serviço e barbeiro, T05 Data e horário, T06 Confirmação (RF04 a RF06).

O cliente vai passo a passo. O que ele já escolheu viaja na própria URL
(servico, barbeiro, data, hora e, ao remarcar, remarcar=<id>).
"""
from datetime import datetime, timedelta

from flask import (Blueprint, current_app, flash, redirect, render_template,
                   request, url_for)
from flask_login import current_user

from app.agenda import (MSG_ESCOLHA_INVALIDA, MSG_ESCOLHA_OBRIGATORIA,
                        calcular_grade, data_dentro_do_prazo,
                        mensagem_prazo_expirado, prazo_de_alteracao_ok,
                        validar_agendamento)
from app.extensions import db
from app.models import (STATUS_CONFIRMADO, TIPO_CLIENTE, Agendamento, Barbeiro,
                        Servico, Usuario)
from app.routes.decoradores import perfil_exigido
from app.utils import NOMES_DIAS, parse_hora

bp = Blueprint("agendar", __name__, url_prefix="/agendar")


def _ler_data(texto):
    try:
        return datetime.strptime(texto or "", "%Y-%m-%d").date()
    except ValueError:
        return None


def _ler_escolha(valores):
    """Lê servico, barbeiro e (opcional) remarcar. Devolve (servico, barbeiro, remarcando, erro)."""
    servico = db.session.get(Servico, valores.get("servico", type=int) or 0)
    barbeiro = db.session.get(Barbeiro, valores.get("barbeiro", type=int) or 0)
    remarcando = None
    if not (servico and barbeiro):
        return None, None, None, MSG_ESCOLHA_OBRIGATORIA                   # SE04
    if not (servico.ativo and barbeiro.ativo):
        return None, None, None, MSG_ESCOLHA_INVALIDA
    if valores.get("remarcar", type=int):
        remarcando = db.session.get(Agendamento, valores.get("remarcar", type=int))
        if (not remarcando or remarcando.cliente_id != current_user.id
                or remarcando.status != STATUS_CONFIRMADO):
            return None, None, None, "Agendamento não encontrado"
    return servico, barbeiro, remarcando, None


def _params(servico, barbeiro, remarcando):
    """Parâmetros que acompanham o cliente de uma tela para outra."""
    p = {"servico": servico.id, "barbeiro": barbeiro.id}
    if remarcando:
        p["remarcar"] = remarcando.id
    return p


def _destino_de_erro(valores):
    """Se deu erro na escolha: volta ao T07 (remarcando) ou ao T04."""
    if valores.get("remarcar"):
        return redirect(url_for("agendamentos.lista"))
    return redirect(url_for("agendar.escolher"))


@bp.route("/")
@perfil_exigido(TIPO_CLIENTE)
def escolher():
    """T04 Serviço e barbeiro."""
    servicos = Servico.query.filter_by(ativo=True).order_by(Servico.nome).all()
    barbeiros = (Barbeiro.query.join(Usuario).filter(Barbeiro.ativo.is_(True))
                 .order_by(Usuario.nome).all())
    return render_template(
        "agendar/servico_barbeiro.html", servicos=servicos, barbeiros=barbeiros,
        servico_id=request.args.get("servico", type=int),
        barbeiro_id=request.args.get("barbeiro", type=int))


@bp.route("/data")
@perfil_exigido(TIPO_CLIENTE)
def data_horario():
    """T05 Data e horário (RF05: mostra os horários livres)."""
    servico, barbeiro, remarcando, erro = _ler_escolha(request.args)
    if erro:
        flash(erro, "danger")
        return _destino_de_erro(request.args)

    hoje = datetime.now().date()
    max_dias = current_app.config["MAX_DIAS_A_FRENTE"]
    dia = _ler_data(request.args.get("data"))
    grade = None
    if request.args.get("data"):
        erro_data = ("Escolha uma data" if dia is None
                     else data_dentro_do_prazo(dia, hoje, max_dias))
        if erro_data:
            flash(erro_data, "danger")
        else:
            grade = calcular_grade(barbeiro, servico, dia,
                                   ignorar_id=remarcando.id if remarcando else None)
    return render_template(
        "agendar/data_horario.html", servico=servico, barbeiro=barbeiro,
        remarcando=remarcando, params=_params(servico, barbeiro, remarcando),
        dia=dia, grade=grade, tem_livre=bool(grade) and any(l for _, l in grade),
        data_min=hoje.isoformat(),
        data_max=(hoje + timedelta(days=max_dias)).isoformat())


@bp.route("/confirmacao")
@perfil_exigido(TIPO_CLIENTE)
def confirmacao():
    """T06 Confirmação: só leitura, com Confirmar, Alterar e Cancelar operação."""
    servico, barbeiro, remarcando, erro = _ler_escolha(request.args)
    if erro:
        flash(erro, "danger")
        return _destino_de_erro(request.args)

    params = _params(servico, barbeiro, remarcando)
    dia = _ler_data(request.args.get("data"))
    hora = parse_hora(request.args.get("hora"))
    if not (dia and hora):
        flash(MSG_ESCOLHA_OBRIGATORIA, "danger")                           # SE04
        return redirect(url_for("agendar.data_horario", **params,
                                data=request.args.get("data") or None))
    fim = (datetime.combine(dia, hora) + timedelta(minutes=servico.duracao_minutos)).time()
    return render_template(
        "agendar/confirmacao.html", servico=servico, barbeiro=barbeiro,
        remarcando=remarcando, params=params, dia=dia, hora=hora, fim=fim,
        nome_dia=NOMES_DIAS[dia.weekday()].lower())


@bp.route("/confirmar", methods=["POST"])
@perfil_exigido(TIPO_CLIENTE)
def confirmar():
    servico, barbeiro, remarcando, erro = _ler_escolha(request.form)
    if erro:
        flash(erro, "danger")
        return _destino_de_erro(request.form)

    dia = _ler_data(request.form.get("data"))
    hora = parse_hora(request.form.get("hora"))
    params = _params(servico, barbeiro, remarcando)
    if not (dia and hora):
        flash(MSG_ESCOLHA_OBRIGATORIA, "danger")
        return redirect(url_for("agendar.data_horario", **params))

    voltar = url_for("agendar.confirmacao", **params, data=dia.isoformat(),
                     hora=hora.strftime("%H:%M"))

    # RN06: ao remarcar, o agendamento atual precisa estar a 2h ou mais do horário
    if remarcando and not prazo_de_alteracao_ok(remarcando):
        flash(mensagem_prazo_expirado(), "danger")                         # SE08
        return redirect(url_for("agendamentos.lista"))

    # Trava a linha do barbeiro: dois clientes no mesmo horário são atendidos
    # um de cada vez (RN01). No MySQL isso é um SELECT ... FOR UPDATE.
    db.session.query(Barbeiro).filter_by(id=barbeiro.id).with_for_update().one()

    erro = validar_agendamento(current_user.id, servico, barbeiro, dia, hora,
                               ignorar_id=remarcando.id if remarcando else None)
    if erro:
        db.session.rollback()
        flash(erro, "danger")                                              # SE06 / SE07
        return redirect(voltar)

    fim = (datetime.combine(dia, hora) + timedelta(minutes=servico.duracao_minutos)).time()
    if remarcando:                      # remarcar muda o mesmo agendamento
        remarcando.data, remarcando.hora_inicio, remarcando.hora_fim = dia, hora, fim
        mensagem = "Agendamento remarcado!"
    else:
        db.session.add(Agendamento(
            cliente_id=current_user.id, barbeiro_id=barbeiro.id, servico_id=servico.id,
            data=dia, hora_inicio=hora, hora_fim=fim))                     # RN03
        mensagem = "Agendamento confirmado!"
    db.session.commit()
    flash(mensagem, "success")
    return redirect(url_for("agendamentos.lista"))
