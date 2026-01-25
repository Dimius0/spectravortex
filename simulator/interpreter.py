# simulator/interpreter.py
"""
Interpreter for SpectraVortex AST
"""

from typing import Dict, List, Any, Optional
from .matrix_ops import MatrixOperations  # Импортируем MatrixOperations

# Явно импортируем все используемые классы из ast_nodes
from compiler.ast_nodes import (
    ASTNode, ProgramNode, PhotonDefNode, BeamDefNode,
    ProgramDefNode, PrintNode, VariableDeclNode, AssignmentNode,
    FunctionDeclNode, ReturnNode, IfNode, WhileNode, LiteralNode,
    IdentifierNode, BinaryOpNode, UnaryOpNode, ArrayLiteralNode,
    MatrixLiteralNode, FunctionCallNode, ParenExprNode, ExpressionNode
)

class Interpreter:
    """Interprets and executes SpectraVortex AST"""
    
    def __init__(self):
        self.symbol_table = {}
        self.photon_definitions = {}
        self.beam_definitions = {}
        self.matrix_operations = MatrixOperations()  # Теперь класс определен
    
    def execute(self, ast_node: ASTNode) -> Any:
        """Execute an AST node"""
        # Определяем тип узла правильно
        node_type = ast_node.__class__.__name__
        
        if node_type == "ProgramNode":
            return self._execute_program(ast_node)
        elif node_type == "PhotonDefNode":
            return self._execute_photon_def(ast_node)
        elif node_type == "BeamDefNode":
            return self._execute_beam_def(ast_node)
        elif node_type == "ProgramDefNode":
            return self._execute_program_def(ast_node)
        elif node_type == "PrintNode":
            return self._execute_print(ast_node)
        elif node_type == "VariableDeclNode":
            return self._execute_variable_decl(ast_node)
        elif node_type == "AssignmentNode":
            return self._execute_assignment(ast_node)
        elif node_type == "FunctionDeclNode":
            return self._execute_function_decl(ast_node)
        elif node_type == "ReturnNode":
            return self._execute_return(ast_node)
        elif node_type == "IfNode":
            return self._execute_if(ast_node)
        elif node_type == "WhileNode":
            return self._execute_while(ast_node)
        elif node_type == "MatrixLiteralNode":
            return self._execute_matrix_literal(ast_node)
        elif node_type == "ArrayLiteralNode":
            return self._execute_array_literal(ast_node)
        elif node_type == "LiteralNode":
            return ast_node.value
        elif node_type == "IdentifierNode":
            return self._lookup_variable(ast_node.name)
        elif node_type == "BinaryOpNode":
            return self._execute_binary_op(ast_node)
        elif node_type == "UnaryOpNode":
            return self._execute_unary_op(ast_node)
        elif node_type == "FunctionCallNode":
            return self._execute_function_call(ast_node)
        elif node_type == "ParenExprNode":
            return self.execute(ast_node.expression)
        else:
            raise RuntimeError(f"Unknown node type: {node_type}")
    
    def _execute_program(self, node: ProgramNode) -> None:
        """Execute a program"""
        for stmt in node.statements:
            self.execute(stmt)
    
    def _execute_photon_def(self, node: PhotonDefNode) -> None:
        """Store photon definition"""
        self.photon_definitions[node.name] = node.parameters
    
    def _execute_beam_def(self, node: BeamDefNode) -> None:
        """Store beam definition"""
        self.beam_definitions[node.name] = {
            'base_photon': node.base_photon,
            'modifiers': node.modifiers
        }
    
    def _execute_program_def(self, node: ProgramDefNode) -> None:
        """Execute a program definition"""
        # Store program for later execution
        print(f"[Interpreter] Defining program: {node.name}")
        self.symbol_table[node.name] = node
        
        # Execute program body immediately (simplified approach)
        print(f"[Interpreter] Executing program: {node.name}")
        for stmt in node.body:
            self.execute(stmt)
    
    def _execute_print(self, node: PrintNode) -> None:
        """Execute print statement"""
        value = self.execute(node.expression)
        print(value)
    
    def _execute_variable_decl(self, node: VariableDeclNode) -> None:
        """Execute variable declaration"""
        value = self.execute(node.initializer) if node.initializer else None
        self.symbol_table[node.name] = value
        print(f"[Interpreter] Variable declared: {node.name} = {value}")
    
    def _execute_assignment(self, node: AssignmentNode) -> None:
        """Execute assignment"""
        value = self.execute(node.value)
        var_name = node.name.name
        self.symbol_table[var_name] = value
        print(f"[Interpreter] Variable assigned: {var_name} = {value}")
    
    def _execute_matrix_literal(self, node: MatrixLiteralNode) -> Dict[str, Any]:
        """Execute matrix literal"""
        # Evaluate matrix elements
        evaluated_matrix = []
        for row in node.value:
            evaluated_row = []
            for element in row:
                evaluated_row.append(self.execute(element))
            evaluated_matrix.append(evaluated_row)
        
        matrix_obj = {
            'type': 'matrix',
            'rows': node.rows,
            'cols': node.cols,
            'value': evaluated_matrix
        }
        
        print(f"[Interpreter] Created matrix: {node.rows}x{node.cols}")
        return matrix_obj
    
    def _execute_array_literal(self, node: ArrayLiteralNode) -> List[Any]:
        """Execute array literal"""
        result = [self.execute(element) for element in node.elements]
        print(f"[Interpreter] Created array with {len(result)} elements")
        return result
    
    def _lookup_variable(self, name: str) -> Any:
        """Look up a variable"""
        if name in self.symbol_table:
            return self.symbol_table[name]
        raise RuntimeError(f"Undefined variable: {name}")
    
    def _execute_binary_op(self, node: BinaryOpNode) -> Any:
        """Execute binary operation"""
        left = self.execute(node.left)
        right = self.execute(node.right)
        
        # Check if it's matrix multiplication
        if node.op == "*":
            # Check if both are matrices
            if isinstance(left, dict) and left.get('type') == 'matrix':
                if isinstance(right, dict) and right.get('type') == 'matrix':
                    return self._matrix_multiply(left, right)
                elif isinstance(right, (int, float)):
                    return self._matrix_scalar_multiply(left, right)
            elif isinstance(right, dict) and right.get('type') == 'matrix':
                if isinstance(left, (int, float)):
                    return self._matrix_scalar_multiply(right, left)
        
        # Standard operations
        ops = {
            '+': lambda a, b: a + b,
            '-': lambda a, b: a - b,
            '*': lambda a, b: a * b,
            '/': lambda a, b: a / b,
            '==': lambda a, b: a == b,
            '!=': lambda a, b: a != b,
            '<': lambda a, b: a < b,
            '<=': lambda a, b: a <= b,
            '>': lambda a, b: a > b,
            '>=': lambda a, b: a >= b,
            'and': lambda a, b: a and b,
            'or': lambda a, b: a or b,
        }
        
        if node.op in ops:
            return ops[node.op](left, right)
        
        raise RuntimeError(f"Unknown operator: {node.op}")
    
    def _matrix_multiply(self, matrix_a: Dict, matrix_b: Dict) -> Dict:
        """Matrix multiplication"""
        print(f"[Interpreter] Matrix multiplication: {matrix_a['rows']}x{matrix_a['cols']} * {matrix_b['rows']}x{matrix_b['cols']}")
        
        # Use MatrixOperations class
        return self.matrix_operations.multiply(matrix_a, matrix_b)
    
    def _matrix_scalar_multiply(self, matrix: Dict, scalar: float) -> Dict:
        """Multiply matrix by scalar"""
        result = {
            'type': 'matrix',
            'rows': matrix['rows'],
            'cols': matrix['cols'],
            'value': [[element * scalar for element in row] for row in matrix['value']]
        }
        print(f"[Interpreter] Scalar multiplication: matrix * {scalar}")
        return result
    
    def _execute_unary_op(self, node: UnaryOpNode) -> Any:
        """Execute unary operation"""
        operand = self.execute(node.operand)
        
        if node.op == '-':
            return -operand
        elif node.op == 'not':
            return not operand
        
        raise RuntimeError(f"Unknown unary operator: {node.op}")
    
    def _execute_function_call(self, node: FunctionCallNode) -> Any:
        """Execute function call"""
        print(f"[Interpreter] Function call: {node.name}")
        
        # For now, handle built-in functions
        if node.name == "encode_matrix":
            if len(node.arguments) != 1:
                raise RuntimeError("encode_matrix expects 1 argument")
            matrix = self.execute(node.arguments[0])
            print(f"[Interpreter] Encoding matrix: {matrix['rows']}x{matrix['cols']}")
            return matrix
        
        elif node.name == "optical_matmul":
            if len(node.arguments) != 2:
                raise RuntimeError("optical_matmul expects 2 arguments")
            a = self.execute(node.arguments[0])
            b = self.execute(node.arguments[1])
            return self._matrix_multiply(a, b)
        
        elif node.name == "measure_optical_matrix":
            if len(node.arguments) != 1:
                raise RuntimeError("measure_optical_matrix expects 1 argument")
            matrix = self.execute(node.arguments[0])
            # Simulate measurement by squaring amplitudes (intensity)
            result = {
                'type': 'electrical',
                'rows': matrix['rows'],
                'cols': matrix['cols'],
                'value': [[element * element for element in row] for row in matrix['value']]
            }
            print(f"[Interpreter] Measured optical matrix")
            return result
        
        else:
            # Try to execute user-defined function
            if node.name in self.symbol_table:
                func_node = self.symbol_table[node.name]
                if isinstance(func_node, FunctionDeclNode):
                    return self._execute_user_function(func_node, node.arguments)
            
            raise RuntimeError(f"Unknown function: {node.name}")
    
    def _execute_user_function(
        self, 
        func_node: FunctionDeclNode, 
        args: List[ExpressionNode]
    ) -> Any:
        """Execute user-defined function"""
        print(f"[Interpreter] Executing user function: {func_node.name}")
        
        # Save current symbol table
        old_symbols = self.symbol_table.copy()
        
        # Bind arguments to parameters
        for param, arg in zip(func_node.parameters, args):
            self.symbol_table[param] = self.execute(arg)
        
        # Execute function body
        result = None
        for stmt in func_node.body:
            self.execute(stmt)
            # Check for return statement (simplified)
            if isinstance(stmt, ReturnNode):
                result = self.execute(stmt.value) if stmt.value else None
        
        # Restore symbol table
        self.symbol_table = old_symbols
        
        return result
    
    def _execute_function_decl(self, node: FunctionDeclNode) -> None:
        """Store function declaration"""
        self.symbol_table[node.name] = node
        print(f"[Interpreter] Function declared: {node.name}")
    
    def _execute_return(self, node: ReturnNode) -> Any:
        """Execute return statement"""
        value = self.execute(node.value) if node.value else None
        print(f"[Interpreter] Return value: {value}")
        return value
    
    def _execute_if(self, node: IfNode) -> Any:
        """Execute if statement"""
        condition = self.execute(node.condition)
        print(f"[Interpreter] If condition: {condition}")
        
        if condition:
            for stmt in node.then_branch:
                self.execute(stmt)
        else:
            for stmt in node.else_branch:
                self.execute(stmt)
    
    def _execute_while(self, node: WhileNode) -> None:
        """Execute while statement"""
        print(f"[Interpreter] While loop")
        while self.execute(node.condition):
            for stmt in node.body:
                self.execute(stmt)
    
    def run(self, ast: ProgramNode) -> None:
        """Run the interpreter on an AST"""
        print("[Interpreter] Starting execution...")
        self.execute(ast)
        print("[Interpreter] Execution completed!")
