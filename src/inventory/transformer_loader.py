"""
Cargador de inventario de transformadores EDERSA
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class Transformer:
    """Modelo de datos para transformador"""
    codigo: str
    sucursal: str
    alimentador: str
    potencia_kva: float
    usuarios: int
    localidad: str
    coord_x: Optional[float] = None
    coord_y: Optional[float] = None
    resultado: Optional[str] = None
    penalized: bool = False
    
    @property
    def has_coordinates(self) -> bool:
        return self.coord_x is not None and self.coord_y is not None
    
    @property
    def quality_score(self) -> float:
        """Score de calidad: 1.0 = Correcta, 0.5 = Penalizada, 0.0 = Fallida"""
        if self.resultado == 'Correcta':
            return 1.0
        elif self.resultado == 'Penalizada':
            return 0.5
        elif self.resultado == 'Fallida':
            return 0.0
        return np.nan


class TransformerInventoryLoader:
    """Carga y procesa el inventario de transformadores EDERSA"""
    
    def __init__(self, data_path: Path):
        self.data_path = data_path
        self.raw_data = None
        self.transformers = []
        
    def load_excel(self, file_name: str = "Mediciones Originales EDERSA.xlsx") -> pd.DataFrame:
        """Carga el archivo Excel de EDERSA"""
        file_path = self.data_path / "raw" / file_name
        logger.info(f"Cargando inventario desde {file_path}")
        
        try:
            self.raw_data = pd.read_excel(file_path, sheet_name='Hoja 1')
            logger.info(f"Cargados {len(self.raw_data)} registros")
            return self.raw_data
        except Exception as e:
            logger.error(f"Error cargando archivo: {e}")
            raise
            
    def process_inventory(self) -> List[Transformer]:
        """Procesa el inventario y crea objetos Transformer"""
        if self.raw_data is None:
            raise ValueError("Debe cargar los datos primero con load_excel()")
            
        transformers = []
        
        for idx, row in self.raw_data.iterrows():
            try:
                transformer = Transformer(
                    codigo=str(row['Codigoct']),
                    sucursal=str(row['N_Sucursal']) if pd.notna(row['N_Sucursal']) else 'SIN_SUCURSAL',
                    alimentador=str(row['Alimentador']) if pd.notna(row['Alimentador']) else 'SIN_ALIMENTADOR',
                    potencia_kva=float(row['Potencia']) if pd.notna(row['Potencia']) else 0.0,
                    usuarios=int(row['Q_Usuarios']) if pd.notna(row['Q_Usuarios']) else 0,
                    localidad=str(row['N_Localida']) if pd.notna(row['N_Localida']) else 'SIN_LOCALIDAD',
                    coord_x=float(row['Coord_X']) if pd.notna(row['Coord_X']) else None,
                    coord_y=float(row['Coord_Y']) if pd.notna(row['Coord_Y']) else None,
                    resultado=str(row['Resultado']) if pd.notna(row['Resultado']) else None,
                    penalized=row['Resultado'] in ['Penalizada', 'Fallida'] if pd.notna(row['Resultado']) else False
                )
                transformers.append(transformer)
            except Exception as e:
                logger.warning(f"Error procesando registro {idx}: {e}")
                continue
                
        self.transformers = transformers
        logger.info(f"Procesados {len(transformers)} transformadores")
        return transformers
        
    def get_summary(self) -> Dict:
        """Genera resumen del inventario"""
        if not self.transformers:
            raise ValueError("Debe procesar el inventario primero")
            
        df = pd.DataFrame([t.__dict__ for t in self.transformers])
        
        summary = {
            'total_transformers': len(self.transformers),
            'total_capacity_mva': df['potencia_kva'].sum() / 1000,
            'total_users': df['usuarios'].sum(),
            'transformers_with_quality': df['resultado'].notna().sum(),
            'penalized_transformers': df['penalized'].sum(),
            'transformers_with_coordinates': sum(t.has_coordinates for t in self.transformers),
            'by_branch': df.groupby('sucursal').size().to_dict(),
            'by_feeder': df.groupby('alimentador').size().to_dict(),
            'quality_distribution': df['resultado'].value_counts().to_dict()
        }
        
        return summary
