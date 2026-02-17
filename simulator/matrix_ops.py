# simulator/matrix_ops.py
"""
Matrix operations for SpectraVortex interpreter
"""

class MatrixOperations:
    """Matrix operations for optical computing simulation"""
    
    @staticmethod
    def multiply(a, b):
        """Multiply two matrices"""
        # Проверяем, что это матрицы
        if not isinstance(a, dict) or a.get('type') != 'matrix':
            raise TypeError(f"First argument must be a matrix, got {type(a)}")
        if not isinstance(b, dict) or b.get('type') != 'matrix':
            raise TypeError(f"Second argument must be a matrix, got {type(b)}")
        
        # Используем сохраненные размеры
        a_rows, a_cols = a['rows'], a['cols']
        b_rows, b_cols = b['rows'], b['cols']
        
        if a_cols != b_rows:
            raise ValueError(f"Cannot multiply {a_rows}x{a_cols} matrix by {b_rows}x{b_cols} matrix")
        
        result = [[0.0 for _ in range(b_cols)] for _ in range(a_rows)]
        
        for i in range(a_rows):
            for j in range(b_cols):
                for k in range(a_cols):
                    result[i][j] += a['value'][i][k] * b['value'][k][j]
        
        return {
            'type': 'matrix',
            'rows': a_rows,
            'cols': b_cols,
            'value': result
        }
    
    @staticmethod
    def simulate_mzi_mesh(matrix_data):
        """
        Simulate Mach-Zehnder Interferometer mesh for optical
        matrix multiplication
        """
        print(f"[MatrixOps] Configuring {matrix_data['rows']}x{matrix_data['cols']} MZI mesh")
        
        # В реальной реализации здесь была бы оптическая симуляция
        # интерференции в массиве интерферометров Маха-Цендера
        return matrix_data
    
    @staticmethod
    def format_matrix(matrix):
        """Format matrix for display"""
        if not isinstance(matrix, dict) or matrix.get('type') != 'matrix':
            return str(matrix)
        
        rows = matrix['value']
        if not rows:
            return "[]"
        
        formatted = "["
        for i, row in enumerate(rows):
            if i > 0:
                formatted += " "
            formatted += "["
            formatted += ", ".join(f"{val:.4f}" if isinstance(val, float) else str(val) for val in row)
            formatted += "]"
            if i < len(rows) - 1:
                formatted += "\n"
        formatted += "]"
        return formatted
    
    @staticmethod
    def matrix_to_string(matrix):
        """Convert matrix to string representation (compatible with print)"""
        if not isinstance(matrix, dict) or matrix.get('type') != 'matrix':
            return str(matrix)
        
        return f"Matrix({matrix['rows']}x{matrix['cols']}): {MatrixOperations.format_matrix(matrix)}"
