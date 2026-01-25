class Simulator:
    def __init__(self):
        self.symbol_table = {}
        self.matrix_operations = MatrixOperations()
    
    def execute(self, ast_node):
        # ... существующий код ...
        
        # Добавьте обработку новых типов узлов
        if node_type == 'matrix_literal':
            return self.handle_matrix_literal(node)
        elif node_type == 'matrix_multiplication':
            return self.handle_matrix_multiplication(node)
        elif node_type == 'function_call':
            return self.handle_function_call(node)
        
        # ... продолжение существующего кода ...
    
    def handle_matrix_literal(self, node):
        """Создание матрицы из литерала"""
        matrix_data = {
            'rows': int(node.rows),
            'cols': int(node.cols),
            'value': [[float(val) for val in row] for row in node.values]
        }
        return {'type': 'matrix', 'data': matrix_data}
    
    def handle_matrix_multiplication(self, node):
        """Выполнение матричного умножения"""
        left = self.execute(node.left)
        right = self.execute(node.right)
        
        if left['type'] != 'matrix' or right['type'] != 'matrix':
            raise RuntimeError("Both operands must be matrices for multiplication")
        
        result = self.matrix_operations.multiply(left['data'], right['data'])
        return {'type': 'matrix', 'data': result}
    
    def handle_function_call(self, node):
        """Вызов функций encode_matrix, optical_matmul и т.д."""
        func_name = node.func_name
        
        if func_name == 'encode_matrix':
            arg = self.execute(node.args[0])
            return self.encode_matrix(arg)
        elif func_name == 'optical_matmul':
            a = self.execute(node.args[0])
            b = self.execute(node.args[1])
            return self.optical_matmul(a, b)
        elif func_name == 'measure_optical_matrix':
            arg = self.execute(node.args[0])
            return self.measure_optical_matrix(arg)
        elif func_name == 'print':
            # ... существующая реализация print ...
            pass
    
    def encode_matrix(self, matrix_data):
        """Симуляция кодирования матрицы в оптические сигналы"""
        print(f"[SIM] Encoding matrix {matrix_data['rows']}x{matrix_data['cols']} to optical modes")
        return {'type': 'optical_matrix', 'data': matrix_data['value']}
    
    def optical_matmul(self, optical_a, optical_b):
        """Симуляция оптического матричного умножения"""
        a_data = optical_a['data']
        b_data = optical_b['data']
        
        # Простое матричное умножение для демонстрации
        rows_a = len(a_data)
        cols_a = len(a_data[0]) if rows_a > 0 else 0
        cols_b = len(b_data[0]) if len(b_data) > 0 else 0
        
        result = [[0.0 for _ in range(cols_b)] for _ in range(rows_a)]
        
        for i in range(rows_a):
            for j in range(cols_b):
                for k in range(cols_a):
                    result[i][j] += a_data[i][k] * b_data[k][j]
        
        print(f"[SIM] Optical matrix multiplication completed")
        return {'type': 'optical_matrix', 'data': result}
