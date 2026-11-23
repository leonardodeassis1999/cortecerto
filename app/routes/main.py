"""Rotas gerais. As demais telas (T01 a T11) entram nas próximas etapas."""
from flask import Blueprint, render_template

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return render_template("index.html")
