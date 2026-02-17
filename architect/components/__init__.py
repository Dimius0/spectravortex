"""
Библиотека компонентов для топологического синтеза.
"""

try:
    from .component_library import COMPONENT_LIBRARY, get_component_spec
    from .component_library import create_component_from_library, list_available_components
    
    __all__ = [
        'COMPONENT_LIBRARY', 
        'get_component_spec',
        'create_component_from_library',
        'list_available_components'
    ]
except ImportError:
    # Заглушка если основной файл не загружается
    COMPONENT_LIBRARY = {}
    
    def get_component_spec(name):
        return None
    
    def create_component_from_library(name, component_id=None):
        return {"id": component_id or name, "type": "electronic", "tau": 1.0}
    
    def list_available_components(component_type=None):
        return []
    
    __all__ = [
        'COMPONENT_LIBRARY', 
        'get_component_spec',
        'create_component_from_library',
        'list_available_components'
    ]
