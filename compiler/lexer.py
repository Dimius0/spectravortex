"""
Lexer (Tokenizer) for SpectraVortex language with OAM support
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

class TokenType(Enum):
    # Keywords
    PHOTON = "PHOTON"
    BEAM = "BEAM"
    PROGRAM = "PROGRAM"
    FUNCTION = "FUNCTION"
    RETURN = "RETURN"
    IF = "IF"
    ELSE = "ELSE"
    WHILE = "WHILE"
    FOR = "FOR"
    IN = "IN"
    END = "END"
    PRINT = "PRINT"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    TRUE = "TRUE"
    FALSE = "FALSE"
    
    # OAM and vortex light keywords
    VORTEX = "VORTEX"
    OAM_CHARGE = "OAM_CHARGE"
    HELICAL = "HELICAL"
    TOPOLOGICAL = "TOPOLOGICAL"
    INTERFERE = "INTERFERE"
    SUPERPOSE = "SUPERPOSE"
    MULTIPLEX = "MULTIPLEX"
    DEMULTIPLEX = "DEMULTIPLEX"
    WAVELENGTH = "WAVELENGTH"
    WAIST = "WAIST"
    VORTEX_BEAM = "VORTEX_BEAM"
    LAGUERRE_GAUSSIAN = "LAGUERRE_GAUSSIAN"
    
    # Types and properties
    FREQUENCY = "FREQUENCY"
    AMPLITUDE = "AMPLITUDE"
    PHASE = "PHASE"
    OAM = "OAM"
    POLARIZATION = "POLARIZATION"
    
    # Identifiers & Literals
    IDENTIFIER = "IDENTIFIER"
    NUMBER = "NUMBER"
    STRING = "STRING"
    
    # Operators
    PLUS = "PLUS"           # '+'
    MINUS = "MINUS"         # '-'
    STAR = "STAR"           # '*'
    SLASH = "SLASH"         # '/'
    EQUALS = "EQUALS"       # '='
    EQUAL_EQUAL = "EQUAL_EQUAL"     # '=='
    BANG_EQUAL = "BANG_EQUAL"       # '!='
    LESS = "LESS"                   # '<'
    LESS_EQUAL = "LESS_EQUAL"       # '<='
    GREATER = "GREATER"             # '>'
    GREATER_EQUAL = "GREATER_EQUAL" # '>='
    
    # OAM operators
    OAM_PLUS = "OAM_PLUS"          # ⊕ - специальное сложение OAM
    OAM_MINUS = "OAM_MINUS"        # ⊖
    VORTEX_PROD = "VORTEX_PROD"    # ⊗ - тензорное произведение OAM
    
    # Brackets and punctuation
    LPAREN = "LPAREN"       # '('
    RPAREN = "RPAREN"       # ')'
    LBRACE = "LBRACE"       # '{'
    RBRACE = "RBRACE"       # '}'
    LBRACKET = "LBRACKET"   # '['
    RBRACKET = "RBRACKET"   # ']'
    COMMA = "COMMA"         # ','
    COLON = "COLON"         # ':'
    SEMICOLON = "SEMICOLON" # ';'
    DOT = "DOT"             # '.'
    
    # Special
    NEWLINE = "NEWLINE"
    EOF = "EOF"

@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int
    
    def __str__(self):
        return f"{self.type.name}({repr(self.value)}) at {self.line}:{self.column}"
    
    def __repr__(self):
        return self.__str__()

class Lexer:
    """Lexer for SpectraVortex with OAM and vortex light support"""
    
    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        
        # Keywords lookup table
        self.keywords = {
            'photon': TokenType.PHOTON,
            'beam': TokenType.BEAM,
            'program': TokenType.PROGRAM,
            'function': TokenType.FUNCTION,
            'return': TokenType.RETURN,
            'if': TokenType.IF,
            'else': TokenType.ELSE,
            'while': TokenType.WHILE,
            'for': TokenType.FOR,
            'in': TokenType.IN,
            'end': TokenType.END,
            'print': TokenType.PRINT,
            'and': TokenType.AND,
            'or': TokenType.OR,
            'not': TokenType.NOT,
            'true': TokenType.TRUE,
            'false': TokenType.FALSE,
            
            # OAM keywords
            'vortex': TokenType.VORTEX,
            'oam_charge': TokenType.OAM_CHARGE,
            'helical': TokenType.HELICAL,
            'topological': TokenType.TOPOLOGICAL,
            'interfere': TokenType.INTERFERE,
            'superpose': TokenType.SUPERPOSE,
            'multiplex': TokenType.MULTIPLEX,
            'demultiplex': TokenType.DEMULTIPLEX,
            'wavelength': TokenType.WAVELENGTH,
            'waist': TokenType.WAIST,
            'vortex_beam': TokenType.VORTEX_BEAM,
            'laguerre_gaussian': TokenType.LAGUERRE_GAUSSIAN,
            
            # Physical properties
            'frequency': TokenType.FREQUENCY,
            'amplitude': TokenType.AMPLITUDE,
            'phase': TokenType.PHASE,
            'oam': TokenType.OAM,
            'polarization': TokenType.POLARIZATION,
        }
        
        # Special character mappings
        self.special_chars = {
            '⊕': TokenType.OAM_PLUS,
            '⊖': TokenType.OAM_MINUS,
            '⊗': TokenType.VORTEX_PROD,
        }
    
    def tokenize(self) -> List[Token]:
        """Convert source code to tokens"""
        while self.position < len(self.source):
            char = self.source[self.position]
            start_column = self.column
            
            # Skip whitespace (except newlines which we track)
            if char in ' \t\r':
                self._advance()
                continue
            
            # Handle newlines
            if char == '\n':
                self.tokens.append(Token(TokenType.NEWLINE, '\\n', self.line, self.column))
                self.line += 1
                self.column = 1
                self.position += 1
                continue
            
            # Handle comments
            if char == '/' and self._peek() == '/':
                self._skip_line_comment()
                continue
            
            if char == '/' and self._peek() == '*':
                self._skip_block_comment()
                continue
            
            # Check for special OAM characters
            if char in self.special_chars:
                self.tokens.append(Token(self.special_chars[char], char, self.line, start_column))
                self._advance()
                continue
            
            # Numbers (integers and floats)
            if char.isdigit() or (char == '.' and self._peek() and self._peek().isdigit()):
                self._tokenize_number()
                continue
            
            # Strings
            if char == '"' or char == "'":
                self._tokenize_string(char)
                continue
            
            # Identifiers and keywords
            if char.isalpha() or char == '_':
                self._tokenize_identifier()
                continue
            
            # Multi-character operators
            if self._match_multi_char():
                continue
            
            # Single character operators and punctuation
            token_type = self._get_single_char_token(char)
            if token_type:
                self.tokens.append(Token(token_type, char, self.line, start_column))
                self._advance()
                continue
            
            # Unknown character - skip with warning
            print(f"Warning: Unknown character '{char}' at line {self.line}, column {self.column}")
            self._advance()
        
        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens
    
    def _advance(self) -> None:
        """Advance to next character"""
        self.position += 1
        self.column += 1
    
    def _peek(self, offset: int = 1) -> Optional[str]:
        """Look ahead without consuming"""
        pos = self.position + offset
        if pos < len(self.source):
            return self.source[pos]
        return None
    
    def _match(self, expected: str) -> bool:
        """Check if current character matches expected"""
        if self.position < len(self.source) and self.source[self.position] == expected:
            return True
        return False
    
    def _skip_line_comment(self) -> None:
        """Skip single-line comments"""
        while self.position < len(self.source) and self.source[self.position] != '\n':
            self._advance()
    
    def _skip_block_comment(self) -> None:
        """Skip multi-line comments"""
        self._advance()  # Skip '/'
        self._advance()  # Skip '*'
        
        while self.position < len(self.source):
            if self.source[self.position] == '*' and self._peek() == '/':
                self._advance()  # Skip '*'
                self._advance()  # Skip '/'
                break
            elif self.source[self.position] == '\n':
                self.line += 1
                self.column = 1
                self.position += 1
            else:
                self._advance()
    
    def _tokenize_number(self) -> None:
        """Tokenize numbers (integers, floats, scientific notation)"""
        start = self.position
        start_column = self.column
        
        # Integer part
        while self.position < len(self.source) and self.source[self.position].isdigit():
            self._advance()
        
        # Decimal part
        if self._match('.') and self._peek() and self._peek().isdigit():
            self._advance()  # Skip '.'
            while self.position < len(self.source) and self.source[self.position].isdigit():
                self._advance()
        
        # Scientific notation
        if self._match('e') or self._match('E'):
            self._advance()  # Skip 'e' or 'E'
            
            # Optional sign
            if self._match('+') or self._match('-'):
                self._advance()
            
            # Exponent digits
            if self.position < len(self.source) and self.source[self.position].isdigit():
                while self.position < len(self.source) and self.source[self.position].isdigit():
                    self._advance()
            else:
                # Invalid scientific notation - backtrack
                self.position = start + (self.position - start) // 2
        
        number = self.source[start:self.position]
        self.tokens.append(Token(TokenType.NUMBER, number, self.line, start_column))
    
    def _tokenize_string(self, quote_char: str) -> None:
        """Tokenize string literals"""
        start = self.position
        start_column = self.column
        
        self._advance()  # Skip opening quote
        
        while self.position < len(self.source) and self.source[self.position] != quote_char:
            if self.source[self.position] == '\\' and self._peek():
                # Handle escape sequences
                self._advance()  # Skip backslash
                self._advance()  # Skip escaped character
            elif self.source[self.position] == '\n':
                # Multi-line string (allow newlines in strings)
                self.line += 1
                self.column = 1
                self._advance()
            else:
                self._advance()
        
        if self.position >= len(self.source):
            raise SyntaxError(f"Unterminated string at line {self.line}")
        
        string_content = self.source[start + 1:self.position]  # Exclude quotes
        self.tokens.append(Token(TokenType.STRING, string_content, self.line, start_column))
        self._advance()  # Skip closing quote
    
    def _tokenize_identifier(self) -> None:
        """Tokenize identifiers and keywords"""
        start = self.position
        start_column = self.column
        
        while self.position < len(self.source) and (self.source[self.position].isalnum() or self.source[self.position] == '_'):
            self._advance()
        
        text = self.source[start:self.position]
        token_type = self.keywords.get(text.lower(), TokenType.IDENTIFIER)
        self.tokens.append(Token(token_type, text, self.line, start_column))
    
    def _match_multi_char(self) -> bool:
        """Handle multi-character operators"""
        char = self.source[self.position]
        start_column = self.column
        
        # Two-character operators
        two_char_ops = {
            '==': TokenType.EQUAL_EQUAL,
            '!=': TokenType.BANG_EQUAL,
            '<=': TokenType.LESS_EQUAL,
            '>=': TokenType.GREATER_EQUAL,
            '//': None,  # Comment, handled elsewhere
            '/*': None,  # Comment, handled elsewhere
        }
        
        if self.position + 1 < len(self.source):
            two_char = char + self.source[self.position + 1]
            
            # Handle comments first
            if two_char == '//':
                self._skip_line_comment()
                return True
            
            if two_char == '/*':
                self._skip_block_comment()
                return True
            
            # Handle other two-character operators
            if two_char in two_char_ops and two_char_ops[two_char] is not None:
                self.tokens.append(Token(two_char_ops[two_char], two_char, self.line, start_column))
                self._advance()
                self._advance()
                return True
        
        return False
    
    def _get_single_char_token(self, char: str) -> Optional[TokenType]:
        """Get token type for single character"""
        single_char_tokens = {
            '+': TokenType.PLUS,
            '-': TokenType.MINUS,
            '*': TokenType.STAR,
            '/': TokenType.SLASH,
            '=': TokenType.EQUALS,
            '<': TokenType.LESS,
            '>': TokenType.GREATER,
            '(': TokenType.LPAREN,
            ')': TokenType.RPAREN,
            '{': TokenType.LBRACE,
            '}': TokenType.RBRACE,
            '[': TokenType.LBRACKET,
            ']': TokenType.RBRACKET,
            ',': TokenType.COMMA,
            ':': TokenType.COLON,
            ';': TokenType.SEMICOLON,
            '.': TokenType.DOT,
            '!': None,  # Only valid as '!='
        }
        
        return single_char_tokens.get(char)


def test_lexer():
    """Test the lexer with OAM support"""
    print("Testing Lexer with OAM support...")
    
    source = """
vortex photon_plus1 = {
    oam_charge: +1,
    wavelength: 1550e-9
}

vortex_beam lg_mode = laguerre_gaussian(
    oam_charge: +3,
    radial_order: 0
)

program oam_demo() {
    result = interfere(beam1, beam2);
    multiplexed = multiplex([mode1, mode2, mode3]);
}
"""
    
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    print(f"Generated {len(tokens)} tokens")
    
    # Show OAM-related tokens
    print("\nOAM-related tokens found:")
    for token in tokens:
        if any(keyword in token.type.name for keyword in ['VORTEX', 'OAM', 'INTERFERE', 'MULTIPLEX']):
            print(f"  {token}")
    
    return tokens


if __name__ == "__main__":
    test_lexer()
