from abc import ABC, abstractmethod
from enum import Enum

class NodeType(Enum):
    Program = "Program"

    # statements
    ExpressionStatement = "ExpressionStatement"
    LetStatement = "LetStatement"
    FunctionStatement = "FunctionStatement"
    BlockStatement = "BlockStatement"
    ReturnStatement = "ReturnStatement"
    AssignmentStatement = "AssignmentStatement"
    IfStatement = "IfStatement"

    # expressions
    InfixExpression = "InfixExpression"

    # literals
    IntegerLiteral = "IntegerLiteral"
    FloatLiteral = "FloatLiteral"
    IdentifierLiteral = "IdentifierLiteral"
    BooleanLiteral = "BooleanLiteral"

class Node(ABC):
    @abstractmethod
    def type(self) -> NodeType:
        pass

    @abstractmethod
    def json(self) -> dict:
        pass

class Statements(Node):
    pass

class Expressions(Node):
    pass

class Program(Node):
    def __init__(self) -> None:
        self.statements: list[Statements] = []

    def type(self) -> NodeType:
        return NodeType.Program

    def json(self) -> dict:
        return {
            "type": self.type().value,
            "statements": [stmt.json() for stmt in self.statements]
        }

# statements
class ExpressionStatement(Statements):
    def __init__(self, expr: Expressions = None) -> None:
        self.expr: Expression = expr

    def type(self) -> NodeType:
        return NodeType.ExpressionStatement

    def json(self) -> dict:
        return {
            "type": self.type().value,
            "expr": self.expr.json()
        }

class LetStatement(Statements):
    def __init__(self, name: Expressions = None, value: Expressions = None, value_type: str = None) -> None:
        self.name = name
        self.value = value
        self.value_type = value_type

    def type(self) -> NodeType:
        return NodeType.LetStatement

    def json(self) -> dict:
        return {
            "type": self.type().value,
            "name": self.name.json(),
            "value": self.value.json(),
            "value_type": self.value_type
        }

class BlockStatement(Statements):
    def __init__(self, statements: list[Statements] = None) -> None:
        # allow caller to supply an initial list or create an empty one
        self.statements: list[Statements] = statements if (statements is not None) else []

    def type(self) -> NodeType:
        return NodeType.BlockStatement

    def json(self) -> dict:
        return {
            "type": self.type().value,
            "statements": [stmt.json() for stmt in self.statements]
        }

class ReturnStatement(Statements):
    def __init__(self, return_value: Expressions = None) -> None:
        self.return_value = return_value

    def type(self) -> NodeType:
        return NodeType.ReturnStatement

    def json(self) -> dict:
        return {
            "type": self.type().value,
            "value": self.return_value.json() if self.return_value is not None else None
        }

class FunctionStatement(Statements):
    def __init__(self, name: Expressions = None, parameters: list[Expressions] = None, body: BlockStatement = None, return_type: str = None) -> None:
        self.name = name
        self.parameters = parameters if parameters is not None else []
        self.body = body
        self.return_type = return_type

    def type(self) -> NodeType:
        return NodeType.FunctionStatement

    def json(self) -> dict:
        return {
            "type": self.type().value,
            "name": self.name.json(),
            "parameters": [param.json() for param in self.parameters],
            "body": self.body.json(),
            "return_type": self.return_type
        }

class AssignmentStatement(Statements):
    def __init__(self, ident: Expressions = None, right_value: Expressions = None) -> None:
        self.ident = ident
        self.right_value = right_value

    def type(self) -> NodeType:
        return NodeType.AssignmentStatement

    def json(self) -> dict:
        return {
            "type": self.type().value,
            "ident": self.ident.json(),
            "right_value": self.right_value.json()
        }

class IfStatement(Statements):
    def __init__(self, condition: Expressions = None, consequence: BlockStatement = None, alternative: BlockStatement = None) -> None:
        self.condition = condition
        self.consequence = consequence
        self.alternative = alternative

    def type(self) -> NodeType:
        return NodeType.IfStatement

    def json(self) -> dict:
        return {
            "type": self.type().value,
            "condition": self.condition.json(),
            "consequence": self.consequence.json(),
            "alternative": self.alternative.json() if self.alternative is not None else None
        }

# expressions
class InfixExpression(Expressions):
    def __init__(self, left_node: Expressions, operator: str, right_node: Expressions = None) -> None:
        self.left_node: Expression = left_node
        self.operator: str = operator
        self.right_node: Expression = right_node

    def type(self) -> NodeType:
        return NodeType.InfixExpression

    def json(self) -> dict:
        return {
            "type": self.type().value,
            "left_node": self.left_node.json(),
            "operator": self.operator,
            "right_node": self.right_node.json()
        }

# literals
class IntegerLiteral(Expressions):
    def __init__(self, value: int = None) -> None:
        self.value: int = value

    def type(self) -> NodeType:
        return NodeType.IntegerLiteral

    def json(self) -> dict:
        return {
            "type": self.type().value,
            "value": self.value
        }

class FloatLiteral(Expressions):
    def __init__(self, value: float = None) -> None:
        self.value: float = value

    def type(self) -> NodeType:
        return NodeType.FloatLiteral

    def json(self) -> dict:
        return {
            "type": self.type().value,
            "value": self.value
        }

class IdentifierLiteral(Expressions):
    def __init__(self, value: str = None) -> None:
        self.value: str = value

    def type(self) -> NodeType:
        return NodeType.IdentifierLiteral

    def json(self) -> dict:
        return {
            "type": self.type().value,
            "value": self.value
        }

class BooleanLiteral(Expressions):
    def __init__(self, value: bool = None) -> None:
        self.value: bool = value

    def type(self) -> NodeType:
        return NodeType.BooleanLiteral

    def json(self) -> dict:
        return {
            "type": self.type().value,
            "value": self.value
        }
