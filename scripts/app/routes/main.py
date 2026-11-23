"""Página inicial."""
from flask import Blueprint, render_template

from app.routes.decoradores import redirecionar_se_logado

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return redirecionar_se_logado() or render_template("index.html")
