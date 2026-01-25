# compiler/ast_nodes.py
"""
AST Nodes for SpectraVortex
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass

@dataclass
class ASTNode:
    """Base class for AST nodes"""
    pass

@dataclass
class ProgramNode(ASTNode):
    """Root node of the program"""
    statements: List[ASTNode]

@dataclass
class PhotonDefNode(ASTNode):
    """Photon definition: photon name = { ... }"""
    name: str
    parameters: Dict[str, Any]

@dataclass
class BeamDefNode(ASTNode):
    """Beam definition: beam name = beam(...)"""
    name: str
    base_photon: str
    modifiers: Dict[str, Any]

@dataclass
class ProgramDefNode(ASTNode):
    """Program definition: program name() { ... }"""
    name: str
    body: List[ASTNode]

@dataclass
class PrintNode(ASTNode):
    """Print statement: print(...)"""
    expression: 'ExpressionNode'

@dataclass
class VariableDeclNode(ASTNode):
    """Variable declaration: name: type = value"""
    name: str
    var_type: Optional[str]
    initializer: Optional['ExpressionNode']

@dataclass
class AssignmentNode(ASTNode):
    """Assignment statement: name = value"""
    name: 'IdentifierNode'
    value: 'ExpressionNode'

@dataclass
class FunctionDeclNode(ASTNode):
    """Function declaration: function name(params) { ... }"""
    name: str
    parameters: List[str]
    body: List[ASTNode]

@dataclass
class ReturnNode(ASTNode):
    """Return statement: return value"""
    value: Optional['ExpressionNode']

@dataclass
class IfNode(ASTNode):
    """If statement: if (condition) { ... } else { ... }"""
    condition: 'ExpressionNode'
    then_branch: List[ASTNode]
    else_branch: List[ASTNode]

@dataclass
class WhileNode(ASTNode):
    """While statement: while (condition) { ... }"""
    condition: 'ExpressionNode'
    body: List[ASTNode]

@dataclass
class ExpressionNode(ASTNode):
    """Base class for expressions"""
    pass

@dataclass
class LiteralNode(ExpressionNode):
    """Literal value: number or string"""
    value: Any
    type: str  # "number", "string"

@dataclass
class IdentifierNode(ExpressionNode):
    """Identifier: variable or function name"""
    name: str

@dataclass
class BinaryOpNode(ExpressionNode):
    """Binary operation: left op right"""
    left: ExpressionNode
    op: str  # '+', '-', '*', '/', '=', '==', '!=', '<', '>', '<=', '>=', 'and', 'or'
    right: ExpressionNode

@dataclass
class UnaryOpNode(ExpressionNode):
    """Unary operation: op operand"""
    op: str  # '-', 'not'
    operand: ExpressionNode

@dataclass
class ArrayLiteralNode(ExpressionNode):
    """Array literal: [value1, value2, ...]"""
    elements: List[ExpressionNode]

@dataclass
class MatrixLiteralNode(ExpressionNode):
    """Matrix literal: { rows: N, cols: M, value: [[...], ...] }"""
    rows: int
    cols: int
    value: List[List[ExpressionNode]]

@dataclass
class FunctionCallNode(ExpressionNode):
    """Function call: name(arg1, arg2, ...)"""
    name: str
    arguments: List[ExpressionNode]

@dataclass
class ParenExprNode(ExpressionNode):
    """Parenthesized expression: (expr)"""
    expression: ExpressionNode

# Add to parser.py import section:
# from .ast_nodes import (all the classes above)
