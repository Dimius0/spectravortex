"""
Визуализация топологических архитектур.
Упрощенная версия без HTML-шаблонов.
"""

import numpy as np

def plot_3d_architecture(positions, charges=None, title="Топологическая архитектура"):
    """
    Визуализация архитектуры в 3D.
    Требует matplotlib.
    """
    try:
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D
    except ImportError:
        print("⚠️  Для визуализации установите matplotlib: pip install matplotlib")
        return None
    
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Преобразуем в numpy
    pos_array = np.array(positions)
    
    if len(pos_array) == 0:
        print("⚠️  Нет компонентов для визуализации")
        return fig
    
    # Разделяем координаты
    x = pos_array[:, 0]
    y = pos_array[:, 1]
    z = pos_array[:, 2]
    
    # Цвета по зарядам
    if charges is not None:
        colors = []
        for charge in charges:
            if charge > 0:
                colors.append('red')
            elif charge < 0:
                colors.append('blue')
            else:
                colors.append('gray')
    else:
        colors = ['green'] * len(positions)
    
    # Размер точек
    sizes = [100 + abs(charge * 50) if charges else 100 for charge in (charges or [1]*len(x))]
    
    # Точечный график
    ax.scatter(x, y, z, c=colors, s=sizes, alpha=0.8, edgecolors='black')
    
    # Настройки
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title(title)
    ax.grid(True)
    
    plt.tight_layout()
    return fig

def plot_field_slices(phi_field, title="Поле фазы φ"):
    """
    Визуализация срезов поля φ.
    Требует matplotlib.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("⚠️  Для визуализации установите matplotlib: pip install matplotlib")
        return None
    
    nz, ny, nx = phi_field.shape
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # XY срез
    z_slice = nz // 2
    im1 = axes[0, 0].imshow(phi_field[z_slice, :, :], cmap='RdBu', origin='lower')
    axes[0, 0].set_title(f'XY срез (z={z_slice}/{nz})')
    plt.colorbar(im1, ax=axes[0, 0])
    
    # XZ срез
    y_slice = ny // 2
    im2 = axes[0, 1].imshow(phi_field[:, y_slice, :], cmap='RdBu', origin='lower')
    axes[0, 1].set_title(f'XZ срез (y={y_slice}/{ny})')
    plt.colorbar(im2, ax=axes[0, 1])
    
    # YZ срез
    x_slice = nx // 2
    im3 = axes[1, 0].imshow(phi_field[:, :, x_slice], cmap='RdBu', origin='lower')
    axes[1, 0].set_title(f'YZ срез (x={x_slice}/{nx})')
    plt.colorbar(im3, ax=axes[1, 0])
    
    # Информация
    axes[1, 1].text(0.5, 0.5, f'Размер: {phi_field.shape}\nmin: {phi_field.min():.2f}\nmax: {phi_field.max():.2f}', 
                   ha='center', va='center')
    axes[1, 1].axis('off')
    
    fig.suptitle(title)
    plt.tight_layout()
    return fig

def plot_energy_density(phi_field, title="Плотность энергии"):
    """
    Визуализация плотности энергии.
    Требует matplotlib.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("⚠️  Для визуализации установите matplotlib: pip install matplotlib")
        return None
    
    # Вычисляем градиент
    grad_x = np.gradient(phi_field, axis=2)
    grad_y = np.gradient(phi_field, axis=1)
    grad_z = np.gradient(phi_field, axis=0)
    
    # Плотность энергии
    energy = (grad_x**2 + grad_y**2 + grad_z**2) / 2
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Сумма по осям
    im1 = axes[0].imshow(np.sum(energy, axis=0), cmap='hot', origin='lower')
    axes[0].set_title('Сумма по Z')
    plt.colorbar(im1, ax=axes[0])
    
    # Максимальное значение
    im2 = axes[1].imshow(np.max(energy, axis=0), cmap='hot', origin='lower')
    axes[1].set_title('Максимум по Z')
    plt.colorbar(im2, ax=axes[1])
    
    fig.suptitle(title)
    plt.tight_layout()
    return fig
