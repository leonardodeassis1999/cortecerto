-- CorteCerto - esquema do banco de dados (MySQL / MariaDB)
-- Tabelas: TB01 usuarios | TB02 servicos | TB03 barbeiros
--          TB04 horarios_trabalho | TB05 agendamentos
--
-- Como usar:
--   Local:      crie o banco e rode este arquivo dentro dele.
--   AlwaysData: crie o banco pelo painel, abra o phpMyAdmin e importe este arquivo.
--
-- (Opcional, só no computador local)
-- CREATE DATABASE IF NOT EXISTS cortecerto CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE cortecerto;

CREATE TABLE IF NOT EXISTS usuarios (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    nome              VARCHAR(100) NOT NULL,
    email             VARCHAR(120) NOT NULL,
    senha_hash        VARCHAR(255) NOT NULL,
    telefone          VARCHAR(20)  NOT NULL,
    tipo              VARCHAR(10)  NOT NULL DEFAULT 'cliente',
    tentativas_login  INT          NOT NULL DEFAULT 0,      -- RN13
    bloqueado_ate     DATETIME     NULL,                    -- RN13
    CONSTRAINT uq_usuarios_email UNIQUE (email),            -- RN15
    CONSTRAINT ck_usuarios_tipo CHECK (tipo IN ('cliente', 'barbeiro', 'admin'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS servicos (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    nome             VARCHAR(80)   NOT NULL,
    duracao_minutos  INT           NOT NULL,                -- RN03
    preco            DECIMAL(10,2) NOT NULL,
    ativo            BOOLEAN       NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_servicos_nome UNIQUE (nome),              -- RN15
    CONSTRAINT ck_servicos_duracao CHECK (duracao_minutos > 0),
    CONSTRAINT ck_servicos_preco CHECK (preco > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS barbeiros (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id     INT         NOT NULL,
    especialidade  VARCHAR(80) NULL,
    ativo          BOOLEAN     NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_barbeiros_usuario UNIQUE (usuario_id),    -- relação 1 para 1
    CONSTRAINT fk_barbeiros_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS horarios_trabalho (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    barbeiro_id  INT      NOT NULL,
    dia_semana   SMALLINT NOT NULL,                         -- 0=segunda ... 6=domingo
    hora_inicio  TIME     NOT NULL,
    hora_fim     TIME     NOT NULL,
    CONSTRAINT fk_horarios_barbeiro FOREIGN KEY (barbeiro_id) REFERENCES barbeiros (id),
    CONSTRAINT ck_horarios_dia CHECK (dia_semana BETWEEN 0 AND 6),
    CONSTRAINT ck_horarios_periodo CHECK (hora_fim > hora_inicio)   -- RN02
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS agendamentos (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id   INT         NOT NULL,
    barbeiro_id  INT         NOT NULL,
    servico_id   INT         NOT NULL,
    data         DATE        NOT NULL,
    hora_inicio  TIME        NOT NULL,
    hora_fim     TIME        NOT NULL,                      -- início + duração (RN03)
    status       VARCHAR(10) NOT NULL DEFAULT 'Confirmado', -- RN07
    CONSTRAINT fk_agend_cliente  FOREIGN KEY (cliente_id)  REFERENCES usuarios (id),
    CONSTRAINT fk_agend_barbeiro FOREIGN KEY (barbeiro_id) REFERENCES barbeiros (id),
    CONSTRAINT fk_agend_servico  FOREIGN KEY (servico_id)  REFERENCES servicos (id),
    CONSTRAINT ck_agend_periodo CHECK (hora_fim > hora_inicio),
    CONSTRAINT ck_agend_status CHECK (status IN ('Confirmado', 'Concluído', 'Cancelado')),
    INDEX ix_agendamento_barbeiro_data (barbeiro_id, data, hora_inicio)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
