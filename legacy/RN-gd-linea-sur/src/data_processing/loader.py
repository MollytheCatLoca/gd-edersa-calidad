"""
Module: loader
Purpose: Data loading utilities for various file formats
Author: Claude AI Assistant
Date: 2025-07-06
Version: 1.0.0
"""

import pandas as pd
import xlrd
from pathlib import Path
from typing import Union, List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class DataLoader:
    """Handles loading data from various sources and formats."""
    
    def __init__(self, base_path: Union[str, Path] = None):
        """
        Initialize DataLoader.
        
        Parameters
        ----------
        base_path : str or Path, optional
            Base path for data files
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
    
    def load_excel(self, file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
        """
        Load data from Excel file (.xls or .xlsx).
        
        Parameters
        ----------
        file_path : str or Path
            Path to Excel file
        **kwargs : dict
            Additional arguments for pd.read_excel
            
        Returns
        -------
        pd.DataFrame
            Loaded data
        """
        file_path = Path(file_path)
        
        try:
            if file_path.suffix == '.xls':
                # Use xlrd for old format
                df = pd.read_excel(file_path, engine='xlrd', **kwargs)
            else:
                # Use openpyxl for new format
                df = pd.read_excel(file_path, engine='openpyxl', **kwargs)
            
            logger.info(f"Loaded {len(df)} rows from {file_path.name}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            raise
    
    def load_measurement_file(self, file_path: Union[str, Path]) -> pd.DataFrame:
        """
        Load EPRE measurement file with specific format.
        
        Parameters
        ----------
        file_path : str or Path
            Path to measurement file
            
        Returns
        -------
        pd.DataFrame
            Processed measurement data
        """
        file_path = Path(file_path)
        logger.info(f"Loading measurement file: {file_path.name}")
        
        try:
            # Load Excel file
            df = self.load_excel(file_path, header=None)
            
            # Extract metadata from filename
            filename = file_path.stem
            parts = filename.split()
            
            # Determine station and measurement type
            if 'ET4PI' in filename:
                station = 'Pilcaniyeu'
                voltage_level = '33kV' if '_33' in filename else '13.2kV'
            elif 'ET2IJ' in filename:
                station = 'Jacobacci'
                voltage_level = 'NORTE' if 'NORTE' in filename else 'SUR'
            elif 'ET2MA' in filename:
                station = 'Maquinchao'
                voltage_level = '33kV'
            elif 'ET2LM' in filename:
                station = 'Los Menucos'
                voltage_level = '33kV'
            else:
                station = 'Unknown'
                voltage_level = 'Unknown'
            
            # Process data based on EPRE format
            processed_df = self._process_epre_format(df, station, voltage_level)
            
            return processed_df
            
        except Exception as e:
            logger.error(f"Error processing measurement file {file_path}: {e}")
            raise
    
    def _process_epre_format(self, df: pd.DataFrame, station: str, voltage_level: str) -> pd.DataFrame:
        """
        Process EPRE format data.
        
        The EPRE format typically has:
        - Row 0-4: Headers and metadata
        - Row 5+: Data with columns for Date, Time, V1, V2, V3, I1, I2, I3, P, Q, FP
        """
        logger.debug(f"Processing EPRE format. Initial shape: {df.shape}")
        
        # Try to read with header
        # First, let's check if we can use the Excel file directly with header detection
        if df.empty:
            logger.warning("Empty dataframe received")
            return pd.DataFrame()
        
        # Skip header rows and find data start
        data_start_row = 0
        for i in range(min(20, len(df))):
            first_cell = df.iloc[i, 0]
            if pd.notna(first_cell):
                # Check if this looks like a date (could be number or string)
                if isinstance(first_cell, (int, float)) and first_cell > 40000:  # Excel date
                    data_start_row = i
                    logger.info(f"Found data starting at row {i} (Excel date format)")
                    break
                elif isinstance(first_cell, str) and ('/' in first_cell or '-' in first_cell):
                    data_start_row = i
                    logger.info(f"Found data starting at row {i} (String date format)")
                    break
        
        # If no data found, try default
        if data_start_row == 0:
            logger.warning("Could not detect data start, trying default row 5")
            data_start_row = 5
        
        # Extract data
        data_df = df.iloc[data_start_row:].copy()
        
        # Reset index
        data_df = data_df.reset_index(drop=True)
        
        # Define column names based on typical EPRE format
        columns = ['fecha', 'hora', 'v1', 'v2', 'v3', 'i1', 'i2', 'i3', 
                   'p_total', 'q_total', 'fp', 'frecuencia']
        
        # Assign columns (adjust based on actual number of columns)
        num_cols = min(len(columns), data_df.shape[1])
        data_df.columns = columns[:num_cols]
        
        logger.info(f"Data shape after extraction: {data_df.shape}")
        
        # Check first few rows
        if len(data_df) > 0:
            logger.debug(f"First fecha value: {data_df.iloc[0]['fecha']} (type: {type(data_df.iloc[0]['fecha'])})")
            logger.debug(f"First hora value: {data_df.iloc[0]['hora']} (type: {type(data_df.iloc[0]['hora'])})")
        
        # Clean and convert data types
        data_df = data_df.dropna(subset=['fecha', 'hora'])
        
        # Parse datetime - handle different formats
        if len(data_df) > 0:
            first_date = data_df.iloc[0]['fecha']
            
            # If fecha is numeric (Excel date), convert it first
            if isinstance(first_date, (int, float)):
                # Excel stores dates as days since 1900-01-01
                data_df['fecha'] = pd.to_datetime('1899-12-30') + pd.to_timedelta(data_df['fecha'], unit='D')
                data_df['timestamp'] = data_df['fecha'] + pd.to_timedelta(data_df['hora'].astype(str))
            else:
                # Try standard parsing
                data_df['timestamp'] = pd.to_datetime(
                    data_df['fecha'].astype(str) + ' ' + data_df['hora'].astype(str),
                    errors='coerce',
                    dayfirst=True  # Try day-first format common in Argentina
                )
        
        # Convert numeric columns
        numeric_cols = ['v1', 'v2', 'v3', 'i1', 'i2', 'i3', 'p_total', 'q_total', 'fp']
        for col in numeric_cols:
            if col in data_df.columns:
                data_df[col] = pd.to_numeric(data_df[col], errors='coerce')
        
        # Add metadata
        data_df['station'] = station
        data_df['voltage_level'] = voltage_level
        
        # Calculate additional metrics
        if all(col in data_df.columns for col in ['v1', 'v2', 'v3']):
            data_df['v_avg'] = data_df[['v1', 'v2', 'v3']].mean(axis=1)
            data_df['v_min'] = data_df[['v1', 'v2', 'v3']].min(axis=1)
            data_df['v_max'] = data_df[['v1', 'v2', 'v3']].max(axis=1)
        
        # Remove invalid timestamps
        data_df = data_df[data_df['timestamp'].notna()]
        
        logger.info(f"Processed {len(data_df)} records for {station} - {voltage_level}")
        
        return data_df
    
    def load_all_station_data(self, station_name: str, year: int = None) -> pd.DataFrame:
        """
        Load all available data for a specific station.
        
        Parameters
        ----------
        station_name : str
            Name of the station (Pilcaniyeu, Jacobacci, Maquinchao, Los Menucos)
        year : int, optional
            Specific year to load, if None loads all available years
            
        Returns
        -------
        pd.DataFrame
            Combined data for the station
        """
        # Map station names to folder names
        station_map = {
            'Pilcaniyeu': 'Pilcaniyeu',
            'Jacobacci': 'Jacobacci',
            'Maquinchao': 'Maquinchao',
            'Los Menucos': 'Menucos',
            'Menucos': 'Menucos'
        }
        
        folder_name = station_map.get(station_name, station_name)
        base_path = self.base_path / "data" / "Registros Línea Sur"
        
        all_data = []
        
        # Get year folders
        if year:
            year_folders = [base_path / f"{folder_name}{year}"]
        else:
            year_folders = [f for f in base_path.glob(f"{folder_name}*") if f.is_dir()]
        
        for year_folder in year_folders:
            if not year_folder.exists():
                logger.warning(f"Year folder not found: {year_folder}")
                continue
            
            # Process each month folder
            for month_folder in sorted(year_folder.glob("*")):
                if not month_folder.is_dir():
                    continue
                
                # Process each Excel file in the month
                for excel_file in month_folder.glob("*.xls*"):
                    try:
                        df = self.load_measurement_file(excel_file)
                        if not df.empty:
                            # Add month/year metadata
                            df['year'] = int(year_folder.name[-4:])
                            df['month'] = month_folder.name[:2]
                            all_data.append(df)
                    except Exception as e:
                        logger.warning(f"Error loading {excel_file}: {e}")
                        continue
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            combined_df = combined_df.sort_values('timestamp')
            logger.info(f"Loaded {len(combined_df)} total records for {station_name}")
            return combined_df
        else:
            logger.warning(f"No data found for station {station_name}")
            return pd.DataFrame()
    
    def load_all_stations_data(self, year: int = None) -> Dict[str, pd.DataFrame]:
        """
        Load data for all stations.
        
        Parameters
        ----------
        year : int, optional
            Specific year to load
            
        Returns
        -------
        dict
            Dictionary with station names as keys and DataFrames as values
        """
        stations = ['Pilcaniyeu', 'Jacobacci', 'Maquinchao', 'Los Menucos']
        all_station_data = {}
        
        for station in stations:
            logger.info(f"Loading data for {station}...")
            df = self.load_all_station_data(station, year)
            if not df.empty:
                all_station_data[station] = df
        
        return all_station_data