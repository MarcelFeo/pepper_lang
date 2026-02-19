from enum import Enum
from typing import Any

class TokenType(Enum):
    # special tokens
    EOF = "EOF"
    ILLEGAL = "ILLEGAL"

    # data types
    IDENT = "IDENT"
    INT = "INT"
    FLOAT = "FLOAT"

    # arithmetic symbols
    PLUS = "PLUS"
    MINUS = "MINUS"
    ASTERISK = "ASTERISK"
    SLASH = "SLASH"
    POW = "POW"
    MODULUS = "MODULUS"

    # assignemt symbols
    EQ = "EQ"

    # symbols
    COLON = "COLON"
    SEMICOLON = "SEMICOLON"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"

    # keywords
    LET = "LET"

    # typing
    TYPE = "TYPE"

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

KEYWORDS: dict[str, TokenType] = {
    "let": TokenType.LET
}

ALT_KEYWORDS: dict[str, TokenType] = {
    "make": TokenType.LET,
    "equal": TokenType.EQ,
    "now": TokenType.SEMICOLON
}

TYPE_KEYWORDS: list[str] = ["int", "float"]

def lookup_ident(ident: str) -> TokenType:
    tt: TokenType | None = KEYWORDS.get(ident)
    if tt is not None:
        return tt

    tt: TokenType | None = ALT_KEYWORDS.get(ident)
    if tt is not None:
        return tt

    if ident in TYPE_KEYWORDS:
        return TokenType.TYPE

    return TokenType.IDENT
