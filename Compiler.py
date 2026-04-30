from llvmlite import ir

from AST import NodeType, Node, Statements, Expressions, Program, ExpressionStatement, LetStatement, InfixExpression, IntegerLiteral, FloatLiteral, IdentifierLiteral, AssignmentStatement
from AST import FunctionStatement, FunctionParameter, BlockStatement, ReturnStatement, CallExpression, BooleanLiteral, IfStatement
from AST import WhileStatement

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

        # stacks to keep track of current loop targets for break/continue
        self._loop_end_stack: list[ir.Block] = []
        self._loop_continue_stack: list[ir.Block] = []

        # counter for unique string constants
        self._str_const_count: int = 0

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

        # declare a C-like printf: int printf(i8*, i32)
        i8ptr = ir.IntType(8).as_pointer()
        # printf should accept a format string and varargs
        printf_ty = ir.FunctionType(ir.IntType(32), [i8ptr], var_arg=True)
        printf_func = ir.Function(self.module, printf_ty, name="printf")
        self.env.define("printf", printf_func, printf_func.function_type.return_type)

    def compile(self, node: Node) -> None:
        t = node.type()
        if t == NodeType.Program:
            self.__visit_program(node)
        elif t == NodeType.ExpressionStatement:
            self.__visit_expression_statement(node)
        elif t == NodeType.LetStatement:
            self.__visit_let_statement(node)
        elif t == NodeType.FunctionStatement:
            self.__visit_function_statement(node)
        elif t == NodeType.BlockStatement:
            self.__visit_block_statement(node)
        elif t == NodeType.ReturnStatement:
            self.__visit_return_statement(node)
        elif t == NodeType.AssignmentStatement:
            self.__visit_assign_statement(node)
        elif t == NodeType.IfStatement:
            self.__visit_if_statement(node)
        elif t == NodeType.WhileStatement:
            self.__visit_while_statement(node)
        elif t == NodeType.ForStatement:
            self.__visit_for_statement(node)
        elif t == NodeType.BreakStatement:
            self.__visit_break_statement(node)
        elif t == NodeType.ContinueStatement:
            self.__visit_continue_statement(node)
        elif t == NodeType.InfixExpression:
            self.__visit_infix_expression(node)
        elif t == NodeType.CallExpression:
            self.__visit_call_expression(node)
        # handle prefix and literal expressions by resolving their values
        elif t == NodeType.PrefixExpression:
            return self.__resolve_value(node)
        elif t == NodeType.IntegerLiteral or t == NodeType.FloatLiteral or t == NodeType.IdentifierLiteral:
            return self.__resolve_value(node)
        elif t == NodeType.BooleanLiteral or t == NodeType.StringLiteral:
            return self.__resolve_value(node)

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

    def __visit_while_statement(self, node: WhileStatement) -> None:
        condition = node.condition
        body = node.body

        # current function
        try:
            func = self.builder.block.function
        except Exception:
            raise Exception("While statement not inside a function")

        # create basic blocks
        loop_cond = func.append_basic_block("while_cond")
        loop_body = func.append_basic_block("while_body")
        loop_end = func.append_basic_block("while_end")

        # jump to condition first
        self.builder.branch(loop_cond)

        # condition
        self.builder.position_at_end(loop_cond)
        test, _ = self.__resolve_value(node=condition)
        self.builder.cbranch(test, loop_body, loop_end)

        # push loop targets for break/continue
        self._loop_end_stack.append(loop_end)
        self._loop_continue_stack.append(loop_cond)

        # body
        self.builder.position_at_end(loop_body)
        self.compile(body)
        # after body, jump back to condition
        if not self.builder.block.is_terminated:
            self.builder.branch(loop_cond)

        # pop loop targets
        self._loop_end_stack.pop()
        self._loop_continue_stack.pop()

        # continue after loop
        self.builder.position_at_end(loop_end)

    def __visit_for_statement(self, node: "ForStatement") -> None:
        init = node.init
        condition = node.condition
        post = node.post
        body = node.body

        try:
            func = self.builder.block.function
        except Exception:
            raise Exception("For statement not inside a function")

        # compile init
        if init is not None:
            self.compile(init)

        # create basic blocks
        loop_cond = func.append_basic_block("for_cond")
        loop_body = func.append_basic_block("for_body")
        loop_post = func.append_basic_block("for_post")
        loop_end = func.append_basic_block("for_end")

        # jump to condition first
        self.builder.branch(loop_cond)

        # condition
        self.builder.position_at_end(loop_cond)
        if condition is not None:
            test, _ = self.__resolve_value(node=condition)
            self.builder.cbranch(test, loop_body, loop_end)
        else:
            self.builder.branch(loop_body)

        # push loop targets
        self._loop_end_stack.append(loop_end)
        self._loop_continue_stack.append(loop_post)

        # body
        self.builder.position_at_end(loop_body)
        self.compile(body)
        if not self.builder.block.is_terminated:
            self.builder.branch(loop_post)

        # post
        self.builder.position_at_end(loop_post)
        if post is not None:
            self.compile(post)
        self.builder.branch(loop_cond)

        # pop loop targets
        self._loop_end_stack.pop()
        self._loop_continue_stack.pop()

        # continue after loop
        self.builder.position_at_end(loop_end)

    def __visit_break_statement(self, node: "BreakStatement") -> None:
        if len(self._loop_end_stack) == 0:
            raise Exception("'break' used outside of loop")

        target = self._loop_end_stack[-1]
        self.builder.branch(target)

        # create an unreachable continuation block to keep generating
        try:
            func = self.builder.block.function
            cont = func.append_basic_block("after_break")
            self.builder.position_at_end(cont)
        except Exception:
            pass

    def __visit_continue_statement(self, node: "ContinueStatement") -> None:
        if len(self._loop_continue_stack) == 0:
            raise Exception("'continue' used outside of loop")

        target = self._loop_continue_stack[-1]
        self.builder.branch(target)

        # create an unreachable continuation block to keep generating
        try:
            func = self.builder.block.function
            cont = func.append_basic_block("after_continue")
            self.builder.position_at_end(cont)
        except Exception:
            pass

    # expressions
    def __visit_infix_expression(self, node: InfixExpression) -> tuple[ir.Value, ir.Type]:
        operator: str = node.operator
        left_value, left_type = self.__resolve_value(node.left_node)
        right_value, right_type = self.__resolve_value(node.right_node)

        value = None
        Type = None
        if isinstance(right_type, ir.IntType) and isinstance(left_type, ir.IntType):
            Type = self.type_map['int']
            if operator == '+':
                value = self.builder.add(left_value, right_value)
            elif operator == '-':
                value = self.builder.sub(left_value, right_value)
            elif operator == '*':
                value = self.builder.mul(left_value, right_value)
            elif operator == '/':
                # promote integer division to float division so expressions
                # like `5 / 2` can produce `2.5` when used in float contexts.
                left_fp = self.builder.sitofp(left_value, ir.FloatType())
                right_fp = self.builder.sitofp(right_value, ir.FloatType())
                value = self.builder.fdiv(left_fp, right_fp)
                Type = ir.FloatType()
            elif operator == '%':
                value = self.builder.srem(left_value, right_value)
            elif operator == '**':
                # TODO:
                pass
            elif operator == '<':
                value = self.builder.icmp_signed('<', left_value, right_value)
                Type = ir.IntType(1)
            elif operator == '<=':
                value = self.builder.icmp_signed('<=', left_value, right_value)
                Type = ir.IntType(1)
            elif operator == '>':
                value = self.builder.icmp_signed('>', left_value, right_value)
                Type = ir.IntType(1)
            elif operator == '>=':
                value = self.builder.icmp_signed('>=', left_value, right_value)
                Type = ir.IntType(1)
            elif operator == '==':
                value = self.builder.icmp_signed('==', left_value, right_value)
                Type = ir.IntType(1)

        elif isinstance(right_type, ir.FloatType) and isinstance(left_type, ir.FloatType):
            Type = ir.FloatType()
            if operator == '+':
                value = self.builder.fadd(left_value, right_value)
            elif operator == '-':
                value = self.builder.fsub(left_value, right_value)
            elif operator == '*':
                value = self.builder.fmul(left_value, right_value)
            elif operator == '/':
                value = self.builder.fdiv(left_value, right_value)
            elif operator == '%':
                value = self.builder.frem(left_value, right_value)
            elif operator == '**':
                # TODO:
                pass
            elif operator == '<':
                value = self.builder.fcmp_ordered('<', left_value, right_value)
                Type = ir.IntType(1)
            elif operator == '<=':
                value = self.builder.fcmp_ordered('<=', left_value, right_value)
                Type = ir.IntType(1)
            elif operator == '>':
                value = self.builder.fcmp_ordered('>', left_value, right_value)
                Type = ir.IntType(1)
            elif operator == '>=':
                value = self.builder.fcmp_ordered('>=', left_value, right_value)
                Type = ir.IntType(1)
            elif operator == '==':
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

        func, ret_type = self.env.lookup(name)
        ret = self.builder.call(func, args)

        return ret, ret_type

    # helpers methods
    def __resolve_value(self, node: Expressions) -> tuple[ir.Value, ir.Type]:
        t = node.type()
        if t == NodeType.IntegerLiteral:
            node: IntegerLiteral = node
            value, Type = node.value, self.type_map['int']
            return ir.Constant(Type, value), Type
        elif t == NodeType.FloatLiteral:
            node: FloatLiteral = node
            value, Type = node.value, self.type_map['float']
            return ir.Constant(Type, value), Type
        elif t == NodeType.IdentifierLiteral:
            node: IdentifierLiteral = node
            ptr, Type = self.env.lookup(node.value)
            return self.builder.load(ptr), Type
        elif t == NodeType.BooleanLiteral:
            node: BooleanLiteral = node
            return ir.Constant(ir.IntType(1), int(node.value)), ir.IntType(1)
        elif t == NodeType.StringLiteral:
            node = node
            # create a global constant for the string
            raw: bytes = (node.value + "\0").encode('utf8')
            array_ty = ir.ArrayType(ir.IntType(8), len(raw))
            elems = [ir.Constant(ir.IntType(8), b) for b in raw]
            const = ir.Constant(array_ty, elems)

            name = f".str{self._str_const_count}"
            self._str_const_count += 1

            gvar = ir.GlobalVariable(self.module, array_ty, name=name)
            gvar.global_constant = True
            gvar.initializer = const

            # get i8* pointer to the first char
            ptr = self.builder.bitcast(gvar, ir.IntType(8).as_pointer())

            return ptr, ir.IntType(8).as_pointer()
        elif t == NodeType.InfixExpression:
            # typo fixed: should call __visit_infix_expression
            return self.__visit_infix_expression(node)
        elif t == NodeType.CallExpression:
            return self.__visit_call_expression(node)
        elif t == NodeType.PrefixExpression:
            # unary operators: '-' (negation) and '!' (logical not)
            # evaluate right side
            right_val, right_type = self.__resolve_value(node.right_node)

            if right_val is None or right_type is None:
                return None

            op = node.operator
            if op == '-':
                if isinstance(right_type, ir.IntType):
                    zero = ir.Constant(self.type_map['int'], 0)
                    return self.builder.sub(zero, right_val), self.type_map['int']
                elif isinstance(right_type, ir.FloatType):
                    zero = ir.Constant(self.type_map['float'], 0.0)
                    return self.builder.fsub(zero, right_val), self.type_map['float']
            elif op == '!':
                # logical not: compare to zero for boolean
                if isinstance(right_type, ir.IntType):
                    zero = ir.Constant(ir.IntType(1), 0)
                    val = self.builder.icmp_signed('==', right_val, zero)
                    return val, ir.IntType(1)

            return None
