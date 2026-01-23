"""
Lexer (Tokenizer) for SpectraVortex language
"""

from enum import Enum
from dataclasses import dataclass
from typing import List

class TokenType(Enum):
    # Keywords
    PHOTON = "PHOTON"
    BEAM = "BEAM"
    PROGRAM = "PROGRAM"
    FUNCTION = "FUNCTION"
    RETURN = "RETURN"
    IF = "IF"
    ELSE = "ELSE"
    FOR = "FOR"
    IN = "IN"
    END = "END"
    
    # Types
    FREQUENCY = "FREQUENCY"
    AMPLITUDE = "AMPLITUDE"
    PHASE = "PHASE"
    
    # Identifiers & Literals
    IDENTIFIER = "IDENTIFIER"
    NUMBER = "NUMBER"
    STRING = "STRING"
    
    # Operators
    PLUS = "PLUS"
    MINUS = "MINUS"
    STAR = "STAR"
    SLASH = "SLASH"
    EQUALS = "EQUALS"
    
    # Brackets
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    COMMA = "COMMA"
    COLON = "COLON"
    
    # Special
    EOF = "EOF"

@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int
    
    def __str__(self):
        return f"{self.type.name}:{self.value}"

class Lexer:
    """Simple lexer for SpectraVortex"""
    
    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
    
    def tokenize(self) -> List[Token]:
        """Convert source code to tokens"""
        while self.position < len(self.source):
            char = self.source[self.position]
            
            # Skip whitespace
            if char in ' \t\r':
                self.position += 1
                self.column += 1
                continue
            
            # Skip newline
            if char == '\n':
                self.position += 1
                self.line += 1
                self.column = 1
                continue
            
            # Skip comments
            if char == '/' and self.position + 1 < len(self.source) and self.source[self.position + 1] == '/':
                while self.position < len(self.source) and self.source[self.position] != '\n':
                    self.position += 1
                continue
            
            # Numbers
            if char.isdigit() or char == '.':
                start = self.position
                while self.position < len(self.source) and (self.source[self.position].isdigit() or self.source[self.position] == '.'):
                    self.position += 1
                number = self.source[start:self.position]
                self.tokens.append(Token(TokenType.NUMBER, number, self.line, self.column))
                self.column += len(number)
                continue
            
            # Identifiers and keywords
            if char.isalpha() or char == '_':
                start = self.position
                while self.position < len(self.source) and (self.source[self.position].isalnum() or self.source[self.position] == '_'):
                    self.position += 1
                text = self.source[start:self.position]
                
                # Check if it's a keyword
                if text == 'photon':
                    token_type = TokenType.PHOTON
                elif text == 'beam':
                    token_type = TokenType.BEAM
                elif text == 'program':
                    token_type = TokenType.PROGRAM
                elif text == 'frequency':
                    token_type = TokenType.FREQUENCY
                elif text == 'amplitude':
                    token_type = TokenType.AMPLITUDE
                elif text == 'phase':
                    token_type = TokenType.PHASE
                else:
                    token_type = TokenType.IDENTIFIER
                
                self.tokens.append(Token(token_type, text, self.line, self.column))
                self.column += len(text)
                continue
            
            # Operators and punctuation
            if char == '+':
                self.tokens.append(Token(TokenType.PLUS, char, self.line, self.column))
            elif char == '-':
                self.tokens.append(Token(TokenType.MINUS, char, self.line, self.column))
            elif char == '*':
                self.tokens.append(Token(TokenType.STAR, char, self.line, self.column))
            elif char == '/':
                self.tokens.append(Token(TokenType.SLASH, char, self.line, self.column))
            elif char == '=':
                self.tokens.append(Token(TokenType.EQUALS, char, self.line, self.column))
            elif char == '(':
                self.tokens.append(Token(TokenType.LPAREN, char, self.line, self.column))
            elif char == ')':
                self.tokens.append(Token(TokenType.RPAREN, char, self.line, self.column))
            elif char == '{':
                self.tokens.append(Token(TokenType.LBRACE, char, self.line, self.column))
            elif char == '}':
                self.tokens.append(Token(TokenType.RBRACE, char, self.line, self.column))
            elif char == ',':
                self.tokens.append(Token(TokenType.COMMA, char, self.line, self.column))
            elif char == ':':
                self.tokens.append(Token(TokenType.COLON, char, self.line, self.column))
            else:
                # Unknown character - skip it
                self.position += 1
                self.column += 1
                continue
            
            self.position += 1
            self.column += 1
        
        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens

def test_lexer():
    """Simple test function"""
    source = """
photon laser = {
    frequency: 193.414e12,
    amplitude: 0.8
}
"""
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    print("Lexer test output:")
    for token in tokens:
        print(f"  {token}")
    
    return tokens

if __name__ == "__main__":
    test_lexer()
