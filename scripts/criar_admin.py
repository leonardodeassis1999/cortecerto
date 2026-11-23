"""Cria o primeiro usuário administrador.

Uso (na pasta do projeto, com o banco já criado):
    python -m scripts.criar_admin
A senha é digitada no terminal e guardada apenas como hash.
"""
from getpass import getpass

from app import create_app
from app.extensions import db
from app.models import TIPO_ADMIN, Usuario


def main() -> None:
    app = create_app()
    with app.app_context():
        nome = input("Nome do admin: ").strip()
        email = input("E-mail: ").strip().lower()
        telefone = input("Telefone com DDD: ").strip()
        senha = getpass("Senha (mínimo 6 caracteres): ")

        if not (nome and email and telefone):
            print("Preencha todos os campos.")
            return
        if len(senha) < 6:
            print("A senha precisa ter 6 ou mais caracteres.")
            return
        if Usuario.query.filter_by(email=email).first():
            print("Este e-mail já está em uso.")
            return

        admin = Usuario(nome=nome, email=email, telefone=telefone, tipo=TIPO_ADMIN)
        admin.definir_senha(senha)
        db.session.add(admin)
        db.session.commit()
        print(f"Admin criado: {email}")


if __name__ == "__main__":
    main()
