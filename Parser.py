from Lexer import Lexer
from Token import Token, TokenType
from typing import Callable
from enum import Enum, auto

from AST import Statements, Expressions, Program, ExpressionStatement, InfixExpression, LetStatement, IntegerLiteral, FloatLiteral, IdentifierLiteral, AssignmentStatement
from AST import FunctionStatement, BlockStatement, ReturnStatement

# precedence types
class PrecedenceType(Enum):
    P_LOWEST = 0
    P_EQUALS = auto()
    P_LESSGREATER = auto()
    P_SUM = auto()
    P_PRODUCT = auto()
    P_EXPONENT = auto()
    P_PREFIX = auto()
    P_CALL = auto()
    P_INDEX = auto()

# precedence mapping
PRECEDENCE: dict[TokenType, PrecedenceType] = {
    TokenType.PLUS: PrecedenceType.P_SUM,
    TokenType.MINUS: PrecedenceType.P_SUM,
    TokenType.SLASH: PrecedenceType.P_PRODUCT,
    TokenType.ASTERISK: PrecedenceType.P_PRODUCT,
    TokenType.MODULUS: PrecedenceType.P_PRODUCT,
    TokenType.POW: PrecedenceType.P_EXPONENT
}

class Parser:
    def __init__(self, lexer: Lexer) -> None:
        self.lexer: Lexer = lexer

        self.errors: list[str] = []

        self.current_token: Token = None
        self.peek_token: Token = None

        self.prefix_parse_fns: dict[TokenType, Callable] = {
            TokenType.INT: self.__parse_int_literal,
            TokenType.FLOAT: self.__parse_float_literal,
            TokenType.LPAREN: self.__parse_grouped_expression,
            TokenType.IDENT: self.__parse_identifier
        } # -1
        self.infix_parse_fns: dict[TokenType, Callable] = {
            TokenType.PLUS: self.__parse_infix_expression,
            TokenType.MINUS: self.__parse_infix_expression,
            TokenType.SLASH: self.__parse_infix_expression,
            TokenType.ASTERISK: self.__parse_infix_expression,
            TokenType.MODULUS: self.__parse_infix_expression,
            TokenType.POW: self.__parse_infix_expression
        }  # 5 + 5

        self.__next_token()
        self.__next_token()

    # parser helpers
    def __next_token(self) -> None:
        self.current_token = self.peek_token
        self.peek_token = self.lexer.next_token()

    def __current_token_is(self, tt: TokenType) -> bool:
        return self.current_token.type == tt

    def __peek_token_is(self, tt: TokenType) -> bool:
        return self.peek_token.type == tt

    def __parse_identifier(self) -> Expressions:
        return IdentifierLiteral(value=self.current_token.literal)

    def __expect_peek(self, tt:TokenType) -> bool:
        if self.__peek_token_is(tt):
            self.__next_token()
            return True
        else:
            self.__peek_error(tt)
            return False

    def __current_precedence(self) -> PrecedenceType:
        prec: int | None = PRECEDENCE.get(self.current_token.type)
        if prec is None:
            return PrecedenceType.P_LOWEST
        return prec

    def __peek_precedence(self) -> PrecedenceType:
        prec: int | None = PRECEDENCE.get(self.peek_token.type)
        if prec is None:
            return PrecedenceType.P_LOWEST
        return prec

    def __peek_error(self, tt: TokenType) -> None:
        self.errors.append(f"EXPECTED NEXT TOKEN TO BE {tt}, GOT {self.peek_token.type} INSTEAD.")

    def __no_prefix_parse_fn_error(self, tt: TokenType):
        self.errors.append(f"NO PREFIX PARSE FUNCTION FOR {tt} FOUND.")

    # main execution
    def parse_program(self) -> Program:
        program = Program()

        while self.current_token.type != TokenType.EOF:
            stmt = self.__parse_statement()
            if stmt is not None:
                program.statements.append(stmt)

            self.__next_token()

        return program

    # statement methods
    def __parse_statement(self) -> Statements:
        if self.current_token.type == TokenType.IDENT and self.peek_token.type == TokenType.EQ:
            return self.__parse_assignment_statement()

        match self.current_token.type:
            case TokenType.LET:
                return self.__parse_let_statement()
            case TokenType.FN:
                return self.__parse_function_statement()
            case TokenType.RETURN:
                return self.__parse_return_statement()
            case _:
                return self.__parse_expression_statement()


    def __parse_expression_statement(self) -> ExpressionStatement:
        expr = self.__parse_expression(PrecedenceType.P_LOWEST)

        if self.__peek_token_is(TokenType.SEMICOLON):
            self.__next_token()

        stmt: ExpressionStatement = ExpressionStatement(expr=expr)

        return stmt

    def __parse_let_statement(self) -> LetStatement:
        # let a$int = 10;
        stmt: LetStatement = LetStatement()

        if not self.__expect_peek(TokenType.IDENT):
            return None

        stmt.name = IdentifierLiteral(value=self.current_token.literal)

        if not self.__expect_peek(TokenType.COLON):
            return None

        if not self.__expect_peek(TokenType.TYPE):
            return None

        stmt.value_type = self.current_token.literal

        if not self.__expect_peek(TokenType.EQ):
            return None

        self.__next_token()

        stmt.value = self.__parse_expression(PrecedenceType.P_LOWEST)

        while not self.__current_token_is(TokenType.SEMICOLON) and not self.__current_token_is(TokenType.EOF):
            self.__next_token()

        return stmt

    def __parse_function_statement(self) -> FunctionStatement:
        """Parse a function declaration.

        The expected syntax is roughly:

            fn name(param1$type, param2$type) : returnType { ... }

        We currently don't implement parameter parsing beyond consuming
        tokens until the closing parenthesis.  The earlier implementation
        incorrectly returned early when tokens were valid, which left
        the parser out of sync and caused the errors the user reported.
        """
        stmt: FunctionStatement = FunctionStatement()

        # function name
        if not self.__expect_peek(TokenType.IDENT):
            return None
        stmt.name = IdentifierLiteral(value=self.current_token.literal)

        # opening parenthesis for parameters
        if not self.__expect_peek(TokenType.LPAREN):
            return None

        # consume parameters (not yet supported).  We just need to
        # advance to the closing parenthesis to keep the parser in sync.
        stmt.parameters = []

        if self.__peek_token_is(TokenType.RPAREN):
            # empty parameter list: just consume ')'
            self.__next_token()
        else:
            # consume everything up to the ')'
            self.__next_token()
            while not self.__current_token_is(TokenType.RPAREN) and \
                  not self.__current_token_is(TokenType.EOF):
                self.__next_token()
            # current_token should now be RPAREN
            if not self.__current_token_is(TokenType.RPAREN):
                self.__peek_error(TokenType.RPAREN)
                return None
            # consume the closing paren
            self.__next_token()

        # return type arrow (colon in the source)
        if not self.__expect_peek(TokenType.ARROW):
            return None

        if not self.__expect_peek(TokenType.TYPE):
            return None
        stmt.return_type = self.current_token.literal

        if not self.__expect_peek(TokenType.LBRACE):
            return None

        stmt.body = self.__parse_block_statement()
        return stmt

    def __parse_return_statement(self) -> ReturnStatement:
        stmt: ReturnStatement = ReturnStatement()

        self.__next_token()

        stmt.return_value = self.__parse_expression(PrecedenceType.P_LOWEST)

        while not self.__current_token_is(TokenType.SEMICOLON) and not self.__current_token_is(TokenType.EOF):
            self.__next_token()

        return stmt

    def __parse_block_statement(self) -> BlockStatement:
        block: BlockStatement = BlockStatement()

        self.__next_token()

        while not self.__current_token_is(TokenType.RBRACE) and not self.__current_token_is(TokenType.EOF):
            stmt = self.__parse_statement()
            if stmt is not None:
                block.statements.append(stmt)
            self.__next_token()

        return block

    def __parse_assignment_statement(self) -> AssignmentStatement:
        stmt: AssignmentStatement = AssignmentStatement()

        stmt.ident = IdentifierLiteral(value=self.current_token.literal)

        self.__next_token()  # consume identifier
        self.__next_token()  # consume '->'(=)

        stmt.right_value = self.__parse_expression(PrecedenceType.P_LOWEST)

        self.__next_token()  # consume expression

        return stmt

    # expression methods
    def __parse_expression(self, precedence: PrecedenceType) -> Expressions:
        prefix_fn = self.prefix_parse_fns.get(self.current_token.type)

        if prefix_fn is None:
            self.__no_prefix_parse_fn_error(self.current_token.type)
            return None

        left_expr = prefix_fn()

        while (not self.__peek_token_is(TokenType.SEMICOLON)) and precedence.value < self.__peek_precedence().value:
            infix_fn = self.infix_parse_fns.get(self.peek_token.type)
            if infix_fn is None:
                return left_expr

            self.__next_token()
            left_expr = infix_fn(left_expr)

        return left_expr


    def __parse_infix_expression(self, left_node: Expressions) -> Expressions:
        infix_expr: InfixExpression = InfixExpression(left_node=left_node, operator=self.current_token.literal)

        precedence = self.__current_precedence()

        self.__next_token()

        infix_expr.right_node = self.__parse_expression(precedence)

        return infix_expr

    def __parse_grouped_expression(self) -> Expressions:
        self.__next_token()
        exp = self.__parse_expression(PrecedenceType.P_LOWEST)

        if not self.__expect_peek(TokenType.RPAREN):
            return None

        return exp


    # prefix methods
    def __parse_int_literal(self) -> Expressions:
        int_lit: IntegerLiteral = IntegerLiteral()

        try:
            int_lit.value = int(self.current_token.literal)
        except:
            self.errors.append(f"COULD NOT PARSE `{self.current_token.literal}` AS AN INTEGER.")
            return None

        return int_lit

    def __parse_float_literal(self) -> Expressions:
        float_lit: FloatLiteral = FloatLiteral()

        try:
            float_lit.value = float(self.current_token.literal)
        except:
            self.errors.append(f"COULD NOT PARSE `{self.current_token.literal}` AS AN FLOAT.")
            return None

        return float_lit

