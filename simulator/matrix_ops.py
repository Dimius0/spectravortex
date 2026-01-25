# simulator/matrix_ops.py
class MatrixOperations:
    @staticmethod
    def multiply(a, b):
        """Умножение двух матриц"""
        a_rows, a_cols = len(a['value']), len(a['value'][0])
        b_rows, b_cols = len(b['value']), len(b['value'][0])
        
        if a_cols != b_rows:
            raise ValueError(f"Matrix dimensions mismatch: {a_rows}x{a_cols} vs {b_rows}x{b_cols}")
        
        result = [[0.0 for _ in range(b_cols)] for _ in range(a_rows)]
        
        for i in range(a_rows):
            for j in range(b_cols):
                for k in range(a_cols):
                    result[i][j] += a['value'][i][k] * b['value'][k][j]
        
        return {
            'rows': a_rows,
            'cols': b_cols,
            'value': result
        }
    
    @staticmethod
    def simulate_mzi_mesh(matrix_data):
        """
        Симуляция интерферометра Маха-Цендера для оптического
        матричного умножения
        """
        # Упрощенная модель: каждый MZI реализует элементарное вращение
        # В реальности это была бы сложная оптическая схема
        print(f"[MZI Mesh] Configuring {len(matrix_data)}x{len(matrix_data[0])} interferometer array")
        return matrix_data
