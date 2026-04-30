from Lexer import Lexer
from Token import Token, TokenType
from typing import Callable
from enum import Enum, auto

from AST import Statements, Expressions, Program, ExpressionStatement, InfixExpression, LetStatement, IntegerLiteral, FloatLiteral, IdentifierLiteral, AssignmentStatement
from AST import IfStatement, BooleanLiteral, CallExpression, WhileStatement
from AST import StringLiteral
from AST import FunctionStatement, BlockStatement, ReturnStatement, FunctionParameter
from AST import ForStatement, BreakStatement, ContinueStatement, PrefixExpression

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
    TokenType.POW: PrecedenceType.P_EXPONENT,
    TokenType.EQ_EQ: PrecedenceType.P_EQUALS,
    TokenType.NOT_EQ: PrecedenceType.P_EQUALS,
    TokenType.LT: PrecedenceType.P_LESSGREATER,
    TokenType.GT: PrecedenceType.P_LESSGREATER,
    TokenType.LT_EQ: PrecedenceType.P_LESSGREATER,
    TokenType.GT_EQ: PrecedenceType.P_LESSGREATER,
    TokenType.LPAREN: PrecedenceType.P_CALL
}

# tokens that act as assignment operators
ASSIGN_TOKENS = {TokenType.EQ, TokenType.PLUS_EQ, TokenType.MINUS_EQ, TokenType.ASTERISK_EQ, TokenType.SLASH_EQ, TokenType.MODULUS_EQ}

