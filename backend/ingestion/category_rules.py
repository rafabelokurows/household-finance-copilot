"""Keyword-based merchant → category rules. Seeded into DB on first run; editable via /api/categories."""
from typing import Optional

# Source of truth for DB seeding on first startup. Edit via UI after that.
RULES: list[tuple[list[str], str]] = [
    (["continente", "pingo doce", "lidl", "aldi", "mercadona", "intermarche",
      "minipreco", "mini preco", "jumbo", "el corte ingles", "froiz"], "Groceries"),
    (["mcdonald", "burger king", "kfc", "subway", "nando", "pizza", "sushi",
      "restaurante", "tasca", "taberna", "cervejaria", "bifanas", "pastelaria",
      "padaria", "cafe ", "snack"], "Restaurants"),
    (["cp comboios", "metro", "carris", "uber", "bolt ", "cabify", "flixbus",
      "renfe", "sncf", "ryanair", "tap ", "easyjet", "wizz", "transavia",
      "autoestrada", "via verde", "bxval", "portagem"], "Transportation"),
    (["ibelectra", "edp ", "e.dp", "endesa", "galp", "goldenergy", "enel",
      "agua ", "aguas ", "eggas", "lisboagas", "setgás", "nos ", "meo ",
      "vodafone", "nowo", "internet", "telecomunicacoes"], "Utilities"),
    (["farmacia", "farmácia", "clinica", "cliníca", "hospital", "consultorio",
      "medico", "médico", "dentista", "optica", "wells", "dr."], "Healthcare"),
    (["amazon", "ikea", "fnac", "mediamarkt", "worten", "leroy merlin",
      "aki ", "zara", "h&m", "pull", "primark", "mango", "sport zone",
      "decathlon", "staples", "shein"], "Shopping"),
    (["netflix", "spotify", "hbo", "disney", "apple tv", "youtube premium",
      "steam", "playstation", "xbox", "cinema", "teatro", "bilheteira",
      "ticketmaster"], "Entertainment"),
    (["airbnb", "booking.com", "expedia", "hotel", "hostel", "pousada",
      "turismo"], "Travel"),
    (["seguro", "fidelidade", "ageas", "allianz", "axa ", "liberty mutual",
      "zurich", "generali", "tranquilidade"], "Insurance"),
    (["salario", "salário", "vencimento", "ordenado", "pagamento ordenado"], "Salary"),
    (["trading", "degiro", "etoro", "xtb", "revolut invest", "wise invest"], "Investments"),
]


def guess_category(merchant: str) -> Optional[str]:
    """Return first matching category for merchant name using DB rules, or None."""
    if not merchant:
        return None
    lower = merchant.lower()
    try:
        from ..db.client import get_connection
        conn = get_connection()
        rows = conn.execute(
            "SELECT keyword, category FROM category_rules ORDER BY priority, id"
        ).fetchall()
        for row in rows:
            if row[0] in lower:
                return row[1]
    except Exception:
        # Fallback to hardcoded rules if DB unavailable
        for keywords, category in RULES:
            if any(kw in lower for kw in keywords):
                return category
    return None
