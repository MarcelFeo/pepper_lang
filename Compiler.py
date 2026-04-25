from llvmlite import ir

from AST import NodeType, Node, Statements, Expressions, Program, ExpressionStatement, LetStatement, InfixExpression, IntegerLiteral, FloatLiteral, IdentifierLiteral, AssignmentStatement
from AST import FunctionStatement, FunctionParameter, BlockStatement, ReturnStatement, CallExpression, BooleanLiteral, IfStatement

from Environment import Environment

class Compiler:
    def __init__(self) -> None:
        self.type_map: dict[str, ir.Type] = {
            'int': ir.IntType(32),
            'float': ir.FloatType(),
            'bool': ir.IntType(1)
        }

        self.module: ir.Module = ir.Module('main')

        self.builder: ir.IRBuilder = ir.IRBuilder()

        self.env: Environment = Environment()

        self.errors: list[str] = []

        self.__initialize_builtins()

    def __initialize_builtins(self) -> None:
        def __init_booleans() -> tuple[ir.GlobalVariable, ir.GlobalVariable]:
            bool_type: ir.Type = self.type_map['bool']

            true_var = ir.GlobalVariable(self.module, bool_type, name="true")
            true_var.initializer = ir.Constant(bool_type, 1)
            true_var.global_constant = True

            false_var = ir.GlobalVariable(self.module, bool_type, name="false")
            false_var.initializer = ir.Constant(bool_type, 0)
            false_var.global_constant = True

            return true_var, false_var

        true_var, false_var = __init_booleans()
        self.env.define("true", true_var, true_var.type)
        self.env.define("false", false_var, false_var.type)

    def compile(self, node: Node) -> None:
        match node.type():
            case NodeType.Program:
                self.__visit_program(node)

            # statements
            case NodeType.ExpressionStatement:
                self.__visit_expression_statement(node)
            case NodeType.LetStatement:
                self.__visit_let_statement(node)
            case NodeType.FunctionStatement:
                self.__visit_function_statement(node)
            case NodeType.BlockStatement:
                self.__visit_block_statement(node)
            case NodeType.ReturnStatement:
                self.__visit_return_statement(node)
            case NodeType.AssignmentStatement:
                self.__visit_assign_statement(node)
            case NodeType.IfStatement:
                self.__visit_if_statement(node)

            # expressions
            case NodeType.InfixExpression:
                self.__visit_infix_expression(node)
            case NodeType.CallExpression:
                self.__visit_call_expression(node)

    # visit method
    def __visit_program(self, node: Program) -> None:
        for stmt in node.statements:
            self.compile(stmt)


    # statements
    def __visit_expression_statement(self, node: ExpressionStatement) -> None:
        self.compile(node.expr)

    def __visit_let_statement(self, node: LetStatement) -> None:
        name: str = node.name.value
        value: Expression = node.value
        value_type: str = node.value_type # TODO: implement

        value, Type = self.__resolve_value(node=value)

        if self.env.lookup(name) is None:
            # define and allocate the variable
            ptr = self.builder.alloca(Type)

            # storing the value to the ptr
            self.builder.store(value, ptr)

            # add the pointer (not the value) to the environment so future
            # lookups return a pointer suitable for `builder.load`.
            self.env.define(name, ptr, Type)
        else:
            ptr, _ = self.env.lookup(name)
            self.builder.store(value, ptr)

    def __visit_function_statement(self, node: FunctionStatement) -> None:
        name: str = node.name.value
        body: BlockStatement = node.body
        params: list[FunctionParameter] = node.parameters

        param_names: list[str] = [param.name.value for param in params]

        param_types: list[ir.Type] = []
        for param in params:
            if param.param_type is None:
                raise Exception(f"Parameter '{param.name.value}' missing type")
            param_types.append(self.type_map[param.param_type])

        return_type: ir.Type = self.type_map[node.return_type]

        fnty = ir.FunctionType(return_type, param_types)
        func = ir.Function(self.module, fnty, name=name)

        block = func.append_basic_block(f"{name}_entry")

        previous_builder = self.builder

        self.builder = ir.IRBuilder(block)

        previous_env = self.env

        # create a new child environment for the function body
        # constructor uses `parent` (not `outer`) as per Environment.py
        self.env = Environment(parent=previous_env)
        # bind parameters: create stack slots and store incoming args
        for i, param in enumerate(params):
            arg = func.args[i]
            arg.name = param.name.value
            ptr = self.builder.alloca(param_types[i])
            self.builder.store(arg, ptr)
            self.env.define(arg.name, ptr, param_types[i])

        # expose the function itself in the environment
        self.env.define(name, func, return_type)

        self.compile(body)

        self.env = previous_env
        self.env.define(name, func, return_type)

        self.builder = previous_builder

    def __visit_block_statement(self, node: BlockStatement) -> None:
        for stmt in node.statements:
            self.compile(stmt)

    def __visit_return_statement(self, node: ReturnStatement) -> None:
        value, Type = self.__resolve_value(node.return_value)
        # Ensure the returned LLVM value matches the function's return type.
        # If not, try to perform a safe cast (e.g. int -> float).
        expected_ret_type = None
        try:
            expected_ret_type = self.builder.block.function.function_type.return_type
        except Exception:
            expected_ret_type = None

        if expected_ret_type is not None and Type is not None and Type != expected_ret_type:
            # int -> float
            if isinstance(Type, ir.IntType) and isinstance(expected_ret_type, ir.FloatType):
                value = self.builder.sitofp(value, expected_ret_type)
                Type = expected_ret_type
            # float -> int
            elif isinstance(Type, ir.FloatType) and isinstance(expected_ret_type, ir.IntType):
                value = self.builder.fptosi(value, expected_ret_type)
                Type = expected_ret_type

        self.builder.ret(value)

    def __visit_assign_statement(self, node: AssignmentStatement) -> None:
        name: str = node.ident.value
        value: Expression = node.right_value

        value, Type = self.__resolve_value(node=value)

        if self.env.lookup(name) is None:
            raise Exception(f"Undefined variable '{name}'")

        ptr, _ = self.env.lookup(name)
        self.builder.store(value, ptr)

    def __visit_if_statement(self, node: Statements) -> None:
        condition = node.condition
        consequence = node.consequence
        alternative = node.alternative

        test, _ = self.__resolve_value(node=condition)

        # If there is an alternative block, emit an if/else; otherwise
        # emit a simple if (if-then) without an else branch.
        if alternative is not None:
            with self.builder.if_else(test) as (true, otherwise):
                with true:
                    self.compile(consequence)

                with otherwise:
                    self.compile(alternative)
        else:
            with self.builder.if_then(test):
                self.compile(consequence)

    # expressions
    def __visit_infix_expression(self, node: InfixExpression) -> tuple[ir.Value, ir.Type]:
        operator: str = node.operator
        left_value, left_type = self.__resolve_value(node.left_node)
        right_value, right_type = self.__resolve_value(node.right_node)

        value = None
        Type = None
        if isinstance(right_type, ir.IntType) and isinstance(left_type, ir.IntType):
            Type = self.type_map['int']
            match operator:
                case '+':
                    value = self.builder.add(left_value, right_value)
                case '-':
                    value = self.builder.sub(left_value, right_value)
                case '*':
                    value = self.builder.mul(left_value, right_value)
                case '/':
                    # promote integer division to float division so expressions
                    # like `5 / 2` can produce `2.5` when used in float contexts.
                    left_fp = self.builder.sitofp(left_value, ir.FloatType())
                    right_fp = self.builder.sitofp(right_value, ir.FloatType())
                    value = self.builder.fdiv(left_fp, right_fp)
                    Type = ir.FloatType()
                case '%':
                    value = self.builder.srem(left_value, right_value)
                case '**':
                    # TODO:
                    pass
                case '<':
                    value = self.builder.icmp_signed('<', left_value, right_value)
                    Type = ir.IntType(1)
                case '<=':
                    value = self.builder.icmp_signed('<=', left_value, right_value)
                    Type = ir.IntType(1)
                case '>':
                    value = self.builder.icmp_signed('>', left_value, right_value)
                    Type = ir.IntType(1)
                case '>=':
                    value = self.builder.icmp_signed('>=', left_value, right_value)
                    Type = ir.IntType(1)
                case '==':
                    value = self.builder.icmp_signed('==', left_value, right_value)
                    Type = ir.IntType(1)

        elif isinstance(right_type, ir.FloatType) and isinstance(left_type, ir.FloatType):
            Type = ir.FloatType()
            match operator:
                case '+':
                    value = self.builder.fadd(left_value, right_value)
                case '-':
                    value = self.builder.fsub(left_value, right_value)
                case '*':
                    value = self.builder.fmul(left_value, right_value)
                case '/':
                    value = self.builder.fdiv(left_value, right_value)
                case '%':
                    value = self.builder.frem(left_value, right_value)
                case '**':
                    # TODO:
                    pass
                case '<':
                    value = self.builder.fcmp_ordered('<', left_value, right_value)
                    Type = ir.IntType(1)
                case '<=':
                    value = self.builder.fcmp_ordered('<=', left_value, right_value)
                    Type = ir.IntType(1)
                case '>':
                    value = self.builder.fcmp_ordered('>', left_value, right_value)
                    Type = ir.IntType(1)
                case '>=':
                    value = self.builder.fcmp_ordered('>=', left_value, right_value)
                    Type = ir.IntType(1)
                case '==':
                    value = self.builder.fcmp_ordered('==', left_value, right_value)
                    Type = ir.IntType(1)

        return value, Type

    def __visit_call_expression(self, node: CallExpression) -> None:
        name: str = node.function.value
        parameters: list[Expressions] = node.arguments

        args = []
        types = []

        for arg_node in parameters:
            val, Type = self.__resolve_value(arg_node)
            args.append(val)
            types.append(Type)

        match name:
            case _:
                func, ret_type = self.env.lookup(name)
                ret = self.builder.call(func, args)

        return ret, ret_type

    # helpers methods
    def __resolve_value(self, node: Expressions) -> tuple[ir.Value, ir.Type]:
        match node.type():
            case NodeType.IntegerLiteral:
                node: IntegerLiteral = node
                value, Type = node.value, self.type_map['int']
                return ir.Constant(Type, value), Type
            case NodeType.FloatLiteral:
                node: FloatLiteral = node
                value, Type = node.value, self.type_map['float']
                return ir.Constant(Type, value), Type
            case NodeType.IdentifierLiteral:
                node: IdentifierLiteral = node
                ptr, Type = self.env.lookup(node.value)
                return self.builder.load(ptr), Type
            case NodeType.BooleanLiteral:
                node: BooleanLiteral = node
                return ir.Constant(ir.IntType(1), int(node.value)), ir.IntType(1)

            # expression value
            case NodeType.InfixExpression:
                # typo fixed: should call __visit_infix_expression
                return self.__visit_infix_expression(node)
            case NodeType.CallExpression:
                return self.__visit_call_expression(node)
