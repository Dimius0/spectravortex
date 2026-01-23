"""
Parser for SpectraVortex language
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from .lexer import Lexer, Token, TokenType

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
    op: str  # '+', '-', '*', '/', '='
    right: ExpressionNode

class Parser:
    """Recursive descent parser for SpectraVortex"""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.position = 0
        self.current_token = None
        self._advance()
    
    def _advance(self):
        """Move to next token"""
        if self.position < len(self.tokens):
            self.current_token = self.tokens[self.position]
            self.position += 1
        else:
            self.current_token = None
    
    def _peek(self) -> Optional[Token]:
        """Look at next token without consuming it"""
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return None
    
    def _expect(self, token_type: TokenType, error_msg: str) -> Token:
        """Expect a specific token type"""
        if self.current_token and self.current_token.type == token_type:
            token = self.current_token
            self._advance()
            return token
        raise SyntaxError(error_msg)
    
    def _match(self, token_type: TokenType) -> bool:
        """Try to match a token type"""
        if self.current_token and self.current_token.type == token_type:
            self._advance()
            return True
        return False
    
    def parse(self) -> ProgramNode:
        """Parse entire program"""
        statements = []
        
        while self.current_token and self.current_token.type != TokenType.EOF:
            # Skip newlines and whitespace
            while self._match(TokenType.NEWLINE):
                pass
            
            if self.current_token is None:
                break
            
            # Parse different statement types
            if self.current_token.type == TokenType.PHOTON:
                stmt = self._parse_photon_def()
            elif self.current_token.type == TokenType.BEAM:
                stmt = self._parse_beam_def()
            elif self.current_token.type == TokenType.PROGRAM:
                stmt = self._parse_program_def()
            else:
                # Skip unknown tokens
                self._advance()
                continue
            
            if stmt:
                statements.append(stmt)
        
        return ProgramNode(statements)
    
    def _parse_photon_def(self) -> PhotonDefNode:
        """Parse photon definition: photon name = { ... }"""
        # photon
        self._expect(TokenType.PHOTON, "Expected 'photon'")
        
        # name
        name_token = self._expect(TokenType.IDENTIFIER, "Expected photon name")
        name = name_token.value
        
        # =
        self._expect(TokenType.EQUALS, "Expected '='")
        
        # {
        self._expect(TokenType.LBRACE, "Expected '{'")
        
        # Parse parameters
        parameters = {}
        while self.current_token and self.current_token.type != TokenType.RBRACE:
            # param_name: value
            param_name = self._expect(TokenType.IDENTIFIER, "Expected parameter name").value
            self._expect(TokenType.COLON, "Expected ':'")
            
            # Parse value
            if self.current_token.type == TokenType.NUMBER:
                value = float(self.current_token.value)
                self._advance()
            elif self.current_token.type == TokenType.STRING:
                value = self.current_token.value
                self._advance()
            elif self.current_token.type == TokenType.IDENTIFIER:
                value = self.current_token.value
                self._advance()
            else:
                raise SyntaxError(f"Unexpected token in photon parameter: {self.current_token}")
            
            parameters[param_name] = value
            
            # Optional comma
            if self.current_token and self.current_token.type == TokenType.COMMA:
                self._advance()
        
        # }
        self._expect(TokenType.RBRACE, "Expected '}'")
        
        return PhotonDefNode(name, parameters)
    
    def _parse_beam_def(self) -> BeamDefNode:
        """Parse beam definition: beam name = beam(...)"""
        # beam
        self._expect(TokenType.BEAM, "Expected 'beam'")
        
        # name
        name_token = self._expect(TokenType.IDENTIFIER, "Expected beam name")
        name = name_token.value
        
        # =
        self._expect(TokenType.EQUALS, "Expected '='")
        
        # beam(
        self._expect(TokenType.IDENTIFIER, "Expected 'beam'")
        self._expect(TokenType.LPAREN, "Expected '('")
        
        # base photon name
        base_token = self._expect(TokenType.IDENTIFIER, "Expected photon name")
        base_photon = base_token.value
        
        # Parse optional modifiers
        modifiers = {}
        if self._match(TokenType.COMMA):
            while self.current_token and self.current_token.type != TokenType.RPAREN:
                # modifier: value
                mod_name = self._expect(TokenType.IDENTIFIER, "Expected modifier name").value
                self._expect(TokenType.COLON, "Expected ':'")
                
                # Parse value
                if self.current_token.type == TokenType.NUMBER:
                    value = float(self.current_token.value)
                    self._advance()
                elif self.current_token.type == TokenType.STRING:
                    value = self.current_token.value
                    self._advance()
                else:
                    raise SyntaxError(f"Unexpected token in beam modifier: {self.current_token}")
                
                modifiers[mod_name] = value
                
                # Optional comma
                if self.current_token and self.current_token.type == TokenType.COMMA:
                    self._advance()
        
        # )
        self._expect(TokenType.RPAREN, "Expected ')'")
        
        return BeamDefNode(name, base_photon, modifiers)
    
    def _parse_program_def(self) -> ProgramDefNode:
        """Parse program definition: program name() { ... }"""
        # program
        self._expect(TokenType.PROGRAM, "Expected 'program'")
        
        # name
        name_token = self._expect(TokenType.IDENTIFIER, "Expected program name")
        name = name_token.value
        
        # (
        self._expect(TokenType.LPAREN, "Expected '('")
        
        # )
        self._expect(TokenType.RPAREN, "Expected ')'")
        
        # {
        self._expect(TokenType.LBRACE, "Expected '{'")
        
        # Parse body (simplified - just skip for now)
        body = []
        while self.current_token and self.current_token.type != TokenType.RBRACE:
            # Skip everything in body for now
            self._advance()
        
        # }
        self._expect(TokenType.RBRACE, "Expected '}'")
        
        return ProgramDefNode(name, body)
    
    def _parse_expression(self) -> ExpressionNode:
        """Parse an expression"""
        # Simplified - just parse literals and identifiers
        if self.current_token.type == TokenType.NUMBER:
            value = float(self.current_token.value)
            self._advance()
            return LiteralNode(value, "number")
        elif self.current_token.type == TokenType.STRING:
            value = self.current_token.value
            self._advance()
            return LiteralNode(value, "string")
        elif self.current_token.type == TokenType.IDENTIFIER:
            name = self.current_token.value
            self._advance()
            return IdentifierNode(name)
        else:
            raise SyntaxError(f"Unexpected token in expression: {self.current_token}")

def test_parser():
    """Test the parser"""
    print("Testing Parser...")
    
    source = """
photon laser = {
    frequency: 193.414e12,
    amplitude: 0.8,
    polarization: "linear"
}

beam laser_beam = beam(laser)

program test() {
    // Simple test program
}
"""
    
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    parser = Parser(tokens)
    ast = parser.parse()
    
    print(f"Parsed {len(ast.statements)} statements:")
    for i, stmt in enumerate(ast.statements):
        print(f"  {i}: {stmt.__class__.__name__}")
        if isinstance(stmt, PhotonDefNode):
            print(f"     Name: {stmt.name}")
            print(f"     Parameters: {stmt.parameters}")
        elif isinstance(stmt, BeamDefNode):
            print(f"     Name: {stmt.name}")
            print(f"     Base photon: {stmt.base_photon}")
            print(f"     Modifiers: {stmt.modifiers}")
    
    return ast

if __name__ == "__main__":
    test_parser()
