"""
Parser for SpectraVortex language with OAM support
"""

from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass
from .lexer import Lexer, Token, TokenType
from .ast_nodes import *

class Parser:
    """Recursive descent parser for SpectraVortex with OAM support"""
    
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
    
    def _peek(self, offset: int = 0) -> Optional[Token]:
        """Look ahead at token without consuming it"""
        pos = self.position + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return None
    
    def _expect(self, token_type: TokenType, error_msg: str) -> Token:
        """Expect a specific token type"""
        if self.current_token and self.current_token.type == token_type:
            token = self.current_token
            self._advance()
            return token
        raise SyntaxError(f"{error_msg}. Got {self.current_token}")
    
    def _match(self, token_type: TokenType) -> bool:
        """Try to match a token type"""
        if self.current_token and self.current_token.type == token_type:
            self._advance()
            return True
        return False
    
    def _is_at_end(self) -> bool:
        """Check if we're at the end of tokens"""
        return self.current_token is None or self.current_token.type == TokenType.EOF
    
    def parse(self) -> ProgramNode:
        """Parse entire program"""
        statements = []
        
        while not self._is_at_end():
            # Skip newlines
            while self._match(TokenType.NEWLINE):
                pass
            
            if self._is_at_end():
                break
            
            stmt = self._parse_statement()
            if stmt:
                statements.append(stmt)
            
            # Optional semicolon
            self._match(TokenType.SEMICOLON)
        
        return ProgramNode(statements)
    
    def _parse_statement(self) -> Optional[ASTNode]:
        """Parse a statement"""
        if self._is_at_end():
            return None
        
        # Check statement type based on current token
        if self.current_token.type == TokenType.PHOTON:
            return self._parse_photon_def()
        elif self.current_token.type == TokenType.VORTEX:
            return self._parse_vortex_def()
        elif self.current_token.type == TokenType.BEAM:
            return self._parse_beam_def()
        elif self.current_token.type == TokenType.VORTEX_BEAM:
            return self._parse_vortex_beam_def()
        elif self.current_token.type == TokenType.PROGRAM:
            return self._parse_program_def()
        elif self.current_token.type == TokenType.FUNCTION:
            return self._parse_function_decl()
        elif self.current_token.type == TokenType.PRINT:
            return self._parse_print_statement()
        elif self.current_token.type == TokenType.IF:
            return self._parse_if_statement()
        elif self.current_token.type == TokenType.WHILE:
            return self._parse_while_statement()
        elif self.current_token.type == TokenType.RETURN:
            return self._parse_return_statement()
        elif self.current_token.type in [TokenType.INTERFERE, TokenType.SUPERPOSE, 
                                         TokenType.MULTIPLEX, TokenType.DEMULTIPLEX]:
            return self._parse_oam_operation()
        elif self.current_token.type == TokenType.IDENTIFIER:
            # Could be variable declaration or assignment
            if self._peek() and self._peek().type == TokenType.COLON:
                return self._parse_variable_decl()
            else:
                return self._parse_assignment_or_expression()
        else:
            # Expression statement
            return self._parse_expression()
    
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
            
            # Parse value expression
            value_expr = self._parse_expression()
            
            # Evaluate simple literals for parameters
            if isinstance(value_expr, LiteralNode):
                parameters[param_name] = value_expr.value
            elif isinstance(value_expr, IdentifierNode):
                parameters[param_name] = value_expr.name
            else:
                raise SyntaxError("Complex expressions not allowed in photon parameters")
            
            # Optional comma
            if self.current_token and self.current_token.type == TokenType.COMMA:
                self._advance()
        
        # }
        self._expect(TokenType.RBRACE, "Expected '}'")
        
        return PhotonDefNode(name, parameters)
    
    def _parse_vortex_def(self) -> VortexPhotonNode:
        """Parse vortex photon definition: vortex name = { oam_charge: N, ... }"""
        # vortex
        self._expect(TokenType.VORTEX, "Expected 'vortex'")
        
        # name
        name_token = self._expect(TokenType.IDENTIFIER, "Expected vortex name")
        name = name_token.value
        
        # =
        self._expect(TokenType.EQUALS, "Expected '='")
        
        # {
        self._expect(TokenType.LBRACE, "Expected '{'")
        
        # Parse parameters
        parameters = {}
        while self.current_token and self.current_token.type != TokenType.RBRACE:
            param_name = self._expect(TokenType.IDENTIFIER, "Expected parameter name").value
            self._expect(TokenType.COLON, "Expected ':'")
            
            if param_name == 'oam_charge':
                # OAM charge must be integer
                if self.current_token.type != TokenType.NUMBER:
                    raise SyntaxError("OAM charge must be a number")
                value = int(self.current_token.value)
                self._advance()
                parameters[param_name] = value
            elif param_name in ['wavelength', 'waist', 'power']:
                # Physical parameters
                if self.current_token.type != TokenType.NUMBER:
                    raise SyntaxError(f"{param_name} must be a number")
                value = float(self.current_token.value)
                self._advance()
                parameters[param_name] = value
            elif param_name == 'profile':
                # Beam profile type
                if self.current_token.type != TokenType.STRING:
                    raise SyntaxError("Profile must be a string")
                value = self.current_token.value
                self._advance()
                parameters[param_name] = value
            elif param_name == 'polarization':
                # Polarization state
                value_expr = self._parse_expression()
                if isinstance(value_expr, (LiteralNode, IdentifierNode)):
                    parameters[param_name] = value_expr.value if isinstance(value_expr, LiteralNode) else value_expr.name
                else:
                    raise SyntaxError("Polarization must be a literal or identifier")
            else:
                raise SyntaxError(f"Unknown vortex parameter: {param_name}")
            
            # Optional comma
            if self.current_token and self.current_token.type == TokenType.COMMA:
                self._advance()
        
        # }
        self._expect(TokenType.RBRACE, "Expected '}'")
        
        return VortexPhotonNode(name, parameters)
    
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
                
                # Parse value expression
                value_expr = self._parse_expression()
                
                # Evaluate simple literals for modifiers
                if isinstance(value_expr, LiteralNode):
                    modifiers[mod_name] = value_expr.value
                else:
                    raise SyntaxError("Complex expressions not allowed in beam modifiers")
                
                # Optional comma
                if self.current_token and self.current_token.type == TokenType.COMMA:
                    self._advance()
        
        # )
        self._expect(TokenType.RPAREN, "Expected ')'")
        
        return BeamDefNode(name, base_photon, modifiers)
    
    def _parse_vortex_beam_def(self) -> VortexBeamNode:
        """Parse vortex beam definition: vortex_beam name = laguerre_gaussian(...)"""
        # vortex_beam
        self._expect(TokenType.VORTEX_BEAM, "Expected 'vortex_beam'")
        
        # name
        name_token = self._expect(TokenType.IDENTIFIER, "Expected beam name")
        name = name_token.value
        
        # =
        self._expect(TokenType.EQUALS, "Expected '='")
        
        # Expect laguerre_gaussian or similar function
        func_token = self._expect(TokenType.IDENTIFIER, "Expected beam function")
        func_name = func_token.value
        
        self._expect(TokenType.LPAREN, "Expected '('")
        
        # Parse parameters
        parameters = {}
        while self.current_token and self.current_token.type != TokenType.RPAREN:
            param_name = self._expect(TokenType.IDENTIFIER, "Expected parameter name").value
            self._expect(TokenType.COLON, "Expected ':'")
            
            if param_name in ['oam_charge', 'radial_order']:
                # Integer parameters
                if self.current_token.type != TokenType.NUMBER:
                    raise SyntaxError(f"{param_name} must be an integer")
                value = int(self.current_token.value)
                self._advance()
                parameters[param_name] = value
            elif param_name in ['wavelength', 'waist', 'power']:
                # Float parameters
                if self.current_token.type != TokenType.NUMBER:
                    raise SyntaxError(f"{param_name} must be a number")
                value = float(self.current_token.value)
                self._advance()
                parameters[param_name] = value
            else:
                # Other parameters
                value_expr = self._parse_expression()
                if isinstance(value_expr, LiteralNode):
                    parameters[param_name] = value_expr.value
                elif isinstance(value_expr, IdentifierNode):
                    parameters[param_name] = value_expr.name
                else:
                    raise SyntaxError("Complex expressions not allowed in beam parameters")
            
            if self.current_token and self.current_token.type == TokenType.COMMA:
                self._advance()
        
        self._expect(TokenType.RPAREN, "Expected ')'")
        
        return VortexBeamNode(name, func_name, parameters)
    
    def _parse_oam_operation(self) -> Optional[OAMOperationNode]:
        """Parse OAM-specific operations: interfere, superpose, multiplex"""
        if self.current_token.type == TokenType.INTERFERE:
            return self._parse_interfere_operation()
        elif self.current_token.type == TokenType.SUPERPOSE:
            return self._parse_superpose_operation()
        elif self.current_token.type == TokenType.MULTIPLEX:
            return self._parse_multiplex_operation()
        elif self.current_token.type == TokenType.DEMULTIPLEX:
            return self._parse_demultiplex_operation()
        return None
    
    def _parse_interfere_operation(self) -> InterfereNode:
        """Parse interference: interfere(beam1, beam2)"""
        self._expect(TokenType.INTERFERE, "Expected 'interfere'")
        self._expect(TokenType.LPAREN, "Expected '('")
        
        beam1 = self._parse_expression()
        self._expect(TokenType.COMMA, "Expected ','")
        beam2 = self._parse_expression()
        
        self._expect(TokenType.RPAREN, "Expected ')'")
        return InterfereNode(beam1, beam2)
    
    def _parse_superpose_operation(self) -> SuperposeNode:
        """Parse superposition: superpose(beams: [...], coefficients: [...])"""
        self._expect(TokenType.SUPERPOSE, "Expected 'superpose'")
        self._expect(TokenType.LPAREN, "Expected '('")
        
        # Parse beams array
        self._expect(TokenType.IDENTIFIER, "Expected 'beams' parameter")
        self._expect(TokenType.COLON, "Expected ':'")
        beams = self._parse_array_literal()
        
        self._expect(TokenType.COMMA, "Expected ','")
        
        # Parse coefficients array
        self._expect(TokenType.IDENTIFIER, "Expected 'coefficients' parameter")
        self._expect(TokenType.COLON, "Expected ':'")
        coefficients = self._parse_array_literal()
        
        self._expect(TokenType.RPAREN, "Expected ')'")
        return SuperposeNode(beams, coefficients)
    
    def _parse_multiplex_operation(self) -> MultiplexNode:
        """Parse multiplexing: multiplex(beams, method: "mode")"""
        self._expect(TokenType.MULTIPLEX, "Expected 'multiplex'")
        self._expect(TokenType.LPAREN, "Expected '('")
        
        # Parse beams array
        beams = self._parse_expression()
        
        # Parse optional method parameter
        method = "mode"  # default
        if self._match(TokenType.COMMA):
            self._expect(TokenType.IDENTIFIER, "Expected 'method'")
            self._expect(TokenType.COLON, "Expected ':'")
            if self.current_token.type == TokenType.STRING:
                method = self.current_token.value
                self._advance()
            else:
                raise SyntaxError("Method must be a string")
        
        self._expect(TokenType.RPAREN, "Expected ')'")
        beams_list = beams if isinstance(beams, list) else [beams]
        return MultiplexNode(beams_list, method)
    
    def _parse_demultiplex_operation(self) -> DemultiplexNode:
        """Parse demultiplexing: demultiplex(input_beam, output_modes)"""
        self._expect(TokenType.DEMULTIPLEX, "Expected 'demultiplex'")
        self._expect(TokenType.LPAREN, "Expected '('")
        
        input_beam = self._parse_expression()
        self._expect(TokenType.COMMA, "Expected ','")
        output_modes = self._parse_array_literal()
        
        self._expect(TokenType.RPAREN, "Expected ')'")
        return DemultiplexNode(input_beam, output_modes)
    
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
        
        # Parse body
        body = []
        while self.current_token and self.current_token.type != TokenType.RBRACE:
            stmt = self._parse_statement()
            if stmt:
                body.append(stmt)
            
            # Optional semicolon
            self._match(TokenType.SEMICOLON)
        
        # }
        self._expect(TokenType.RBRACE, "Expected '}'")
        
        return ProgramDefNode(name, body)
    
    def _parse_function_decl(self) -> FunctionDeclNode:
        """Parse function declaration: function name(params) { ... }"""
        # function
        self._expect(TokenType.FUNCTION, "Expected 'function'")
        
        # name
        name_token = self._expect(TokenType.IDENTIFIER, "Expected function name")
        name = name_token.value
        
        # (
        self._expect(TokenType.LPAREN, "Expected '('")
        
        # Parse parameters
        parameters = []
        if self.current_token.type != TokenType.RPAREN:
            while True:
                param_token = self._expect(TokenType.IDENTIFIER, "Expected parameter name")
                parameters.append(param_token.value)
                
                if not self._match(TokenType.COMMA):
                    break
        
        # )
        self._expect(TokenType.RPAREN, "Expected ')'")
        
        # {
        self._expect(TokenType.LBRACE, "Expected '{'")
        
        # Parse body
        body = []
        while self.current_token and self.current_token.type != TokenType.RBRACE:
            stmt = self._parse_statement()
            if stmt:
                body.append(stmt)
            
            # Optional semicolon
            self._match(TokenType.SEMICOLON)
        
        # }
        self._expect(TokenType.RBRACE, "Expected '}'")
        
        return FunctionDeclNode(name, parameters, body)
    
    def _parse_print_statement(self) -> PrintNode:
        """Parse print statement: print(expression)"""
        # print
        self._expect(TokenType.PRINT, "Expected 'print'")
        
        # (
        self._expect(TokenType.LPAREN, "Expected '('")
        
        # expression
        expr = self._parse_expression()
        
        # )
        self._expect(TokenType.RPAREN, "Expected ')'")
        
        return PrintNode(expr)
    
    def _parse_variable_decl(self) -> VariableDeclNode:
        """Parse variable declaration: name: type = value"""
        # name
        name_token = self._expect(TokenType.IDENTIFIER, "Expected variable name")
        name = name_token.value
        
        # :
        self._expect(TokenType.COLON, "Expected ':'")
        
        # type (optional)
        var_type = None
        if self.current_token.type == TokenType.IDENTIFIER:
            var_type_token = self._expect(TokenType.IDENTIFIER, "Expected type")
            var_type = var_type_token.value
        
        # = value (optional)
        initializer = None
        if self._match(TokenType.EQUALS):
            initializer = self._parse_expression()
        
        return VariableDeclNode(name, var_type, initializer)
    
    def _parse_assignment_or_expression(self) -> ASTNode:
        """Parse assignment or expression statement"""
        # Try to parse as expression first
        expr = self._parse_expression()
        
        # Check if it's an assignment
        if self._match(TokenType.EQUALS):
            if isinstance(expr, IdentifierNode):
                value = self._parse_expression()
                return AssignmentNode(expr, value)
            else:
                raise SyntaxError("Left side of assignment must be an identifier")
        
        # If not an assignment, return as expression statement
        return expr
    
    def _parse_if_statement(self) -> IfNode:
        """Parse if statement: if (condition) { ... } else { ... }"""
        # if
        self._expect(TokenType.IF, "Expected 'if'")
        
        # (
        self._expect(TokenType.LPAREN, "Expected '('")
        
        # condition
        condition = self._parse_expression()
        
        # )
        self._expect(TokenType.RPAREN, "Expected ')'")
        
        # {
        self._expect(TokenType.LBRACE, "Expected '{'")
        
        # Parse then branch
        then_branch = []
        while self.current_token and self.current_token.type != TokenType.RBRACE:
            stmt = self._parse_statement()
            if stmt:
                then_branch.append(stmt)
            
            # Optional semicolon
            self._match(TokenType.SEMICOLON)
        
        # }
        self._expect(TokenType.RBRACE, "Expected '}'")
        
        # Optional else branch
        else_branch = []
        if self._match(TokenType.ELSE):
            self._expect(TokenType.LBRACE, "Expected '{'")
            
            while self.current_token and self.current_token.type != TokenType.RBRACE:
                stmt = self._parse_statement()
                if stmt:
                    else_branch.append(stmt)
                
                # Optional semicolon
                self._match(TokenType.SEMICOLON)
            
            self._expect(TokenType.RBRACE, "Expected '}'")
        
        return IfNode(condition, then_branch, else_branch)
    
    def _parse_while_statement(self) -> WhileNode:
        """Parse while statement: while (condition) { ... }"""
        # while
        self._expect(TokenType.WHILE, "Expected 'while'")
        
        # (
        self._expect(TokenType.LPAREN, "Expected '('")
        
        # condition
        condition = self._parse_expression()
        
        # )
        self._expect(TokenType.RPAREN, "Expected ')'")
        
        # {
        self._expect(TokenType.LBRACE, "Expected '{'")
        
        # Parse body
        body = []
        while self.current_token and self.current_token.type != TokenType.RBRACE:
            stmt = self._parse_statement()
            if stmt:
                body.append(stmt)
            
            # Optional semicolon
            self._match(TokenType.SEMICOLON)
        
        # }
        self._expect(TokenType.RBRACE, "Expected '}'")
        
        return WhileNode(condition, body)
    
    def _parse_return_statement(self) -> ReturnNode:
        """Parse return statement: return value"""
        # return
        self._expect(TokenType.RETURN, "Expected 'return'")
        
        # Optional value
        value = None
        if not (self.current_token.type in [TokenType.SEMICOLON, TokenType.RBRACE, TokenType.NEWLINE]):
            value = self._parse_expression()
        
        return ReturnNode(value)
    
    # ========== Expression Parsing ==========
    
    def _parse_expression(self) -> ExpressionNode:
        """Parse an expression"""
        return self._parse_logical_or()
    
    def _parse_logical_or(self) -> ExpressionNode:
        """Parse logical OR: and_expr ('or' and_expr)*"""
        expr = self._parse_logical_and()
        
        while self._match(TokenType.OR):
            op = "or"
            right = self._parse_logical_and()
            expr = BinaryOpNode(expr, op, right)
        
        return expr
    
    def _parse_logical_and(self) -> ExpressionNode:
        """Parse logical AND: equality ('and' equality)*"""
        expr = self._parse_equality()
        
        while self._match(TokenType.AND):
            op = "and"
            right = self._parse_equality()
            expr = BinaryOpNode(expr, op, right)
        
        return expr
    
    def _parse_equality(self) -> ExpressionNode:
        """Parse equality: comparison (('==' | '!=') comparison)*"""
        expr = self._parse_comparison()
        
        while True:
            if self._match(TokenType.EQUAL_EQUAL):
                op = "=="
            elif self._match(TokenType.BANG_EQUAL):
                op = "!="
            else:
                break
            
            right = self._parse_comparison()
            expr = BinaryOpNode(expr, op, right)
        
        return expr
    
    def _parse_comparison(self) -> ExpressionNode:
        """Parse comparison: term (('<' | '<=' | '>' | '>=') term)*"""
        expr = self._parse_term()
        
        while True:
            if self._match(TokenType.LESS):
                op = "<"
            elif self._match(TokenType.LESS_EQUAL):
                op = "<="
            elif self._match(TokenType.GREATER):
                op = ">"
            elif self._match(TokenType.GREATER_EQUAL):
                op = ">="
            else:
                break
            
            right = self._parse_term()
            expr = BinaryOpNode(expr, op, right)
        
        return expr
    
    def _parse_term(self) -> ExpressionNode:
        """Parse term: factor (('+' | '-' | OAM_PLUS | OAM_MINUS) factor)*"""
        expr = self._parse_factor()
        
        while True:
            if self._match(TokenType.PLUS):
                op = "+"
            elif self._match(TokenType.MINUS):
                op = "-"
            elif self._match(TokenType.OAM_PLUS):
                op = "⊕"
            elif self._match(TokenType.OAM_MINUS):
                op = "⊖"
            else:
                break
            
            right = self._parse_factor()
            expr = BinaryOpNode(expr, op, right)
        
        return expr
    
    def _parse_factor(self) -> ExpressionNode:
        """Parse factor: unary (('*' | '/' | VORTEX_PROD) unary)*"""
        expr = self._parse_unary()
        
        while True:
            if self._match(TokenType.STAR):
                op = "*"
            elif self._match(TokenType.SLASH):
                op = "/"
            elif self._match(TokenType.VORTEX_PROD):
                op = "⊗"
            else:
                break
            
            right = self._parse_unary()
            expr = BinaryOpNode(expr, op, right)
        
        return expr
    
    def _parse_unary(self) -> ExpressionNode:
        """Parse unary: ('-' | 'not') unary | primary"""
        if self._match(TokenType.MINUS):
            op = "-"
            operand = self._parse_unary()
            return UnaryOpNode(op, operand)
        elif self._match(TokenType.NOT):
            op = "not"
            operand = self._parse_unary()
            return UnaryOpNode(op, operand)
        
        return self._parse_primary()
    
    def _parse_primary(self) -> ExpressionNode:
        """Parse primary expression"""
        if self._is_at_end():
            raise SyntaxError("Unexpected end of input")
        
        # Matrix literal
        if self.current_token.type == TokenType.LBRACE:
            # Check if it's a matrix or vortex definition
            if self._peek(1) and self._peek(1).type == TokenType.IDENTIFIER:
                if self._peek(1).value in ['rows', 'oam_charge']:
                    # Check second token to decide
                    if self._peek(1).value == 'rows':
                        return self._parse_matrix_literal()
                    else:
                        # This should have been caught by _parse_statement
                        raise SyntaxError("Vortex definition in expression context")
            else:
                return self._parse_matrix_literal()
        
        # Array literal
        if self.current_token.type == TokenType.LBRACKET:
            return self._parse_array_literal()
        
        # Literals
        if self.current_token.type == TokenType.NUMBER:
            value = float(self.current_token.value)
            self._advance()
            return LiteralNode(value, "number")
        
        if self.current_token.type == TokenType.STRING:
            value = self.current_token.value
            self._advance()
            return LiteralNode(value, "string")
        
        # Identifier or function call
        if self.current_token.type == TokenType.IDENTIFIER:
            name_token = self._expect(TokenType.IDENTIFIER, "Expected identifier")
            name = name_token.value
            
            # Check if it's a function call
            if self.current_token and self.current_token.type == TokenType.LPAREN:
                return self._parse_function_call(name)
            
            return IdentifierNode(name)
        
        # OAM charge literal
        if self.current_token.type == TokenType.OAM_CHARGE:
            self._advance()
            self._expect(TokenType.COLON, "Expected ':' after 'oam_charge'")
            
            if self.current_token.type != TokenType.NUMBER:
                raise SyntaxError("OAM charge must be a number")
            
            charge = int(self.current_token.value)
            self._advance()
            return OAMChargeNode(charge)
        
        # Parenthesized expression
        if self._match(TokenType.LPAREN):
            expr = self._parse_expression()
            self._expect(TokenType.RPAREN, "Expected ')'")
            return ParenExprNode(expr)
        
        raise SyntaxError(f"Unexpected token: {self.current_token}")
    
    def _parse_matrix_literal(self) -> MatrixLiteralNode:
        """Parse matrix literal: { rows: N, cols: M, value: [[...], ...] }"""
        self._expect(TokenType.LBRACE, "Expected '{'")
        
        rows = None
        cols = None
        matrix_data = None
        
        # Parse rows, cols, and value
        while self.current_token and self.current_token.type != TokenType.RBRACE:
            # Parse key
            key_token = self._expect(TokenType.IDENTIFIER, "Expected 'rows', 'cols', or 'value'")
            key = key_token.value
            
            self._expect(TokenType.COLON, "Expected ':'")
            
            if key == "rows" or key == "cols":
                # Parse number
                if self.current_token.type != TokenType.NUMBER:
                    raise SyntaxError(f"Expected number for '{key}', got {self.current_token}")
                
                value = int(self.current_token.value)
                self._advance()
                
                if key == "rows":
                    rows = value
                else:
                    cols = value
            elif key == "value":
                # Parse nested array
                matrix_data = self._parse_nested_array_literal()
            else:
                raise SyntaxError(f"Unknown matrix key: '{key}'. Expected 'rows', 'cols', or 'value'")
            
            # Optional comma
            if self.current_token and self.current_token.type == TokenType.COMMA:
                self._advance()
        
        self._expect(TokenType.RBRACE, "Expected '}'")
        
        # Validate matrix
        if rows is None or cols is None or matrix_data is None:
            raise SyntaxError("Matrix must have 'rows', 'cols', and 'value'")
        
        # Validate dimensions
        if len(matrix_data) != rows:
            raise SyntaxError(f"Matrix row count mismatch: declared {rows}, got {len(matrix_data)}")
        
        for i, row in enumerate(matrix_data):
            if len(row) != cols:
                raise SyntaxError(f"Matrix column count mismatch in row {i}: declared {cols}, got {len(row)}")
        
        return MatrixLiteralNode(rows, cols, matrix_data)
    
    def _parse_nested_array_literal(self) -> List[List[ExpressionNode]]:
        """Parse nested array for matrix values: [[...], [...], ...]"""
        self._expect(TokenType.LBRACKET, "Expected '[' for matrix values")
        
        rows = []
        
        # Parse rows
        while self.current_token and self.current_token.type != TokenType.RBRACKET:
            # Parse a row (array)
            row = self._parse_array_literal()
            rows.append(row)
            
            # Optional comma between rows
            if self.current_token and self.current_token.type == TokenType.COMMA:
                self._advance()
        
        self._expect(TokenType.RBRACKET, "Expected ']'")
        
        return rows
    
    def _parse_array_literal(self) -> List[ExpressionNode]:
        """Parse array literal: [expr1, expr2, ...]"""
        self._expect(TokenType.LBRACKET, "Expected '['")
        
        elements = []
        
        # Empty array
        if self.current_token and self.current_token.type == TokenType.RBRACKET:
            self._advance()
            return elements
        
        # Parse elements
        while True:
            element = self._parse_expression()
            elements.append(element)
            
            if not self._match(TokenType.COMMA):
                break
        
        self._expect(TokenType.RBRACKET, "Expected ']'")
        
        return elements
    
    def _parse_function_call(self, name: str) -> FunctionCallNode:
        """Parse function call: name(arg1, arg2, ...)"""
        self._expect(TokenType.LPAREN, "Expected '('")
        
        arguments = []
        
        # Parse arguments if any
        if self.current_token and self.current_token.type != TokenType.RPAREN:
            while True:
                arg = self._parse_expression()
                arguments.append(arg)
                
                if not self._match(TokenType.COMMA):
                    break
        
        self._expect(TokenType.RPAREN, "Expected ')'")
        
        return FunctionCallNode(name, arguments)


