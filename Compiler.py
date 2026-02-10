from llvmlite import ir

from AST import NodeType, Node, Statements, Expressions, Program, ExpressionStatement, InfixExpression, IntegerLiteral, FloatLiteral

class Compiler:
    def __init__(self) -> None:
        self.type_map: dict[str, ir.Type] = {
            'int': ir.IntType(32),
            'float': ir.FloatType()
        }

        self.module: ir.Module = ir.Module('main')

        self.builder: ir.IRBuilder = ir.IRBuilder()

    def compile(self, node: Node) -> None:
        match node.type():
            case NodeType.Program:
                self.__visit_program(node)

            # statements
            case NodeType.ExpressionStatement:
                self.__visit_expression_statement(node)

            # expressions
            case NodeType.InfixExpression:
                self.__visit_infix_expression(node)

    # visit method
    def __visit_program(self, node: Program) -> None:
        func_main: str = "main"
        param_types: list[ir.Type] = []
        return_type: ir.Type = self.type_map["int"]

        fnty = ir.FunctionType(return_type, param_types)
        func = ir.Function(self.module, fnty, name=func_main)

        block = func.append_basic_block(f"{func_main}_entry")

        self.builder = ir.IRBuilder(block)

        for stmt in node.statements:
            self.compile(stmt)

        return_value: ir_Constant = ir.Constant(self.type_map["int"], 69)
        self.builder.ret(return_value)


    # statements
    def __visit_expression_statement(self, node: ExpressionStatement) -> None:
        self.compile(node.expr)

    # expressions
    def __visit_infix_expression(self, node: InfixExpression) -> None:
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
                case 'x':
                    value = self.builder.mul(left_value, right_value)
                case '/':
                    value = self.builder.sdiv(left_value, right_value)
                case '%':
                    value = self.builder.srem(left_value, right_value)
                case 'e':
                    # TODO:
                    pass
        elif isinstance(right_type, ir.FloatType) and isinstance(left_type, ir.FloatType):
            Type = ir.FloatType()
            match operator:
                case '+':
                    value = self.builder.fadd(left_value, right_value)
                case '-':
                    value = self.builder.fsub(left_value, right_value)
                case 'x':
                    value = self.builder.fmul(left_value, right_value)
                case '/':
                    value = self.builder.fdiv(left_value, right_value)
                case '%':
                    value = self.builder.frem(left_value, right_value)
                case 'e':
                    # TODO:
                    pass

        return value, Type

    # helpers methods
    def __resolve_value(self, node: Expressions, value_type: str = None) -> tuple[ir.Value, ir.Type]:
        match node.type():
            case NodeType.IntegerLiteral:
                node: IntegerLiteral = node
                value, Type = node.value, self.type_map['int' if value_type is None else value_type]
                return ir.Constant(Type, value), Type
            case NodeType.FloatLiteral:
                node: FloatLiteral = node
                value, Type = node.value, self.type_map['float' if value_type is None else value_type]
                return ir.Constant(Type, value), Type

            # expression value
            case NodeType.InfixExpression:
               return self.__visitc_infix_expression(node)
