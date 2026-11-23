"""Modelos (tabelas) do CorteCerto - TB01 a TB05.

Espelham o desenho do banco no Miro:
USUARIO 1-N AGENDAMENTO, SERVICO 1-N AGENDAMENTO,
BARBEIRO 1-N AGENDAMENTO, USUARIO 1-1 BARBEIRO, BARBEIRO 1-N HORARIO_TRABALHO.
"""
from datetime import datetime, timedelta

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager

# Valores permitidos (RN07 e perfis de acesso)
STATUS_CONFIRMADO = "Confirmado"
STATUS_CONCLUIDO = "Concluído"
STATUS_CANCELADO = "Cancelado"
STATUS_VALIDOS = (STATUS_CONFIRMADO, STATUS_CONCLUIDO, STATUS_CANCELADO)

TIPO_CLIENTE = "cliente"
TIPO_BARBEIRO = "barbeiro"
TIPO_ADMIN = "admin"
TIPOS_VALIDOS = (TIPO_CLIENTE, TIPO_BARBEIRO, TIPO_ADMIN)


class Usuario(UserMixin, db.Model):
    """TB01 - quem acessa o sistema (cliente, barbeiro ou admin)."""
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)  # RN15
    senha_hash = db.Column(db.String(255), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    tipo = db.Column(db.String(10), nullable=False, default=TIPO_CLIENTE)
    tentativas_login = db.Column(db.Integer, nullable=False, default=0)  # RN13
    bloqueado_ate = db.Column(db.DateTime, nullable=True)                # RN13

    barbeiro = db.relationship("Barbeiro", back_populates="usuario", uselist=False)
    agendamentos = db.relationship("Agendamento", back_populates="cliente")

    def definir_senha(self, senha: str) -> None:
        """Guarda apenas o hash da senha, nunca a senha em texto."""
        self.senha_hash = generate_password_hash(senha)

    def conferir_senha(self, senha: str) -> bool:
        return check_password_hash(self.senha_hash, senha)

    def esta_bloqueado(self, agora: datetime | None = None) -> bool:
        """RN13: conta bloqueada enquanto 'bloqueado_ate' estiver no futuro."""
        agora = agora or datetime.now()
        return self.bloqueado_ate is not None and self.bloqueado_ate > agora

    def registrar_falha_login(self, maximo: int, minutos: int,
                              agora: datetime | None = None) -> bool:
        """RN13: conta uma senha errada. Ao chegar no máximo, bloqueia a conta.

        Devolve True se esta falha bloqueou a conta.
        """
        agora = agora or datetime.now()
        self.tentativas_login = (self.tentativas_login or 0) + 1
        if self.tentativas_login >= maximo:
            self.bloqueado_ate = agora + timedelta(minutes=minutos)
            self.tentativas_login = 0
            return True
        return False

    def registrar_login_ok(self) -> None:
        """Login correto: zera as tentativas erradas e libera o bloqueio."""
        self.tentativas_login = 0
        self.bloqueado_ate = None

    def __repr__(self) -> str:
        return f"<Usuario {self.email} ({self.tipo})>"


class Servico(db.Model):
    """TB02 - serviços oferecidos (corte, barba, corte + barba...)."""
    __tablename__ = "servicos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False, unique=True)  # RN15
    duracao_minutos = db.Column(db.Integer, nullable=False)       # RN03
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    agendamentos = db.relationship("Agendamento", back_populates="servico")

    def __repr__(self) -> str:
        return f"<Servico {self.nome} {self.duracao_minutos}min>"


class Barbeiro(db.Model):
    """TB03 - perfil profissional ligado a um usuário (relação 1 para 1)."""
    __tablename__ = "barbeiros"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"),
                           nullable=False, unique=True)
    especialidade = db.Column(db.String(80), nullable=True)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    usuario = db.relationship("Usuario", back_populates="barbeiro")
    horarios = db.relationship("HorarioTrabalho", back_populates="barbeiro",
                               cascade="all, delete-orphan")
    agendamentos = db.relationship("Agendamento", back_populates="barbeiro")

    def __repr__(self) -> str:
        return f"<Barbeiro id={self.id}>"


class HorarioTrabalho(db.Model):
    """TB04 - expediente do barbeiro por dia da semana (RN02)."""
    __tablename__ = "horarios_trabalho"

    id = db.Column(db.Integer, primary_key=True)
    barbeiro_id = db.Column(db.Integer, db.ForeignKey("barbeiros.id"), nullable=False)
    dia_semana = db.Column(db.SmallInteger, nullable=False)  # 0=segunda ... 6=domingo
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fim = db.Column(db.Time, nullable=False)

    barbeiro = db.relationship("Barbeiro", back_populates="horarios")


class Agendamento(db.Model):
    """TB05 - horário marcado por um cliente com um barbeiro para um serviço."""
    __tablename__ = "agendamentos"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    barbeiro_id = db.Column(db.Integer, db.ForeignKey("barbeiros.id"), nullable=False)
    servico_id = db.Column(db.Integer, db.ForeignKey("servicos.id"), nullable=False)
    data = db.Column(db.Date, nullable=False)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fim = db.Column(db.Time, nullable=False)  # início + duração do serviço (RN03)
    status = db.Column(db.String(10), nullable=False, default=STATUS_CONFIRMADO)  # RN07

    cliente = db.relationship("Usuario", back_populates="agendamentos")
    barbeiro = db.relationship("Barbeiro", back_populates="agendamentos")
    servico = db.relationship("Servico", back_populates="agendamentos")

    __table_args__ = (
        db.Index("ix_agendamento_barbeiro_data", "barbeiro_id", "data", "hora_inicio"),
    )

    def __repr__(self) -> str:
        return f"<Agendamento {self.data} {self.hora_inicio} {self.status}>"


@login_manager.user_loader
def carregar_usuario(usuario_id: str):
    """Usado pelo Flask-Login para recuperar o usuário da sessão."""
    return db.session.get(Usuario, int(usuario_id))
