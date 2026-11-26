"""Funções auxiliares sem dependência de banco (fáceis de testar)."""
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
