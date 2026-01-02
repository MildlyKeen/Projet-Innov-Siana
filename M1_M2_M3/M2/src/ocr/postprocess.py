def clean_text(t: str) -> str:
    if t is None:
        return ""
    t = t.strip().replace(" ", "")
    # corrections fréquentes (si jamais)
    t = t.replace("O", "0").replace("I", "1").replace("l", "1")
    return t
