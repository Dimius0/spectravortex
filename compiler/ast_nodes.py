"""
AST Nodes for SpectraVortex with OAM support
"""

from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass

@dataclass
class ASTNode:
    """Base class for AST nodes"""
    pass

@dataclass
class ProgramNode(ASTNode):
    """Root node of the program"""
    statements: List['ASTNode']

@dataclass
class PhotonDefNode(ASTNode):
    """Photon definition: photon name = { ... }"""
    name: str
    parameters: Dict[str, Any]

@dataclass
class VortexPhotonNode(ASTNode):
    """Vortex photon with OAM charge"""
    name: str
    parameters: Dict[str, Any]
    
    def __post_init__(self):
        """Extract OAM charge from parameters"""
        self.oam_charge = self.parameters.get('oam_charge', 0)

@dataclass
class BeamDefNode(ASTNode):
    """Beam definition: beam name = beam(...)"""
    name: str
    base_photon: str
    modifiers: Dict[str, Any]

@dataclass
class VortexBeamNode(ASTNode):
    """Vortex beam (LG mode)"""
    name: str
    beam_type: str  # "laguerre_gaussian", "helical", etc.
    parameters: Dict[str, Any]
    
    def __post_init__(self):
        """Extract OAM charge from parameters"""
        self.oam_charge = self.parameters.get('oam_charge', 0)

@dataclass
class ProgramDefNode(ASTNode):
    """Program definition: program name() { ... }"""
    name: str
    body: List['ASTNode']

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
    body: List['ASTNode']

@dataclass
class ReturnNode(ASTNode):
    """Return statement: return value"""
    value: Optional['ExpressionNode']

@dataclass
class IfNode(ASTNode):
    """If statement: if (condition) { ... } else { ... }"""
    condition: 'ExpressionNode'
    then_branch: List['ASTNode']
    else_branch: List['ASTNode']

@dataclass
class WhileNode(ASTNode):
    """While statement: while (condition) { ... }"""
    condition: 'ExpressionNode'
    body: List['ASTNode']

@dataclass
class OAMOperationNode(ASTNode):
    """Base class for OAM operations"""
    pass

@dataclass
class InterfereNode(OAMOperationNode):
    """Optical interference of two beams"""
    beam1: 'ExpressionNode'
    beam2: 'ExpressionNode'

@dataclass
class SuperposeNode(OAMOperationNode):
    """Quantum superposition of OAM states"""
    beams: List['ExpressionNode']
    coefficients: List['ExpressionNode']

@dataclass
class MultiplexNode(OAMOperationNode):
    """Spatial multiplexing of OAM modes"""
    beams: List['ExpressionNode']
    method: str = "mode"

@dataclass
class DemultiplexNode(OAMOperationNode):
    """Demultiplexing OAM modes"""
    input_beam: 'ExpressionNode'
    output_modes: List['ExpressionNode']

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
    left: 'ExpressionNode'
    op: str  # '+', '-', '*', '/', '=', '==', '!=', '<', '>', '<=', '>=', 'and', 'or', '⊕', '⊖', '⊗'
    right: 'ExpressionNode'

@dataclass
class UnaryOpNode(ExpressionNode):
    """Unary operation: op operand"""
    op: str  # '-', 'not'
    operand: 'ExpressionNode'

@dataclass
class ArrayLiteralNode(ExpressionNode):
    """Array literal: [value1, value2, ...]"""
    elements: List['ExpressionNode']

@dataclass
class MatrixLiteralNode(ExpressionNode):
    """Matrix literal: { rows: N, cols: M, value: [[...], ...] }"""
    rows: int
    cols: int
    value: List[List['ExpressionNode']]

@dataclass
class FunctionCallNode(ExpressionNode):
    """Function call: name(arg1, arg2, ...)"""
    name: str
    arguments: List['ExpressionNode']

@dataclass
class ParenExprNode(ExpressionNode):
    """Parenthesized expression: (expr)"""
    expression: 'ExpressionNode'

@dataclass
class OAMChargeNode(ExpressionNode):
    """OAM charge value"""
    charge: int

@dataclass
class TypeAnnotationNode(ASTNode):
    """Type annotation for OAM checking"""
    variable: 'IdentifierNode'
    type_expr: str  # "vortex", "beam", "matrix", etc.

# Explicit export list
__all__ = [
    'ASTNode',
    'ProgramNode',
    'PhotonDefNode',
    'VortexPhotonNode',
    'BeamDefNode',
    'VortexBeamNode',
    'ProgramDefNode',
    'PrintNode',
    'VariableDeclNode',
    'AssignmentNode',
    'FunctionDeclNode',
    'ReturnNode',
    'IfNode',
    'WhileNode',
    'OAMOperationNode',
    'InterfereNode',
    'SuperposeNode',
    'MultiplexNode',
    'DemultiplexNode',
    'ExpressionNode',
    'LiteralNode',
    'IdentifierNode',
    'BinaryOpNode',
    'UnaryOpNode',
    'ArrayLiteralNode',
    'MatrixLiteralNode',
    'FunctionCallNode',
    'ParenExprNode',
    'OAMChargeNode',
    'TypeAnnotationNode'
]
