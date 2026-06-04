"""Keyword-based merchant → category rules. Add entries freely — order matters (first match wins)."""
from typing import Optional

# Each entry: (list of substrings to match, category name)
# Matching is case-insensitive substring search on the merchant field.
RULES: list[tuple[list[str], str]] = [
    # Groceries
    (["continente", "pingo doce", "lidl", "aldi", "mercadona", "intermarche",
      "minipreco", "mini preco", "jumbo", "el corte ingles", "froiz"], "Groceries"),
    # Restaurants / Dining
    (["mcdonald", "burger king", "kfc", "subway", "nando", "pizza", "sushi",
      "restaurante", "tasca", "taberna", "cervejaria", "bifanas", "pastelaria",
      "padaria", "cafe ", "snack"], "Restaurants"),
    # Transportation
    (["cp comboios", "metro", "carris", "uber", "bolt ", "cabify", "flixbus",
      "renfe", "sncf", "ryanair", "tap ", "easyjet", "wizz", "transavia",
      "autoestrada", "via verde", "bxval", "portagem"], "Transportation"),
    # Utilities
    (["ibelectra", "edp ", "e.dp", "endesa", "galp", "goldenergy", "enel",
      "agua ", "aguas ", "eggas", "lisboagas", "setgás", "nos ", "meo ",
      "vodafone", "nowo", "internet", "telecomunicacoes"], "Utilities"),
    # Healthcare
    (["farmacia", "farmácia", "clinica", "cliníca", "hospital", "consultorio",
      "medico", "médico", "dentista", "optica", "wells", "dr."], "Healthcare"),
    # Shopping
    (["amazon", "ikea", "fnac", "mediamarkt", "worten", "leroy merlin",
      "aki ", "zara", "h&m", "pull", "primark", "mango", "sport zone",
      "decathlon", "staples", "shein"], "Shopping"),
    # Entertainment
    (["netflix", "spotify", "hbo", "disney", "apple tv", "youtube premium",
      "steam", "playstation", "xbox", "cinema", "teatro", "bilheteira",
      "ticketmaster"], "Entertainment"),
    # Travel
    (["airbnb", "booking.com", "expedia", "hotel", "hostel", "pousada",
      "turismo"], "Travel"),
    # Insurance
    (["seguro", "fidelidade", "ageas", "allianz", "axa ", "liberty mutual",
      "zurich", "generali", "tranquilidade"], "Insurance"),
    # Salary / Income
    (["salario", "salário", "vencimento", "ordenado", "pagamento ordenado"], "Salary"),
    # Investments
    (["trading", "degiro", "etoro", "xtb", "revolut invest", "wise invest"], "Investments"),
]


def guess_category(merchant: str) -> Optional[str]:
    """Return first matching category for merchant name, or None."""
    if not merchant:
        return None
    lower = merchant.lower()
    for keywords, category in RULES:
        if any(kw in lower for kw in keywords):
            return category
    return None
