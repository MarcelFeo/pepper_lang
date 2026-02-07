from enum import Enum
from typing import Any

class TokenType(Enum):
    # special tokens
    EOF = "EOF"
    ILLEGAL = "ILLEGAL"

    # data types
    INT = "INT"
    FLOAT = "FLOAT"

    # arithmetic symbols
    PLUS = "PLUS"
    MINUS = "MINUS"
    ASTERISK = "ASTERISK"
    SLASH = "SLASH"
    POW = "POW"
    MODULUS = "MODULUS"

    # symbols
    SEMICOLON = "SEMICOLON"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"


