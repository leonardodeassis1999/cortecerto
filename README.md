# CorteCerto

> Seu horário, sem espera e sem conflito.

**Aluno:** Leonardo de Assis Melo Oliveira

## Objetivo
Sistema de agendamento online para barbearias. O cliente escolhe o serviço, o barbeiro e
um horário livre (calculado pela duração do serviço), sem ligar nem mandar mensagem. A
barbearia organiza a agenda do dia e reduz conflitos de horário e faltas.

## Principais funcionalidades
- Cadastro e login por perfil (Cliente, Barbeiro, Admin)
- Cadastro de serviços, barbeiros e horários de trabalho (Admin)
- Escolha de serviço, barbeiro e data, mostrando só horários livres
- Confirmar, cancelar e remarcar agendamentos (até 2h antes)
- Agenda do dia do barbeiro com status colorido (Confirmado, Concluído, Cancelado)

## Tecnologias
Python 3 · Flask · Flask-SQLAlchemy · Flask-Login · Flask-WTF · PyMySQL ·
MySQL/MariaDB · HTML5 + Jinja2 · Bootstrap 5 · JavaScript (Fetch API) · pytest ·
Git/GitHub · Miro (planejamento) · AlwaysData (publicação)

## Como rodar no seu computador
1. Crie e ative um ambiente virtual:
   ```
   python -m venv .venv
   .venv\Scripts\activate        (Windows)
   source .venv/bin/activate     (Linux/Mac)
   ```
2. Instale as dependências: `pip install -r requirements.txt`
3. Copie `.env.example` para `.env` e preencha com os dados do seu MySQL/MariaDB.
4. Crie o banco `cortecerto` e rode `database/schema.sql` dentro dele
   (opcional: `database/seed.sql` para serviços de exemplo).
5. Crie o administrador: `python -m scripts.criar_admin`
6. Inicie o servidor: `python run.py` e abra http://127.0.0.1:5000
7. Testes: `pytest`

## Estrutura
```
app/            código da aplicação (models, rotas, templates, estáticos)
database/       schema.sql (tabelas) e seed.sql (dados de exemplo)
scripts/        utilitários (criar_admin)
tests/          testes automatizados (pytest)
docs/           exportação do planejamento do Miro
config.py       configurações lidas de variáveis de ambiente
run.py          servidor de desenvolvimento
wsgi.py         entrada para publicação na AlwaysData
```

## Segurança
Senhas, chaves e dados de conexão ficam no arquivo `.env`, que **não** é versionado.
As senhas dos usuários são guardadas apenas como hash.

## Planejamento
Miro: https://miro.com/welcomeonboard/a1lRUUdJWmJJUkpCZnVCYlNxNjB2Qnk3SWpSV1pYT1gxVTgyb1BZaHBPK2h5QUtXSmljUWRhZExZYW5FU2hCNGtaWWFTQjhVZlZmaWYva0MzMXJGOUJ2U21YTWw3ZzdZdFBBNVZ3TG9MOVNVbXQ1aktQc0lvV3grUWtWRlJoMkphWWluRVAxeXRuUUgwWDl3Mk1qRGVRPT0hdjE=?share_link_id=989423271915 · Cópia exportada em `docs/`.

## Uso de IA
A IA (Claude, da Anthropic) foi usada como apoio. O registro de como foi usada e das
decisões do aluno está em `docs/registro-uso-ia.md`.
