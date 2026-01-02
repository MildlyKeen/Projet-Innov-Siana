import re

PATTERN = re.compile(r"^\d{3,5}$")

def is_valid_loco_number(text: str) -> bool:
    return bool(PATTERN.match(text))