class Parser:
    def __init__(self, lexer: Lexer) -> None:
        self.lexer: Lexer = lexer

        self.errors: list[str] = []

        self.current_token: Token = None
        self.peek_token: Token = None

        self.prefix_parse_fns: dict[TokenType, Callable] = {
            TokenType.INT: self.__parse_int_literal,
            TokenType.FLOAT: self.__parse_float_literal,
            TokenType.STRING: self.__parse_string_literal,
            TokenType.LPAREN: self.__parse_grouped_expression,
            TokenType.IDENT: self.__parse_identifier,
            TokenType.MINUS: self.__parse_prefix_expression,
            TokenType.PLUS: self.__parse_prefix_expression,
            TokenType.BANG: self.__parse_prefix_expression,
            TokenType.IF: self.__parse_if_expression,
            TokenType.TRUE: self.__parse_boolean_literal,
            TokenType.FALSE: self.__parse_boolean_literal
        } # -1
        self.infix_parse_fns: dict[TokenType, Callable] = {
            TokenType.PLUS: self.__parse_infix_expression,
            TokenType.MINUS: self.__parse_infix_expression,
            TokenType.SLASH: self.__parse_infix_expression,
            TokenType.ASTERISK: self.__parse_infix_expression,
            TokenType.MODULUS: self.__parse_infix_expression,
            TokenType.POW: self.__parse_infix_expression,
            TokenType.EQ_EQ: self.__parse_infix_expression,
            TokenType.NOT_EQ: self.__parse_infix_expression,
            TokenType.LT: self.__parse_infix_expression,
            TokenType.GT: self.__parse_infix_expression,
            TokenType.LT_EQ: self.__parse_infix_expression,
            TokenType.GT_EQ: self.__parse_infix_expression,
            TokenType.LPAREN: self.__parse_call_expression
        }

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
        ASSIGN_TOKENS = {TokenType.EQ, TokenType.PLUS_EQ, TokenType.MINUS_EQ, TokenType.ASTERISK_EQ, TokenType.SLASH_EQ, TokenType.MODULUS_EQ}
        if self.current_token.type == TokenType.IDENT and self.peek_token.type in ASSIGN_TOKENS:
            return self.__parse_assignment_statement()

        if self.current_token.type == TokenType.LET:
            return self.__parse_let_statement()
        elif self.current_token.type == TokenType.FN:
            return self.__parse_function_statement()
        elif self.current_token.type == TokenType.WHILE:
            return self.__parse_while_statement()
        elif self.current_token.type == TokenType.FOR:
            return self.__parse_for_statement()
        elif self.current_token.type == TokenType.BREAK:
            return self.__parse_break_statement()
        elif self.current_token.type == TokenType.CONTINUE:
            return self.__parse_continue_statement()
        elif self.current_token.type == TokenType.RETURN:
            return self.__parse_return_statement()
        else:
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
        stmt.parameters = self.__parse_function_parameters()
        # At this point `__parse_function_parameters` should have
        # consumed the closing ')' and positioned the parser so that
        # `peek_token` is the return-type arrow (':' in source).
        # Proceed to parse the return type and function body.
        if not self.__expect_peek(TokenType.ARROW):
            return None

        if not self.__expect_peek(TokenType.TYPE):
            return None
        stmt.return_type = self.current_token.literal

        if not self.__expect_peek(TokenType.LBRACE):
            return None
        stmt.body = self.__parse_block_statement()



        return stmt

    def __parse_function_parameters(self) -> list[FunctionParameter]:
        params: list[FunctionParameter] = []

        if self.__peek_token_is(TokenType.RPAREN):
            self.__next_token()
            return params

        self.__next_token()

        first_param: FunctionParameter = FunctionParameter(name=IdentifierLiteral(value=self.current_token.literal))

        if not self.__expect_peek(TokenType.COLON):
            return None

        self.__next_token()

        # store the parameter type string in `param_type` to avoid
        # shadowing the `type()` method defined on AST nodes
        first_param.param_type = self.current_token.literal
        params.append(first_param)

        while self.__peek_token_is(TokenType.COMMA):
            self.__next_token()  # consume comma
            self.__next_token()  # move to next parameter name

            param: FunctionParameter = FunctionParameter(name=IdentifierLiteral(value=self.current_token.literal))

            if not self.__expect_peek(TokenType.COLON):
                return None

            self.__next_token()

            param.param_type = self.current_token.literal
            params.append(param)



        # current_token may already be RPAREN (assignment parsed it),
        # so handle both cases
        if not self.__current_token_is(TokenType.RPAREN):
            if self.__peek_token_is(TokenType.RPAREN):
                self.__next_token()
            else:
                self.__peek_error(TokenType.RPAREN)
                return None

        return params

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

        # consume identifier -> now current_token will be the assignment operator
        self.__next_token()
        op_token = self.current_token

        # move to start of right-hand expression
        self.__next_token()

        right = self.__parse_expression(PrecedenceType.P_LOWEST)

        # if this was a compound assignment like '+=' build an infix expression
        if op_token.type == TokenType.PLUS_EQ:
            stmt.right_value = InfixExpression(left_node=IdentifierLiteral(value=stmt.ident.value), operator='+', right_node=right)
        elif op_token.type == TokenType.MINUS_EQ:
            stmt.right_value = InfixExpression(left_node=IdentifierLiteral(value=stmt.ident.value), operator='-', right_node=right)
        elif op_token.type == TokenType.ASTERISK_EQ:
            stmt.right_value = InfixExpression(left_node=IdentifierLiteral(value=stmt.ident.value), operator='*', right_node=right)
        elif op_token.type == TokenType.SLASH_EQ:
            stmt.right_value = InfixExpression(left_node=IdentifierLiteral(value=stmt.ident.value), operator='/', right_node=right)
        elif op_token.type == TokenType.MODULUS_EQ:
            stmt.right_value = InfixExpression(left_node=IdentifierLiteral(value=stmt.ident.value), operator='%', right_node=right)
        else:
            # simple assignment ('=' or '->')
            stmt.right_value = right

        # advance until semicolon, RPAREN or EOF to leave parser in consistent state
        while (not self.__current_token_is(TokenType.SEMICOLON)
               and not self.__current_token_is(TokenType.RPAREN)
               and not self.__current_token_is(TokenType.EOF)):
            self.__next_token()

        return stmt

    def __parse_if_expression(self) -> IfStatement:
        condition: Expressions = None
        consequence: BlockStatement = None
        alternative: BlockStatement = None

        self.__next_token()  # consume 'if'
        condition = self.__parse_expression(PrecedenceType.P_LOWEST)

        if not self.__expect_peek(TokenType.LBRACE):
            return None

        consequence = self.__parse_block_statement()

        # if there's an `else`, it will be the next token after the closing `}`
        if self.__peek_token_is(TokenType.ELSE):
            self.__next_token()  # consume 'else'

            if not self.__expect_peek(TokenType.LBRACE):
                return None

            alternative = self.__parse_block_statement()

        return IfStatement(condition=condition, consequence=consequence, alternative=alternative)

    def __parse_while_statement(self) -> WhileStatement:
        condition: Expressions = None
        body: BlockStatement = None

        self.__next_token()  # consume 'while'
        condition = self.__parse_expression(PrecedenceType.P_LOWEST)

        if not self.__expect_peek(TokenType.LBRACE):
            return None

        body = self.__parse_block_statement()

        return WhileStatement(condition=condition, body=body)

    def __parse_break_statement(self) -> BreakStatement:
        # consume 'break' and advance to semicolon
        self.__next_token()

        while not self.__current_token_is(TokenType.SEMICOLON) and not self.__current_token_is(TokenType.EOF):
            self.__next_token()

        return BreakStatement()

    def __parse_continue_statement(self) -> ContinueStatement:
        # consume 'continue' and advance to semicolon
        self.__next_token()

        while not self.__current_token_is(TokenType.SEMICOLON) and not self.__current_token_is(TokenType.EOF):
            self.__next_token()

        return ContinueStatement()

    def __parse_for_statement(self) -> ForStatement:
        # expect '(' after 'for'
        if not self.__expect_peek(TokenType.LPAREN):
            return None

        # move into the parentheses
        self.__next_token()


        init = None
        # parse init statement if present
        if not self.__current_token_is(TokenType.SEMICOLON):
            if self.current_token.type == TokenType.LET:
                init = self.__parse_let_statement()

            elif self.current_token.type == TokenType.IDENT and self.peek_token.type in ASSIGN_TOKENS:
                init = self.__parse_assignment_statement()

            else:
                init = self.__parse_expression_statement()


        # ensure current token is semicolon; if parse left it at semicolon it's fine,
        # otherwise try to advance to semicolon
        if not self.__current_token_is(TokenType.SEMICOLON):
            if self.__peek_token_is(TokenType.SEMICOLON):
                self.__next_token()
            else:
                self.__peek_error(TokenType.SEMICOLON)
                return None

        # move to first token of condition
        self.__next_token()


        condition = None
        # condition is empty if current token is a semicolon
        if not self.__current_token_is(TokenType.SEMICOLON):
            condition = self.__parse_expression(PrecedenceType.P_LOWEST)

        # expect semicolon separating condition and post
        # accept either `;` or `,` between condition and post (some tests use comma)
        if self.__peek_token_is(TokenType.SEMICOLON) or self.__peek_token_is(TokenType.COMMA):
            self.__next_token()
        else:
            self.__peek_error(TokenType.SEMICOLON)
            return None



        # move to first token of post
        self.__next_token()


        post = None
        if not self.__current_token_is(TokenType.RPAREN):
            if self.current_token.type == TokenType.IDENT and self.peek_token.type in ASSIGN_TOKENS:
                post = self.__parse_assignment_statement()
            else:
                post = self.__parse_expression_statement()


        # current_token may already be RPAREN (assignment parsed it), handle both
        if not self.__current_token_is(TokenType.RPAREN):
            if self.__peek_token_is(TokenType.RPAREN):
                self.__next_token()
            else:
                self.__peek_error(TokenType.RPAREN)
                return None

        if not self.__expect_peek(TokenType.LBRACE):
            return None

        body = self.__parse_block_statement()



        return ForStatement(init=init, condition=condition, post=post, body=body)

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
        # Handle postfix increment/decrement patterns like `i++` and `i--`.
        # When the parser reaches the first '+' or '-' and the next token
        # is the same, interpret as a postfix update and turn it into an
        # AssignmentStatement (e.g. `i += 1`). This keeps changes local
        # and compatible with existing compiler handling of assignments.
        from AST import AssignmentStatement, IntegerLiteral

        # detect postfix ++
        if self.current_token.type == TokenType.PLUS and self.peek_token.type == TokenType.PLUS:
            # consume the second '+'
            if isinstance(left_node, IdentifierLiteral):
                stmt: AssignmentStatement = AssignmentStatement()
                stmt.ident = IdentifierLiteral(value=left_node.literal if hasattr(left_node, 'literal') else left_node.value)
                one = IntegerLiteral(value=1)
                stmt.right_value = InfixExpression(left_node=IdentifierLiteral(value=stmt.ident.value), operator='+', right_node=one)
                self.__next_token()
                return stmt
            else:
                self.errors.append("POSTFIX '++' APPLIED TO NON-IDENTIFIER.")
                self.__next_token()
                return left_node

        # detect postfix --
        if self.current_token.type == TokenType.MINUS and self.peek_token.type == TokenType.MINUS:
            if isinstance(left_node, IdentifierLiteral):
                stmt: AssignmentStatement = AssignmentStatement()
                stmt.ident = IdentifierLiteral(value=left_node.literal if hasattr(left_node, 'literal') else left_node.value)
                one = IntegerLiteral(value=1)
                stmt.right_value = InfixExpression(left_node=IdentifierLiteral(value=stmt.ident.value), operator='-', right_node=one)
                self.__next_token()
                return stmt
            else:
                self.errors.append("POSTFIX '--' APPLIED TO NON-IDENTIFIER.")
                self.__next_token()
                return left_node

        # default infix handling
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

    def __parse_call_expression(self, fun: Expressions) -> CallExpression:
        expr: CallExpression = CallExpression(function=fun)
        expr.arguments = self.__parse_expression_list(TokenType.RPAREN)

        return expr

    def __parse_expression_list(self, end: TokenType) -> list[Expressions]:
        args: list[Expressions] = []

        if self.__peek_token_is(end):
            self.__next_token()
            return args

        self.__next_token()
        args.append(self.__parse_expression(PrecedenceType.P_LOWEST))

        while self.__peek_token_is(TokenType.COMMA):
            self.__next_token()  # consume comma
            self.__next_token()  # move to next expression
            args.append(self.__parse_expression(PrecedenceType.P_LOWEST))

        if not self.__expect_peek(end):
            return None

        return args

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

    def __parse_boolean_literal(self) -> Expressions:
        return BooleanLiteral(value=self.__current_token_is(TokenType.TRUE))

    def __parse_string_literal(self) -> Expressions:
        s = StringLiteral()
        s.value = self.current_token.literal
        return s

    def __parse_prefix_expression(self) -> Expressions:
        expr = PrefixExpression(operator=self.current_token.literal)

        # move to the expression after the prefix operator
        self.__next_token()

        expr.right_node = self.__parse_expression(PrecedenceType.P_PREFIX)

        return expr



