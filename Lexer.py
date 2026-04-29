from Token import Token, TokenType, lookup_ident
from typing import Any

class Lexer:
    def __init__(self, source: str) -> None:
        self.source = source

        self.position: int = -1
        self.read_position: int = 0
        self.line_number: int = 1

        self.current_char: str | None = None

        self.__read_char()

    def __read_char(self) -> None:
        if self.read_position >= len(self.source):
            self.current_char = None
        else:
            self.current_char = self.source[self.read_position]

        self.position = self.read_position
        self.read_position += 1

    def __skip_whitespace(self) -> None:
        while self.current_char in [' ', '\t', '\n', '\r']:
            if self.current_char == '\n':
                self.line_number += 1

            self.__read_char()

    def __new_token(self, tt: TokenType, literal: Any) -> Token:
        return Token(type=tt, literal=literal, line_number=self.line_number, position=self.position)

    def __is_digit(self, char: str):
        return '0' <= char and char <= '9'

    def __is_letter(self, ch: str) -> bool:
        return 'a' <= ch and ch <= 'z' or 'A' <= ch and ch <= 'Z' or ch == '_'

    def __read_number(self) -> Token:
        start_positon: int = self.position
        dot_count: int = 0

        output: str = ""
        while self.__is_digit(self.current_char) or self.current_char == '.':
            if self.current_char == '.':
                dot_count += 1

            if dot_count > 1:
                print(f"TOO MANY DECIMALS IN NUMBER ON LINE {self.line_number}, POSITION {self.position}")
                return self.__new_token(TokenType.ILLEGAL, self.source[start_positon:self.position])

            output += self.source[self.position]
            self.__read_char()

            if self.current_char is None:
                break

        if dot_count == 0:
            return self.__new_token(TokenType.INT, int(output))
        else:
            return self.__new_token(TokenType.FLOAT, float(output))

    def __read_string(self) -> Token:
        # current_char is '"' when called
        # consume opening quote
        self.__read_char()

        start = self.position
        out = ""
        while self.current_char is not None and self.current_char != '"':
            if self.current_char == '\\':
                # handle simple escape sequences
                self.__read_char()
                if self.current_char is None:
                    break
                esc = self.current_char
                if esc == 'n':
                    out += '\n'
                elif esc == 't':
                    out += '\t'
                else:
                    out += esc
                self.__read_char()
                continue

            out += self.current_char
            self.__read_char()

        # consume closing quote
        self.__read_char()

        return self.__new_token(TokenType.STRING, out)

    def __read_identifier(self) -> str:
        position = self.position
        while self.current_char is not None and (self.__is_letter(self.current_char) or self.current_char.isalnum()):
            self.__read_char()

        return self.source[position: self.position]

    def __peek_char(self) -> str | None:
        if self.read_position >= len(self.source):
            return None
        return self.source[self.read_position]

    def next_token(self) -> Token:
        tok: Token = None

        self.__skip_whitespace()

        if self.current_char == '+':
            if self.__peek_char() == '=':
                self.__read_char()
                tok = self.__new_token(TokenType.PLUS_EQ, '+=' )
            else:
                tok = self.__new_token(TokenType.PLUS, self.current_char)
        elif self.current_char == '-':
            if self.__peek_char() == '>':
                self.__read_char()  # consome o '>'
                tok = self.__new_token(TokenType.EQ, "->")
            elif self.__peek_char() == '=':
                self.__read_char()
                tok = self.__new_token(TokenType.MINUS_EQ, '-=')
            else:
                tok = self.__new_token(TokenType.MINUS, self.current_char)
        elif self.current_char == '*':
            if self.__peek_char() == '=':
                self.__read_char()
                tok = self.__new_token(TokenType.ASTERISK_EQ, '*=')
            else:
                tok = self.__new_token(TokenType.ASTERISK, self.current_char)
        elif self.current_char == '/':
            if self.__peek_char() == '=':
                self.__read_char()
                tok = self.__new_token(TokenType.SLASH_EQ, '/=')
            else:
                tok = self.__new_token(TokenType.SLASH, self.current_char)
        elif self.current_char == '^':
            tok = self.__new_token(TokenType.POW, self.current_char)
        elif self.current_char == '%':
            if self.__peek_char() == '=':
                self.__read_char()
                tok = self.__new_token(TokenType.MODULUS_EQ, '%=')
            else:
                tok = self.__new_token(TokenType.MODULUS, self.current_char)
        elif self.current_char == '<':
            if self.__peek_char() == '=':
                ch = self.current_char
                self.__read_char()  # consome o '='
                tok = self.__new_token(TokenType.LT_EQ, ch + self.current_char)
            else:
                tok = self.__new_token(TokenType.LT, self.current_char)
        elif self.current_char == '>':
            if self.__peek_char() == '=':
                ch = self.current_char
                self.__read_char()  # consome o '='
                tok = self.__new_token(TokenType.GT_EQ, ch + self.current_char)
            else:
                tok = self.__new_token(TokenType.GT, self.current_char)
        elif self.current_char == '=':
            if self.__peek_char() == '=':
                ch = self.current_char
                self.__read_char()  # consome o '='
                tok = self.__new_token(TokenType.EQ_EQ, ch + self.current_char)
            else:
                tok = self.__new_token(TokenType.EQ, self.current_char)
        elif self.current_char == '!':
            if self.__peek_char() == '=':
                ch = self.current_char
                self.__read_char()  # consome o '='
                tok = self.__new_token(TokenType.NOT_EQ, ch + self.current_char)
            else:
                tok = self.__new_token(TokenType.BANG, self.current_char)
        elif self.current_char == '$':
            tok = self.__new_token(TokenType.COLON, self.current_char)
        elif self.current_char == ':':
            tok = self.__new_token(TokenType.ARROW, self.current_char)
        elif self.current_char == ',':
            tok = self.__new_token(TokenType.COMMA, self.current_char)
        elif self.current_char == ';':
            tok = self.__new_token(TokenType.SEMICOLON, self.current_char)
        elif self.current_char == '(':
            tok = self.__new_token(TokenType.LPAREN, self.current_char)
        elif self.current_char == ')':
            tok = self.__new_token(TokenType.RPAREN, self.current_char)
        elif self.current_char == '{':
            tok = self.__new_token(TokenType.LBRACE, self.current_char)
        elif self.current_char == '}':
            tok = self.__new_token(TokenType.RBRACE, self.current_char)
        elif self.current_char is None:
            tok = self.__new_token(TokenType.EOF, "")
        else:
            if self.current_char == '"':
                tok = self.__read_string()
                return tok
            if self.__is_letter(self.current_char):
                literal: str = self.__read_identifier()
                tt: TokenType = lookup_ident(literal)
                tok = self.__new_token(tt=tt, literal=literal)
                return tok
            elif self.__is_digit(self.current_char):
                tok = self.__read_number()
                return tok
            else:
                tok = self.__new_token(TokenType.ILLEGAL, self.current_char)

        self.__read_char()
        return tok
