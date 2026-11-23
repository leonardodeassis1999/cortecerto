-- Dados de exemplo (opcional). Rode DEPOIS do schema.sql.
-- O usuário admin NÃO é criado aqui (precisa de senha com hash):
-- use "python -m scripts.criar_admin".

INSERT IGNORE INTO servicos (nome, duracao_minutos, preco) VALUES
    ('Corte',        30, 35.00),
    ('Barba',        30, 25.00),
    ('Corte + Barba', 60, 55.00);