def test_parser():
    """Test the parser with OAM support"""
    print("Testing Parser with OAM Support...")
    
    source = """
vortex photon_plus1 = {
    oam_charge: +1,
    wavelength: 1550e-9,
    waist: 2.0
}

vortex_beam lg_mode = laguerre_gaussian(
    oam_charge: +3,
    radial_order: 0,
    waist: 1.5
)

program oam_demo() {
    print("OAM Demo");
    result = interfere(photon_plus1, lg_mode);
}
"""
    
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    print(f"Tokens: {len(tokens)}")
    
    parser = Parser(tokens)
    ast = parser.parse()
    
    print(f"\nParsed {len(ast.statements)} statements:")
    for i, stmt in enumerate(ast.statements):
        print(f"\n{i}: {stmt.__class__.__name__}")
        
        if isinstance(stmt, VortexPhotonNode):
            print(f"   Name: {stmt.name}")
            print(f"   OAM charge: {stmt.oam_charge}")
            print(f"   Parameters: {stmt.parameters}")
        
        elif isinstance(stmt, VortexBeamNode):
            print(f"   Name: {stmt.name}")
            print(f"   Beam type: {stmt.beam_type}")
            print(f"   Parameters: {stmt.parameters}")
    
    return ast


if __name__ == "__main__":
    test_parser()
