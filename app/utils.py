"""Funções auxiliares sem dependência de banco (fáceis de testar)."""
from datetime import datetime, time
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

CENTAVOS = Decimal("0.01")


def parse_preco(texto: str | None) -> Decimal | None:
    """Converte '35,00', '35.5' ou 'R$ 35' em Decimal com 2 casas.

    Devolve None se não for um número válido.
    """
    if texto is None:
        return None
    limpo = texto.strip().replace("R$", "").replace(" ", "").replace(",", ".")
    try:
        valor = Decimal(limpo)
        if not valor.is_finite():
            return None
        return valor.quantize(CENTAVOS, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        return None


def parse_duracao(texto: str | None) -> int | None:
    """Converte '30' em 30. Devolve None se não for número inteiro."""
    try:
        return int((texto or "").strip())
    except ValueError:
        return None


def formatar_preco(valor) -> str:
    """Decimal('35.00') vira '35,00' (formato brasileiro)."""
    if valor is None:
        return ""
    return f"{Decimal(valor):.2f}".replace(".", ",")


NOMES_DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


def parse_hora(texto: str | None) -> time | None:
    """Converte '08:00' (ou '8:00', '08:00:00') em time. None se for inválido."""
    texto = (texto or "").strip()
    for formato in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(texto, formato).time()
        except ValueError:
            continue
    return None


def periodos_se_sobrepoem(inicio_a: time, fim_a: time,
                          inicio_b: time, fim_b: time) -> bool:
    """True se os dois períodos têm algum minuto em comum.

    Encostar não conta: 08:00-12:00 e 12:00-18:00 NÃO se sobrepõem.
    """
    return inicio_a < fim_b and inicio_b < fim_a
