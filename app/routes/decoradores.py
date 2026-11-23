"""Controle de acesso por perfil (RN09, RN10 e SE09)."""
from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user

from app.extensions import login_manager
from app.models import TIPO_ADMIN, TIPO_BARBEIRO, TIPO_CLIENTE

# Para onde cada perfil vai depois de entrar
ROTA_INICIAL = {
    TIPO_CLIENTE: "paineis.inicio_cliente",    # T03
    TIPO_BARBEIRO: "paineis.agenda_barbeiro",  # T08
    TIPO_ADMIN: "paineis.painel_admin",        # T10
}


def redirecionar_se_logado():
    """Se já estiver logado, devolve o redirecionamento para o menu do perfil."""
    if current_user.is_authenticated and current_user.tipo in ROTA_INICIAL:
        return redirect(url_for(ROTA_INICIAL[current_user.tipo]))
    return None


def perfil_exigido(*tipos):
    """Só deixa passar quem estiver logado E tiver um dos perfis informados."""
    def decorador(funcao):
        @wraps(funcao)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()      # SE12: vai para o login
            if current_user.tipo not in tipos:
                flash("Acesso negado", "danger")          # SE09
                return redirecionar_se_logado() or redirect(url_for("main.index"))
            return funcao(*args, **kwargs)
        return wrapper
    return decorador
