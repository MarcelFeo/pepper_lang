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

class Token:
    def __init__(self, type: TokenType, literal: Any, line_number: int, position: int) -> None:
        self.type = type
        self.literal = literal
        self.line_number = line_number
        self.position = position

    def __str__(self) -> str:
        return f"Token[{self.type} : {self.literal} : Line {self.line_number} : Position {self.position}]"

    def __repr__(self) -> str:
        return str(self)




