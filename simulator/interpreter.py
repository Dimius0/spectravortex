"""
Interpreter for SpectraVortex AST with OAM support
"""

from typing import Dict, List, Any, Optional, Tuple
from .matrix_ops import MatrixOperations
from .oam_physics import OAMPhysics

# Явно импортируем все используемые классы из ast_nodes
from compiler.ast_nodes import (
    ASTNode, ProgramNode, PhotonDefNode, VortexPhotonNode, 
    BeamDefNode, VortexBeamNode, ProgramDefNode, PrintNode, 
    VariableDeclNode, AssignmentNode, FunctionDeclNode, ReturnNode, 
    IfNode, WhileNode, InterfereNode, SuperposeNode, MultiplexNode, 
    DemultiplexNode, LiteralNode, IdentifierNode, BinaryOpNode, 
    UnaryOpNode, ArrayLiteralNode, MatrixLiteralNode, 
    FunctionCallNode, ParenExprNode, OAMChargeNode, OAMOperationNode
)

class Interpreter:
    """Interprets and executes SpectraVortex AST with OAM support"""
    
    def __init__(self):
        self.symbol_table = {}
        self.photon_definitions = {}
        self.beam_definitions = {}
        self.matrix_operations = MatrixOperations()
        self.oam_physics = OAMPhysics()
        
        # Built-in functions
        self.builtin_functions = {
            'encode_matrix': self._builtin_encode_matrix,
            'optical_matmul': self._builtin_optical_matmul,
            'measure_optical_matrix': self._builtin_measure_optical_matrix,
            'calculate_oam_spectrum': self._builtin_calculate_oam_spectrum,
            'create_vortex_array': self._builtin_create_vortex_array,
        }
    
    def execute(self, ast_node: ASTNode) -> Any:
        """Execute an AST node"""
        node_type = ast_node.__class__.__name__
        
        if node_type == "ProgramNode":
            return self._execute_program(ast_node)
        elif node_type == "PhotonDefNode":
            return self._execute_photon_def(ast_node)
        elif node_type == "VortexPhotonNode":
            return self._execute_vortex_photon(ast_node)
        elif node_type == "BeamDefNode":
            return self._execute_beam_def(ast_node)
        elif node_type == "VortexBeamNode":
            return self._execute_vortex_beam(ast_node)
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
        elif node_type == "InterfereNode":
            return self._execute_interfere(ast_node)
        elif node_type == "SuperposeNode":
            return self._execute_superpose(ast_node)
        elif node_type == "MultiplexNode":
            return self._execute_multiplex(ast_node)
        elif node_type == "DemultiplexNode":
            return self._execute_demultiplex(ast_node)
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
        elif node_type == "OAMChargeNode":
            return {"type": "oam_charge", "value": ast_node.charge}
        else:
            raise RuntimeError(f"Unknown node type: {node_type}")
    
    def _execute_program(self, node: ProgramNode) -> None:
        """Execute a program"""
        for stmt in node.statements:
            self.execute(stmt)
    
    def _execute_photon_def(self, node: PhotonDefNode) -> None:
        """Store photon definition"""
        self.photon_definitions[node.name] = node.parameters
        self.symbol_table[node.name] = {
            'type': 'photon',
            'name': node.name,
            'parameters': node.parameters
        }
        print(f"[Interpreter] Photon defined: {node.name}")
    
    def _execute_vortex_photon(self, node: VortexPhotonNode) -> Dict[str, Any]:
        """Execute vortex photon definition"""
        vortex_data = {
            'type': 'vortex_photon',
            'name': node.name,
            'oam_charge': node.parameters.get('oam_charge', 0),
            'wavelength': node.parameters.get('wavelength', 1550e-9),
            'waist': node.parameters.get('waist', 1.0),
            'profile': node.parameters.get('profile', 'laguerre_gaussian'),
            'power': node.parameters.get('power', 1.0)
        }
        
        print(f"[Interpreter] Created vortex photon: OAM={vortex_data['oam_charge']}")
        self.symbol_table[node.name] = vortex_data
        return vortex_data
    
    def _execute_beam_def(self, node: BeamDefNode) -> Dict[str, Any]:
        """Store beam definition"""
        beam_data = {
            'base_photon': node.base_photon,
            'modifiers': node.modifiers
        }
        self.beam_definitions[node.name] = beam_data
        self.symbol_table[node.name] = {
            'type': 'beam',
            'name': node.name,
            **beam_data
        }
        print(f"[Interpreter] Beam defined: {node.name} based on {node.base_photon}")
        return beam_data
    
    def _execute_vortex_beam(self, node: VortexBeamNode) -> Dict[str, Any]:
        """Execute vortex beam definition"""
        # Simulate Laguerre-Gaussian beam
        beam_data = {
            'type': 'vortex_beam',
            'name': node.name,
            'beam_type': node.beam_type,
            'oam_charge': node.parameters.get('oam_charge', 0),
            'radial_order': node.parameters.get('radial_order', 0),
            'waist': node.parameters.get('waist', 1.0),
            'wavelength': node.parameters.get('wavelength', 1550e-9),
            'power': node.parameters.get('power', 1.0)
        }
        
        print(f"[Interpreter] Created {node.beam_type} beam with OAM={beam_data['oam_charge']}")
        self.symbol_table[node.name] = beam_data
        return beam_data
    
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
        
        # Pretty print for special types
        if isinstance(value, dict):
            if value.get('type') == 'vortex_photon':
                print(f"Vortex photon: OAM={value.get('oam_charge', 0)}")
            elif value.get('type') == 'vortex_beam':
                print(f"Vortex beam ({value.get('beam_type')}): OAM={value.get('oam_charge', 0)}")
            elif value.get('type') == 'interference':
                print(f"Interference pattern: visibility={value.get('visibility', 0):.2f}")
            elif value.get('type') == 'superposition':
                print(f"Superposition: {len(value.get('beams', []))} states")
            elif value.get('type') == 'multiplexed':
                print(f"Multiplexed: {len(value.get('oam_charges', []))} modes")
            elif value.get('type') == 'matrix':
                print(f"Matrix {value['rows']}x{value['cols']}: {value['value']}")
            else:
                print(value)
        else:
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
    
    def _execute_interfere(self, node: InterfereNode) -> Dict[str, Any]:
        """Execute interference of two beams"""
        beam1 = self.execute(node.beam1)
        beam2 = self.execute(node.beam2)
        
        # Check OAM conservation
        oam1 = beam1.get('oam_charge', 0) if isinstance(beam1, dict) else 0
        oam2 = beam2.get('oam_charge', 0) if isinstance(beam2, dict) else 0
        
        visibility, resulting_oam = self.oam_physics.interfere_beams(oam1, oam2)
        
        # Simulate interference pattern
        interference = {
            'type': 'interference',
            'beam1': beam1,
            'beam2': beam2,
            'oam_charge1': oam1,
            'oam_charge2': oam2,
            'visibility': visibility,
            'resulting_oam': resulting_oam,
            'can_interfere': oam1 == oam2
        }
        
        if oam1 != oam2:
            print(f"[Interpreter] WARNING: Interfering beams with different OAM: {oam1} ≠ {oam2}")
            print("  → Result will have reduced visibility")
        
        print(f"[Interpreter] Interference: OAM{oam1} ⊕ OAM{oam2} → visibility={visibility:.2f}")
        return interference
    
    def _execute_superpose(self, node: SuperposeNode) -> Dict[str, Any]:
        """Execute quantum superposition of OAM states"""
        beams = [self.execute(beam) for beam in node.beams]
        coeffs = [self.execute(coeff) for coeff in node.coefficients]
        
        # All beams must have defined OAM
        oam_charges = []
        for beam in beams:
            if isinstance(beam, dict):
                oam_charges.append(beam.get('oam_charge', 0))
            else:
                oam_charges.append(0)
        
        # Check if superposition is entangled (multiple different OAM states)
        is_entangled = len(set(oam_charges)) > 1
        
        superposition = {
            'type': 'superposition',
            'beams': beams,
            'coefficients': coeffs,
            'oam_charges': oam_charges,
            'is_entangled': is_entangled,
            'num_states': len(beams)
        }
        
        if is_entangled:
            print(f"[Interpreter] Created entangled superposition of OAM states: {oam_charges}")
        else:
            print(f"[Interpreter] Created superposition of {len(beams)} states with OAM={oam_charges[0]}")
        
        return superposition
    
    def _execute_multiplex(self, node: MultiplexNode) -> Dict[str, Any]:
        """Execute OAM mode multiplexing"""
        beams = [self.execute(beam) for beam in node.beams]
        
        # Extract OAM charges
        oam_charges = []
        valid_beams = []
        for beam in beams:
            if isinstance(beam, dict) and 'oam_charge' in beam:
                oam_charges.append(beam['oam_charge'])
                valid_beams.append(beam)
        
        if not valid_beams:
            raise RuntimeError("No valid OAM beams to multiplex")
        
        # Use OAM physics to multiplex
        multiplexed = self.oam_physics.multiplex_oam_modes(valid_beams, node.method)
        
        print(f"[Interpreter] Multiplexed {len(valid_beams)} OAM modes using {node.method} method")
        print(f"  OAM charges: {oam_charges}")
        print(f"  Capacity: {multiplexed['capacity']} channels, Efficiency: {multiplexed['efficiency']:.1%}")
        
        return multiplexed
    
    def _execute_demultiplex(self, node: DemultiplexNode) -> List[Dict[str, Any]]:
        """Execute OAM mode demultiplexing"""
        input_beam = self.execute(node.input_beam)
        output_modes = [self.execute(mode) for mode in node.output_modes]
        
        if not isinstance(input_beam, dict) or 'oam_charge' not in input_beam:
            raise RuntimeError("Input beam must have OAM charge")
        
        input_oam = input_beam.get('oam_charge', 0)
        
        # Simulate demultiplexing
        results = []
        for i, mode in enumerate(output_modes):
            if isinstance(mode, dict) and 'oam_charge' in mode:
                target_oam = mode['oam_charge']
                efficiency = 0.9 if input_oam == target_oam else 0.1
                
                result = {
                    'type': 'demultiplexed_mode',
                    'input_oam': input_oam,
                    'target_oam': target_oam,
                    'efficiency': efficiency,
                    'detected': efficiency > 0.5,
                    'power': input_beam.get('power', 1.0) * efficiency
                }
                results.append(result)
        
        print(f"[Interpreter] Demultiplexed OAM{input_oam} into {len(results)} output modes")
        return results
    
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
        elif name in self.builtin_functions:
            return {'type': 'builtin_function', 'name': name}
        raise RuntimeError(f"Undefined variable: {name}")
    
    def _execute_binary_op(self, node: BinaryOpNode) -> Any:
        """Execute binary operation"""
        left = self.execute(node.left)
        right = self.execute(node.right)
        
        # Special handling for OAM operations
        if node.op in ['⊕', '⊖', '⊗']:
            return self._execute_oam_binary_op(node.op, left, right)
        
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
    
    def _execute_oam_binary_op(self, op: str, left: Any, right: Any) -> Dict[str, Any]:
        """Execute OAM-specific binary operation"""
        # Extract OAM charges
        oam1 = left.get('oam_charge', 0) if isinstance(left, dict) else 0
        oam2 = right.get('oam_charge', 0) if isinstance(right, dict) else 0
        
        if op == '⊕':  # OAM addition
            result_oam = oam1 + oam2
            print(f"[Interpreter] OAM addition: {oam1} ⊕ {oam2} = {result_oam}")
            return {'type': 'oam_result', 'operation': 'addition', 'result': result_oam}
        
        elif op == '⊖':  # OAM subtraction
            result_oam = oam1 - oam2
            print(f"[Interpreter] OAM subtraction: {oam1} ⊖ {oam2} = {result_oam}")
            return {'type': 'oam_result', 'operation': 'subtraction', 'result': result_oam}
        
        elif op == '⊗':  # OAM tensor product
            # For tensor product, create superposition of products
            result = {
                'type': 'oam_tensor_product',
                'oam1': oam1,
                'oam2': oam2,
                'is_entangled': True,
                'description': f"|OAM{oam1}⟩ ⊗ |OAM{oam2}⟩"
            }
            print(f"[Interpreter] OAM tensor product: |OAM{oam1}⟩ ⊗ |OAM{oam2}⟩")
            return result
        
        raise RuntimeError(f"Unknown OAM operator: {op}")
    
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
        
        # Check built-in functions first
        if node.name in self.builtin_functions:
            args = [self.execute(arg) for arg in node.arguments]
            return self.builtin_functions[node.name](*args)
        
        # Try to execute user-defined function
        if node.name in self.symbol_table:
            func_node = self.symbol_table[node.name]
            if isinstance(func_node, FunctionDeclNode):
                return self._execute_user_function(func_node, node.arguments)
        
        raise RuntimeError(f"Unknown function: {node.name}")
    
    def _execute_user_function(
        self, 
        func_node: FunctionDeclNode, 
        args: List[Any]
    ) -> Any:
        """Execute user-defined function"""
        print(f"[Interpreter] Executing user function: {func_node.name}")
        
        # Save current symbol table
        old_symbols = self.symbol_table.copy()
        
        # Bind arguments to parameters
        for param, arg in zip(func_node.parameters, args):
            self.symbol_table[param] = arg
        
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
        loop_count = 0
        while self.execute(node.condition) and loop_count < 100:  # Safety limit
            for stmt in node.body:
                self.execute(stmt)
            loop_count += 1
        
        if loop_count >= 100:
            print("[Interpreter] WARNING: While loop exceeded safety limit")
    
    # Built-in functions
    
    def _builtin_encode_matrix(self, matrix_data):
        """Built-in: encode_matrix"""
        print(f"[Interpreter] Encoding matrix: {matrix_data.get('rows', '?')}x{matrix_data.get('cols', '?')}")
        return {
            'type': 'encoded_matrix',
            'original': matrix_data,
            'optical_format': 'MZI_mesh',
            'timestamp': 'simulated'
        }
    
    def _builtin_optical_matmul(self, matrix_a, matrix_b):
        """Built-in: optical_matmul"""
        print(f"[Interpreter] Optical matrix multiplication")
        return self._matrix_multiply(matrix_a, matrix_b)
    
    def _builtin_measure_optical_matrix(self, matrix):
        """Built-in: measure_optical_matrix"""
        print(f"[Interpreter] Measuring optical matrix")
        # Simulate measurement by squaring amplitudes (intensity)
        if isinstance(matrix, dict) and matrix.get('type') == 'matrix':
            result = {
                'type': 'electrical',
                'rows': matrix['rows'],
                'cols': matrix['cols'],
                'value': [[element * element for element in row] for row in matrix['value']]
            }
            return result
        return matrix
    
    def _builtin_calculate_oam_spectrum(self, beams):
        """Built-in: calculate_oam_spectrum"""
        print(f"[Interpreter] Calculating OAM spectrum")
        
        if not isinstance(beams, list):
            beams = [beams]
        
        # Extract OAM charges
        oam_charges = []
        for beam in beams:
            if isinstance(beam, dict) and 'oam_charge' in beam:
                oam_charges.append(beam['oam_charge'])
        
        # Calculate spectrum using OAM physics
        spectrum = self.oam_physics.calculate_oam_spectrum(beams)
        
        return {
            'type': 'oam_spectrum',
            'charges': list(range(-10, 11)),
            'intensities': spectrum,
            'total_modes': len(oam_charges),
            'unique_charges': len(set(oam_charges))
        }
    
    def _builtin_create_vortex_array(self, oam_charges, spacing=1.0):
        """Built-in: create_vortex_array"""
        print(f"[Interpreter] Creating vortex array with charges: {oam_charges}")
        
        if not isinstance(oam_charges, list):
            oam_charges = [oam_charges]
        
        return self.oam_physics.create_vortex_array(oam_charges, spacing)
    
    def run(self, ast: ProgramNode) -> None:
        """Run the interpreter on an AST"""
        print("[Interpreter] Starting execution...")
        print("=" * 50)
        self.execute(ast)
        print("=" * 50)
        print("[Interpreter] Execution completed!")
