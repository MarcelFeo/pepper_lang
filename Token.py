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

    # comparison symbols
    LT = '<'
    GT = '>'
    EQ_EQ = '=='
    MOT_EQ = '!='
    LT_EQ = '<='
    GT_EQ = '>='

    # symbols
    COLON = "COLON"
    SEMICOLON = "SEMICOLON"
    ARROW = "ARROW"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"

    # keywords
    LET = "LET"
    FN = "FN"
    RETURN = "RETURN"
    IF = "IF"
    ELSE = "ELSE"
    TRUE = "TRUE"
    FALSE = "FALSE"

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
    "let": TokenType.LET,
    # both `fn` and `fun` are accepted as function keywords; some tests
    # historically used "fun" so we map it here for compatibility.
    "fn": TokenType.FN,
    "fun": TokenType.FN,
    "return": TokenType.RETURN,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE
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
