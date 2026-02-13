"""
SpectraVortex Compiler
Photonic Programming Language with OAM Support
"""

__version__ = "0.3.0"
__author__ = "SpectraVortex Team"
__license__ = "MIT"

# Import core compiler components
from .lexer import Lexer, Token, TokenType
from .parser import Parser

# Import AST nodes explicitly
from .ast_nodes import (
    ASTNode, ProgramNode, PhotonDefNode, VortexPhotonNode, 
    BeamDefNode, VortexBeamNode, ProgramDefNode, PrintNode, 
    VariableDeclNode, AssignmentNode, FunctionDeclNode, ReturnNode, 
    IfNode, WhileNode, InterfereNode, SuperposeNode, MultiplexNode, 
    DemultiplexNode, ExpressionNode, LiteralNode, IdentifierNode, 
    BinaryOpNode, UnaryOpNode, ArrayLiteralNode, MatrixLiteralNode, 
    FunctionCallNode, ParenExprNode, OAMChargeNode
)

# Import type checker
try:
    from .type_checker import TypeChecker, Type, PhotonType, BeamType, OAMType
    HAS_TYPE_CHECKER = True
except ImportError:
    HAS_TYPE_CHECKER = False
    TypeChecker = None
    Type = None
    PhotonType = None
    BeamType = None
    OAMType = None

__all__ = [
    # Core compiler
    'Lexer', 'Token', 'TokenType', 'Parser',
    
    # AST Nodes
    'ASTNode', 'ProgramNode', 'PhotonDefNode', 'VortexPhotonNode',
    'BeamDefNode', 'VortexBeamNode', 'ProgramDefNode', 'PrintNode',
    'VariableDeclNode', 'AssignmentNode', 'FunctionDeclNode', 'ReturnNode',
    'IfNode', 'WhileNode', 'InterfereNode', 'SuperposeNode', 'MultiplexNode',
    'DemultiplexNode',
    
    # Expression Nodes
    'ExpressionNode', 'LiteralNode', 'IdentifierNode', 'BinaryOpNode',
    'UnaryOpNode', 'ArrayLiteralNode', 'MatrixLiteralNode',
    'FunctionCallNode', 'ParenExprNode', 'OAMChargeNode',
    
    # Type system
    'TypeChecker', 'Type', 'PhotonType', 'BeamType', 'OAMType',
    'HAS_TYPE_CHECKER'
]


def hello():
    """Simple test function"""
    return f"SpectraVortex Compiler v{__version__} with OAM support"


def get_version():
    """Get current compiler version"""
    return __version__


def compile_source(source_code: str) -> ProgramNode:
    """
    Compile source code to AST
    
    Args:
        source_code: SpectraVortex source code
        
    Returns:
        ProgramNode: Compiled AST
        
    Example:
        ast = compile_source('program test() { print("Hello"); }')
    """
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


def check_types(ast: ProgramNode) -> bool:
    """
    Type check an AST (if type checker is available)
    
    Args:
        ast: Abstract Syntax Tree
        
    Returns:
        bool: True if type checking passes
        
    Raises:
        ImportError: If type checker is not available
    """
    if not HAS_TYPE_CHECKER:
        raise ImportError("Type checker not available")
    
    type_checker = TypeChecker()
    return type_checker.check(ast)


# Export convenience functions
__all__ += ['hello', 'get_version', 'compile_source', 'check_types']
