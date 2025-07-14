"""
Utilities package for dashboard pages
"""

# MIGRACIÓN COMPLETA A DataManagerV2 - Todos los imports van a V2
from .data_manager_v2 import get_data_manager, DataManagerV2
from .constants import DataStatus

# Alias para compatibilidad
DataManager = DataManagerV2

__all__ = ['get_data_manager', 'DataStatus', 'DataManager', 'DataManagerV2']