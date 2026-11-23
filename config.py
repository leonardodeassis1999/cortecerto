"""Configurações do CorteCerto.

Nenhuma senha ou chave fica no código: tudo vem de variáveis de ambiente
(arquivo .env no computador; painel da AlwaysData na publicação).
"""
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()


def _montar_uri_mysql() -> str:
    usuario = os.environ.get("DB_USER", "")
    senha = quote_plus(os.environ.get("DB_PASSWORD", ""))
    host = os.environ.get("DB_HOST", "localhost")
    porta = os.environ.get("DB_PORT", "3306")
    nome = os.environ.get("DB_NAME", "cortecerto")
    return f"mysql+pymysql://{usuario}:{senha}@{host}:{porta}/{nome}?charset=utf8mb4"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "")
    SQLALCHEMY_DATABASE_URI = _montar_uri_mysql()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Regras de negócio configuráveis (RN04, RN06, RN11, RN12, RN13)
    ANTECEDENCIA_MINIMA_HORAS = 1      # RN04
    PRAZO_CANCELAMENTO_HORAS = 2       # RN06
    MAX_DIAS_A_FRENTE = 30             # RN11
    MAX_AGENDAMENTOS_ATIVOS = 3        # RN12
    MAX_TENTATIVAS_LOGIN = 5           # RN13
    MINUTOS_BLOQUEIO_LOGIN = 15        # RN13
    DURACAO_SLOT_MINUTOS = 30          # tamanho do espaço na agenda
