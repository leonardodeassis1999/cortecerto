"""Formulários do CorteCerto (Flask-WTF) - validações da T01 e T02."""
import re

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField
from sqlalchemy import func
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError

from app.models import Servico, Usuario
from app.utils import parse_duracao, parse_preco

MSG_OBRIGATORIO = "Preencha todos os campos"          # SE04
MSG_EMAIL_USADO = "Este e-mail já está em uso"        # SE03
MSG_NOME_SERVICO_USADO = "Já existe um serviço com este nome"  # RN15
DURACAO_MAXIMA_MIN = 480
PRECO_MAXIMO = 9999.99
REGEX_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def limpar_telefone(valor: str | None) -> str:
    """Deixa só os números: '(49) 98869-6644' vira '49988696644'."""
    return re.sub(r"\D", "", valor or "")


def telefone_valido(valor: str | None) -> bool:
    """Telefone com DDD: 10 ou 11 dígitos e DDD de 11 a 99."""
    numeros = limpar_telefone(valor)
    return len(numeros) in (10, 11) and int(numeros[:2]) >= 11


def _minusculo_sem_espacos(valor):
    return valor.strip().lower() if valor else valor


def _sem_espacos(valor):
    return valor.strip() if valor else valor


class CadastroForm(FlaskForm):
    """T02 Cadastro."""
    nome = StringField(
        "Nome",
        filters=[_sem_espacos],
        validators=[DataRequired(message=MSG_OBRIGATORIO), Length(max=100)],
    )
    email = StringField(
        "E-mail",
        filters=[_minusculo_sem_espacos],
        validators=[DataRequired(message=MSG_OBRIGATORIO), Length(max=120)],
    )
    telefone = StringField(
        "Telefone com DDD",
        filters=[_sem_espacos],
        validators=[DataRequired(message=MSG_OBRIGATORIO)],
    )
    senha = PasswordField(
        "Senha",
        validators=[
            DataRequired(message=MSG_OBRIGATORIO),
            Length(min=6, message="A senha deve ter 6 ou mais caracteres"),
        ],
    )
    confirmar_senha = PasswordField(
        "Confirmar senha",
        validators=[
            DataRequired(message=MSG_OBRIGATORIO),
            EqualTo("senha", message="As senhas não conferem"),
        ],
    )

    def validate_email(self, campo):
        if not REGEX_EMAIL.match(campo.data):
            raise ValidationError("E-mail em formato inválido")
        if Usuario.query.filter_by(email=campo.data).first():
            raise ValidationError(MSG_EMAIL_USADO)

    def validate_telefone(self, campo):
        if not telefone_valido(campo.data):
            raise ValidationError("Informe o telefone com DDD, ex.: (49) 98888-7777")


class LoginForm(FlaskForm):
    """T01 Login."""
    email = StringField(
        "E-mail",
        filters=[_minusculo_sem_espacos],
        validators=[DataRequired(message=MSG_OBRIGATORIO)],
    )
    senha = PasswordField(
        "Senha",
        validators=[DataRequired(message=MSG_OBRIGATORIO)],
    )


class ServicoForm(FlaskForm):
    """T09 Serviços: cadastro e edição (RF02)."""
    nome = StringField(
        "Nome do serviço",
        filters=[_sem_espacos],
        validators=[DataRequired(message=MSG_OBRIGATORIO), Length(max=80)],
    )
    duracao_minutos = StringField(
        "Duração (minutos)",
        filters=[_sem_espacos],
        validators=[DataRequired(message=MSG_OBRIGATORIO)],
        render_kw={"type": "number", "min": 1, "inputmode": "numeric"},
    )
    preco = StringField(
        "Preço (R$)",
        filters=[_sem_espacos],
        validators=[DataRequired(message=MSG_OBRIGATORIO)],
        render_kw={"inputmode": "decimal"},
    )

    def __init__(self, *args, servico_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servico_id = servico_id   # na edição, o próprio serviço não conta como repetido

    def validate_nome(self, campo):
        existente = Servico.query.filter(
            func.lower(Servico.nome) == campo.data.lower())
        if self.servico_id is not None:
            existente = existente.filter(Servico.id != self.servico_id)
        if existente.first():
            raise ValidationError(MSG_NOME_SERVICO_USADO)

    def validate_duracao_minutos(self, campo):
        minutos = parse_duracao(campo.data)
        if minutos is None:
            raise ValidationError("Informe a duração em minutos (número inteiro)")
        if minutos <= 0:
            raise ValidationError("A duração deve ser maior que zero")
        if minutos > DURACAO_MAXIMA_MIN:
            raise ValidationError(f"A duração máxima é {DURACAO_MAXIMA_MIN} minutos")

    def validate_preco(self, campo):
        valor = parse_preco(campo.data)
        if valor is None:
            raise ValidationError("Informe um preço válido, ex.: 35,00")
        if valor <= 0:
            raise ValidationError("O preço deve ser maior que zero")
        if valor > PRECO_MAXIMO:
            raise ValidationError("Preço acima do máximo permitido")
