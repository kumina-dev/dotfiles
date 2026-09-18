"""Small explicit Finnish/English display formats; no global locale mutation.

These helpers format values only. Currency codes describe the value's currency;
formatting never converts amounts. Pass Decimal or a decimal string for money.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext

from .region import read_preferences

CURRENCY_SYMBOLS = {"EUR": "€", "USD": "$", "GBP": "£"}


def _preferences(preferences):
    values = read_preferences() if preferences is None else preferences
    if values.get("number_format") not in ("fi", "en"):
        raise ValueError("Unsupported number format.")
    return values


def _rounded(value, decimals):
    if type(decimals) is not int or not 0 <= decimals <= 6:
        raise ValueError("Decimal places must be between zero and six.")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError("A finite number is required.") from error
    if not number.is_finite():
        raise ValueError("A finite number is required.")
    with localcontext() as context:
        context.prec = max(28, len(number.as_tuple().digits), number.adjusted() + decimals + 2)
        rounded = number.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)
    return rounded.copy_abs() if rounded == 0 else rounded


def format_number(value, preferences=None, *, decimals=2, grouping=True):
    """Format a value using explicit separators and display-only rounding."""
    values = _preferences(preferences)
    rounded = _rounded(value, decimals)
    text = format(rounded, f"{',' if grouping else ''}.{decimals}f")
    if values["number_format"] == "fi":
        text = text.replace(",", "\u00a0").replace(".", ",")
    return text


def format_currency(value, preferences=None, *, currency=None):
    """Use a known amount's currency when supplied; otherwise use the preference."""
    values = _preferences(preferences)
    code = values.get("currency") if currency is None else currency
    if not isinstance(code, str) or code not in CURRENCY_SYMBOLS:
        raise ValueError("Unsupported currency.")
    rounded = _rounded(value, 2)
    magnitude = format_number(rounded.copy_abs(), values, decimals=2)
    sign = "-" if rounded < 0 else ""
    symbol = CURRENCY_SYMBOLS[code]
    if values["number_format"] == "fi":
        return f"{sign}{magnitude}\u00a0{symbol}"
    return f"{sign}{symbol}{magnitude}"
