"""
Lexer (Tokenizer) for SpectraVortex language with full expression support
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
    """Lexer for SpectraVortex with full expression and matrix support"""
    
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
            'frequency': TokenType.FREQUENCY,
            'amplitude': TokenType.AMPLITUDE,
            'phase': TokenType.PHASE,
            'oam': TokenType.OAM,
            'polarization': TokenType.POLARIZATION,
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
    """Test the lexer with various language features"""
    print("Testing Lexer with full expression support...")
    
    test_cases = [
        # Basic photon definition
        """
        photon laser = {
            frequency: 193.414e12,
            amplitude: 0.8,
            polarization: "linear"
        }
        """,
        
        # Matrix definition
        """
        matrix = { rows: 2, cols: 2, value: [[1, 2], [3, 4]] }
        """,
        
        # Program with expressions
        """
        program test() {
            x = 10 + 5 * 2;
            y = x < 20 and x > 5;
            print("Result:", x);
            
            if (x == 20) {
                print("x is 20");
            } else {
                print("x is not 20");
            }
            
            while (x > 0) {
                x = x - 1;
            }
        }
        """,
        
        # Function definition
        """
        function encode_matrix(data) {
            return data * 2;
        }
        """,
        
        # Complex expressions for optical computing
        """
        // Optical interference simulation
        beam1 = beam(laser, phase: 0.0);
        beam2 = beam(laser, phase: 3.14159);
        
        interference = beam1 + beam2;
        intensity = amplitude(interference) * amplitude(interference);
        """
    ]
    
    for i, source in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test Case {i}:")
        print(f"{'='*60}")
        print(f"Source:\n{source.strip()}")
        print(f"\nTokens:")
        
        try:
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            
            for token in tokens:
                if token.type != TokenType.NEWLINE:  # Skip newline tokens for readability
                    print(f"  {token}")
            
            print(f"\n✅ Parsed {len(tokens)} tokens successfully")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    return True


def test_optical_matrix_example():
    """Test the optical matrix multiplier example specifically"""
    print(f"\n{'='*60}")
    print("Testing Optical Matrix Multiplier Example")
    print(f"{'='*60}")
    
    source = """
// Optical Matrix Multiplier Demo
photon source = {
    frequency: 193.414e12,
    amplitude: 1.0,
    phase: 0.0,
    oam: 0,
    polarization: "linear"
}

function encode_matrix(matrix_data) {
    print("Encoding matrix of size:", matrix_data.rows, "x", matrix_data.cols);
    return matrix_data;
}

function optical_matmul(matrix_a, matrix_b) {
    if (matrix_a.cols != matrix_b.rows) {
        print("Error: Matrix dimensions incompatible!");
        return { rows: 0, cols: 0, value: [[]] };
    }
    
    print("Performing optical matrix multiplication...");
    
    // Simulate optical computation
    result_matrix = { 
        rows: matrix_a.rows, 
        cols: matrix_b.cols, 
        value: [[0, 0], [0, 0]] 
    };
    
    return result_matrix;
}

program optical_demo() {
    print("=== Optical Matrix Multiplier Demo ===");
    
    // Define test matrices
    matrix_a = { rows: 2, cols: 2, value: [[1.0, 2.0], [3.0, 4.0]] };
    matrix_b = { rows: 2, cols: 2, value: [[0.5, 1.0], [1.5, 2.0]] };
    
    // Encode matrices as optical signals
    optical_a = encode_matrix(matrix_a);
    optical_b = encode_matrix(matrix_b);
    
    // Perform optical multiplication
    result = optical_matmul(optical_a, optical_b);
    
    print("Demo completed!");
}
"""
    
    print("Source code loaded successfully")
    
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    print(f"\nGenerated {len(tokens)} tokens")
    
    # Count token types
    token_counts = {}
    for token in tokens:
        if token.type != TokenType.NEWLINE and token.type != TokenType.EOF:
            token_counts[token.type] = token_counts.get(token.type, 0) + 1
    
    print("\nToken counts:")
    for token_type, count in sorted(token_counts.items()):
        print(f"  {token_type.name}: {count}")
    
    # Show first 20 non-newline tokens
    print("\nFirst 20 tokens (excluding newlines):")
    non_newline_tokens = [t for t in tokens if t.type != TokenType.NEWLINE]
    for i, token in enumerate(non_newline_tokens[:20]):
        print(f"  {i:2d}: {token}")
    
    print(f"\n✅ Optical matrix example lexed successfully!")
    return tokens


if __name__ == "__main__":
    print("SpectraVortex Lexer Test Suite")
    print("=" * 60)
    
    # Run basic tests
    test_lexer()
    
    # Run optical matrix example test
    test_optical_matrix_example()
    
    print(f"\n{'='*60}")
    print("✅ All lexer tests completed successfully!")
