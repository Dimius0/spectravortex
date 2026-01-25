"""
SpectraVortex Compiler
Photonic Programming Language with Matrix Support
"""

__version__ = "0.2.0"
__author__ = "SpectraVortex Team"
__license__ = "MIT"

# Import core compiler components
from .lexer import Lexer, Token, TokenType
from .parser import Parser

# Import AST nodes explicitly
from .ast_nodes import (
    ASTNode, ProgramNode, PhotonDefNode, BeamDefNode,
    ProgramDefNode, PrintNode, VariableDeclNode, AssignmentNode,
    FunctionDeclNode, ReturnNode, IfNode, WhileNode,
    ExpressionNode, LiteralNode, IdentifierNode, BinaryOpNode,
    UnaryOpNode, ArrayLiteralNode, MatrixLiteralNode,
    FunctionCallNode, ParenExprNode
)

__all__ = [
    # Core compiler
    'Lexer', 'Token', 'TokenType', 'Parser',
    
    # AST Nodes
    'ASTNode', 'ProgramNode', 'PhotonDefNode', 'BeamDefNode',
    'ProgramDefNode', 'PrintNode', 'VariableDeclNode', 'AssignmentNode',
    'FunctionDeclNode', 'ReturnNode', 'IfNode', 'WhileNode',
    
    # Expression Nodes
    'ExpressionNode', 'LiteralNode', 'IdentifierNode', 'BinaryOpNode',
    'UnaryOpNode', 'ArrayLiteralNode', 'MatrixLiteralNode',
    'FunctionCallNode', 'ParenExprNode'
]


def hello():
    """Simple test function"""
    return f"SpectraVortex Compiler v{__version__}"


def get_version():
    """Get current compiler version"""
    return __version__


def get_ast_node_classes():
    """Get list of available AST node classes"""
    return [
        'ASTNode', 'ProgramNode', 'PhotonDefNode', 'BeamDefNode',
        'ProgramDefNode', 'PrintNode', 'VariableDeclNode', 'AssignmentNode',
        'FunctionDeclNode', 'ReturnNode', 'IfNode', 'WhileNode',
        'ExpressionNode', 'LiteralNode', 'IdentifierNode', 'BinaryOpNode',
        'UnaryOpNode', 'ArrayLiteralNode', 'MatrixLiteralNode',
        'FunctionCallNode', 'ParenExprNode'
    ]


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


# Export convenience functions
__all__ += ['hello', 'get_version', 'get_ast_node_classes', 'compile_source']
