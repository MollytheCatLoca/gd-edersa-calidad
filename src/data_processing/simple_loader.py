"""
Simple loader for EPRE Excel files with robust error handling
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def load_epre_file(file_path):
    """
    Load EPRE Excel file with automatic format detection.
    """
    file_path = Path(file_path)
    logger.info(f"Loading: {file_path.name}")
    
    try:
        # First try: Read with pandas automatic detection
        df = pd.read_excel(file_path)
        
        # Check if we got meaningful data
        if len(df) > 0 and len(df.columns) > 5:
            logger.info(f"  Auto-detection successful: {len(df)} rows, {len(df.columns)} columns")
            
            # Standardize column names if possible
            if 'Fecha' in df.columns or 'fecha' in df.columns or df.columns[0].lower() == 'fecha':
                return process_auto_detected(df, file_path.stem)
        
        # Second try: Read without header and detect manually
        df_raw = pd.read_excel(file_path, header=None)
        logger.info(f"  Manual detection: {df_raw.shape}")
        
        # Find where data starts
        data_start = find_data_start(df_raw)
        if data_start >= 0:
            return process_manual_format(df_raw, data_start, file_path.stem)
        
        logger.warning(f"  Could not process {file_path.name}")
        return pd.DataFrame()
        
    except Exception as e:
        logger.error(f"  Error loading {file_path.name}: {e}")
        return pd.DataFrame()


def find_data_start(df):
    """Find where actual data starts in the Excel file."""
    for i in range(min(20, len(df))):
        row = df.iloc[i]
        # Check if first column looks like a date
        if pd.notna(row[0]):
            # Excel numeric date
            if isinstance(row[0], (int, float)) and 40000 < row[0] < 50000:
                return i
            # String date
            if isinstance(row[0], str) and ('/' in row[0] or '-' in row[0]):
                return i
    return -1


def process_auto_detected(df, filename):
    """Process dataframe that was auto-detected by pandas."""
    # Standardize column names
    col_mapping = {
        'Fecha': 'fecha',
        'Hora': 'hora',
        'Tension R': 'v1',
        'Tension S': 'v2', 
        'Tension T': 'v3',
        'Corriente R': 'i1',
        'Corriente S': 'i2',
        'Corriente T': 'i3',
        'Potencia Activa': 'p_total',
        'Potencia Reactiva': 'q_total',
        'Factor de Potencia': 'fp'
    }
    
    # Rename columns if they match
    df.columns = [col_mapping.get(col, col.lower()) for col in df.columns]
    
    # Extract station info from filename
    station_info = extract_station_info(filename)
    
    # Add metadata
    df['station'] = station_info['station']
    df['voltage_level'] = station_info['voltage_level']
    
    # Create timestamp
    if 'fecha' in df.columns and 'hora' in df.columns:
        df['timestamp'] = pd.to_datetime(
            df['fecha'].astype(str) + ' ' + df['hora'].astype(str),
            errors='coerce'
        )
    
    # Calculate voltage average
    if all(col in df.columns for col in ['v1', 'v2', 'v3']):
        df['v_avg'] = df[['v1', 'v2', 'v3']].mean(axis=1)
    
    # Clean
    df = df.dropna(subset=['timestamp'])
    
    logger.info(f"  Processed {len(df)} valid records")
    return df


def process_manual_format(df_raw, start_row, filename):
    """Process dataframe with manual format detection."""
    # Extract data
    data = df_raw.iloc[start_row:].copy()
    data = data.reset_index(drop=True)
    
    # Assign column names
    columns = ['fecha', 'hora', 'v1', 'v2', 'v3', 'i1', 'i2', 'i3', 
               'p_total', 'q_total', 'fp', 'frecuencia']
    
    num_cols = min(len(columns), data.shape[1])
    data.columns = columns[:num_cols]
    
    # Extract station info
    station_info = extract_station_info(filename)
    data['station'] = station_info['station']
    data['voltage_level'] = station_info['voltage_level']
    
    # Handle Excel dates
    if len(data) > 0 and isinstance(data.iloc[0]['fecha'], (int, float)):
        # Convert Excel date
        data['fecha'] = pd.to_datetime('1899-12-30') + pd.to_timedelta(data['fecha'], unit='D')
    
    # Create timestamp
    try:
        if 'hora' in data.columns:
            # Handle time - could be fraction of day or string
            if isinstance(data.iloc[0]['hora'], (int, float)):
                # Time as fraction of day
                data['hora_td'] = pd.to_timedelta(data['hora'], unit='D')
                data['timestamp'] = data['fecha'] + data['hora_td']
            else:
                # Time as string
                data['timestamp'] = pd.to_datetime(
                    data['fecha'].astype(str) + ' ' + data['hora'].astype(str),
                    errors='coerce'
                )
    except:
        data['timestamp'] = pd.NaT
    
    # Convert numeric columns
    numeric_cols = ['v1', 'v2', 'v3', 'i1', 'i2', 'i3', 'p_total', 'q_total', 'fp']
    for col in numeric_cols:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors='coerce')
    
    # Calculate voltage average
    if all(col in data.columns for col in ['v1', 'v2', 'v3']):
        data['v_avg'] = data[['v1', 'v2', 'v3']].mean(axis=1)
    
    # Clean
    data = data.dropna(subset=['timestamp'])
    data = data[data['timestamp'].notna()]
    
    logger.info(f"  Processed {len(data)} valid records")
    return data


def extract_station_info(filename):
    """Extract station and voltage level from filename."""
    info = {
        'station': 'Unknown',
        'voltage_level': 'Unknown'
    }
    
    if 'ET4PI' in filename:
        info['station'] = 'Pilcaniyeu'
        info['voltage_level'] = '33kV' if '_33' in filename else '13.2kV'
    elif 'ET2IJ' in filename:
        info['station'] = 'Jacobacci'
        info['voltage_level'] = 'NORTE' if 'NORTE' in filename else 'SUR'
    elif 'ET2MA' in filename:
        info['station'] = 'Maquinchao'
        info['voltage_level'] = '33kV'
    elif 'ET2LM' in filename:
        info['station'] = 'Los Menucos'
        info['voltage_level'] = '33kV'
    
    return info