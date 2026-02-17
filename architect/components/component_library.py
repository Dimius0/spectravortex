"""
Библиотека предопределённых компонентов.
"""

COMPONENT_LIBRARY = {
    # КВАНТОВЫЕ КОМПОНЕНТЫ
    "transmon_qubit": {
        "type": "quantum",
        "tau": 2.0,
        "physical": {
            "power": 0.001,
            "size": [0.01, 0.01, 0.005],
            "frequency": 5.0,
            "coherence_time": 50.0
        },
        "constraints": {
            "min_temperature": 0.015,
            "max_magnetic_field": 0.001,
            "isolation_required": True
        }
    },
    
    "fluxonium_qubit": {
        "type": "quantum",
        "tau": 2.0,
        "physical": {
            "power": 0.0005,
            "size": [0.015, 0.015, 0.008],
            "frequency": 3.5,
            "coherence_time": 100.0
        }
    },
    
    # ФОТОННЫЕ КОМПОНЕНТЫ
    "si_photonic_modulator": {
        "type": "photonic",
        "tau": -1.0,
        "physical": {
            "power": 0.01,
            "size": [0.1, 0.01, 0.01],
            "bandwidth": 40.0,
            "insertion_loss": 2.0,
            "wavelength": 1550.0
        }
    },
    
    "microring_resonator": {
        "type": "photonic",
        "tau": -1.0,
        "physical": {
            "power": 0.005,
            "size": [0.02, 0.02, 0.01],
            "q_factor": 10000.0,
            "free_spectral_range": 10.0
        }
    },
    
    # ЭЛЕКТРОННЫЕ КОМПОНЕНТЫ
    "finfet_processor": {
        "type": "electronic",
        "tau": 1.0,
        "physical": {
            "power": 5.0,
            "size": [1.0, 1.0, 0.1],
            "clock_speed": 3.5,
            "cores": 8,
            "thermal_limit": 85.0
        }
    },
    
    "hbm_memory": {
        "type": "electronic",
        "tau": 1.0,
        "physical": {
            "power": 3.0,
            "size": [1.5, 0.5, 0.2],
            "bandwidth": 256.0,
            "capacity": 16.0,
            "latency": 50.0
        }
    },
    
    # ИНТЕРФЕЙСЫ
    "optical_interconnect": {
        "type": "photonic",
        "tau": -0.5,
        "physical": {
            "power": 0.1,
            "size": [0.2, 0.2, 0.05],
            "data_rate": 100.0,
            "channels": 8
        }
    },
    
    "superconducting_bus": {
        "type": "quantum",
        "tau": 1.0,
        "physical": {
            "power": 0.0001,
            "size": [0.5, 0.02, 0.01],
            "frequency": 6.0,
            "coupling_strength": 0.05
        }
    }
}

def get_component_spec(component_name):
    """
    Возвращает спецификацию компонента по имени.
    
    Args:
        component_name: имя компонента из библиотеки
        
    Returns:
        Спецификация компонента или None если не найден
    """
    return COMPONENT_LIBRARY.get(component_name)

def create_component_from_library(name, component_id=None):
    """
    Создаёт компонент из библиотеки.
    
    Args:
        name: имя компонента в библиотеке
        component_id: уникальный ID компонента
        
    Returns:
        Словарь с описанием компонента
    """
    spec = get_component_spec(name)
    if not spec:
        raise ValueError(f"Компонент '{name}' не найден в библиотеке")
    
    return {
        "id": component_id or f"{name}_1",
        "type": spec["type"],
        "library_name": name,
        "tau": spec["tau"],
        "physical": spec["physical"].copy(),
        "constraints": spec.get("constraints", {}).copy()
    }

def list_available_components(component_type=None):
    """
    Список доступных компонентов.
    
    Args:
        component_type: фильтр по типу (quantum/photonic/electronic)
        
    Returns:
        Список имён компонентов
    """
    if component_type:
        return [name for name, spec in COMPONENT_LIBRARY.items() 
                if spec["type"] == component_type]
    else:
        return list(COMPONENT_LIBRARY.keys())
