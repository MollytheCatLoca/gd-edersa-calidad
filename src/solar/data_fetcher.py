"""
Solar Data Fetcher for NASA POWER and PVGIS APIs
Fase 4 - Modelado de Recurso Solar
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, List
import json
import time
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SolarDataFetcher:
    """Fetches solar radiation data from NASA POWER and PVGIS APIs"""
    
    # Station coordinates from CLAUDE.md
    STATIONS = {
        'Pilcaniyeu': {'lat': -41.12, 'lon': -70.90, 'altitude': 890},
        'Jacobacci': {'lat': -41.329, 'lon': -69.550, 'altitude': 915},
        'Maquinchao': {'lat': -41.25, 'lon': -68.73, 'altitude': 888},
        'Los Menucos': {'lat': -40.843, 'lon': -68.086, 'altitude': 895}
    }
    
    # NASA POWER API endpoint
    NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
    
    # PVGIS API endpoint
    PVGIS_URL = "https://re.jrc.ec.europa.eu/api/v5_2/"
    
    def __init__(self, data_path: str = "data/solar"):
        """Initialize the solar data fetcher
        
        Args:
            data_path: Base path for storing solar data
        """
        self.data_path = Path(data_path)
        self.raw_path = self.data_path / "raw"
        self.processed_path = self.data_path / "processed"
        
        # Create directories if they don't exist
        self.raw_path.mkdir(parents=True, exist_ok=True)
        self.processed_path.mkdir(parents=True, exist_ok=True)
    
    def fetch_nasa_power_data(self, station: str, start_year: int = 2019, 
                            end_year: int = 2023) -> pd.DataFrame:
        """Fetch solar data from NASA POWER API
        
        Args:
            station: Station name (must be in STATIONS dict)
            start_year: Start year for data
            end_year: End year for data
            
        Returns:
            DataFrame with solar radiation data
        """
        if station not in self.STATIONS:
            raise ValueError(f"Station {station} not found. Available: {list(self.STATIONS.keys())}")
        
        coords = self.STATIONS[station]
        
        # NASA POWER parameters
        params = {
            'parameters': 'ALLSKY_SFC_SW_DWN,ALLSKY_SFC_SW_DNI,ALLSKY_SFC_SW_DIFF,T2M,WS10M',
            'community': 'RE',
            'longitude': coords['lon'],
            'latitude': coords['lat'],
            'start': f"{start_year}0101",
            'end': f"{end_year}1231",
            'format': 'JSON'
        }
        
        logger.info(f"Fetching NASA POWER data for {station} ({start_year}-{end_year})")
        
        try:
            response = requests.get(self.NASA_POWER_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Extract properties
            properties = data['properties']['parameter']
            
            # Convert to DataFrame
            df_list = []
            for param, values in properties.items():
                df_param = pd.DataFrame(list(values.items()), columns=['date', param])
                df_param['date'] = pd.to_datetime(df_param['date'], format='%Y%m%d')
                df_param.set_index('date', inplace=True)
                df_list.append(df_param)
            
            # Combine all parameters
            df = pd.concat(df_list, axis=1)
            
            # Rename columns for clarity
            df.columns = ['GHI', 'DNI', 'DHI', 'Temperature', 'WindSpeed']
            
            # Add station info
            df['station'] = station
            df['latitude'] = coords['lat']
            df['longitude'] = coords['lon']
            
            # Save raw data
            filename = self.raw_path / f"nasa_power_{station}_{start_year}_{end_year}.csv"
            df.to_csv(filename)
            logger.info(f"Saved NASA POWER data to {filename}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching NASA POWER data: {e}")
            raise
    
    def fetch_pvgis_tmy(self, station: str) -> pd.DataFrame:
        """Fetch Typical Meteorological Year (TMY) data from PVGIS
        
        Args:
            station: Station name
            
        Returns:
            DataFrame with hourly TMY data
        """
        if station not in self.STATIONS:
            raise ValueError(f"Station {station} not found")
        
        coords = self.STATIONS[station]
        
        # PVGIS TMY endpoint
        url = f"{self.PVGIS_URL}tmy"
        
        params = {
            'lat': coords['lat'],
            'lon': coords['lon'],
            'outputformat': 'json'
        }
        
        logger.info(f"Fetching PVGIS TMY data for {station}")
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Extract hourly data
            hourly_data = data['outputs']['tmy_hourly']
            
            # Convert to DataFrame
            df = pd.DataFrame(hourly_data)
            
            # Parse time column
            df['time'] = pd.to_datetime(df['time(UTC)'], format='%Y%m%d:%H%M')
            df.set_index('time', inplace=True)
            df.drop('time(UTC)', axis=1, inplace=True)
            
            # Rename columns
            column_map = {
                'G(h)': 'GHI',
                'Gb(n)': 'DNI', 
                'Gd(h)': 'DHI',
                'T2m': 'Temperature',
                'WS10m': 'WindSpeed'
            }
            df.rename(columns=column_map, inplace=True)
            
            # Add station info
            df['station'] = station
            
            # Save TMY data
            filename = self.raw_path / f"pvgis_tmy_{station}.csv"
            df.to_csv(filename)
            logger.info(f"Saved PVGIS TMY data to {filename}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching PVGIS data: {e}")
            raise
    
    def process_solar_data(self, station: str) -> pd.DataFrame:
        """Process and combine solar data from different sources
        
        Args:
            station: Station name
            
        Returns:
            Processed DataFrame with hourly solar data
        """
        # Try to load existing NASA POWER data
        nasa_files = list(self.raw_path.glob(f"nasa_power_{station}_*.csv"))
        
        if not nasa_files:
            # Fetch new data if not available
            df_nasa = self.fetch_nasa_power_data(station)
        else:
            # Load most recent file
            df_nasa = pd.read_csv(nasa_files[-1], index_col='date', parse_dates=True)
        
        # Convert daily to hourly using typical profiles
        df_hourly = self._daily_to_hourly(df_nasa)
        
        # Calculate additional metrics
        df_hourly['clearness_index'] = df_hourly['GHI'] / self._calculate_extraterrestrial(
            df_hourly.index, self.STATIONS[station]['lat']
        )
        
        # Classify day types
        df_hourly['day_type'] = self._classify_days(df_hourly['clearness_index'])
        
        # Save processed data
        filename = self.processed_path / f"solar_hourly_{station}.parquet"
        df_hourly.to_parquet(filename)
        logger.info(f"Saved processed solar data to {filename}")
        
        return df_hourly
    
    def _daily_to_hourly(self, df_daily: pd.DataFrame) -> pd.DataFrame:
        """Convert daily solar data to hourly using typical profiles
        
        Args:
            df_daily: Daily solar data
            
        Returns:
            Hourly solar data
        """
        # Create hourly index
        start_date = df_daily.index.min()
        end_date = df_daily.index.max() + timedelta(days=1)
        hourly_index = pd.date_range(start=start_date, end=end_date, freq='H')[:-1]
        
        # Initialize hourly dataframe
        df_hourly = pd.DataFrame(index=hourly_index)
        
        # Get sunrise/sunset times
        lat = df_daily['latitude'].iloc[0]
        lon = df_daily['longitude'].iloc[0]
        
        # Simple solar profile (bell curve)
        for date in df_daily.index:
            # Get solar noon (approximate)
            solar_noon = 12 - lon/15  # hours
            
            # Daylight hours (simplified)
            day_of_year = date.timetuple().tm_yday
            P = np.arcsin(0.39795 * np.cos(0.98563 * (day_of_year - 173) * np.pi/180))
            sunrise = 12 - 7.639 * np.arccos(-np.tan(lat * np.pi/180) * np.tan(P)) / np.pi
            sunset = 12 + 7.639 * np.arccos(-np.tan(lat * np.pi/180) * np.tan(P)) / np.pi
            
            # Create hourly profile
            hours = np.arange(24)
            profile = np.zeros(24)
            
            daylight_mask = (hours >= sunrise) & (hours <= sunset)
            solar_angle = np.pi * (hours[daylight_mask] - sunrise) / (sunset - sunrise)
            profile[daylight_mask] = np.sin(solar_angle)
            
            # Normalize so sum equals daily total
            if profile.sum() > 0:
                profile = profile / profile.sum()
            
            # Apply to each hour of the day
            day_data = df_daily.loc[date]
            for hour in range(24):
                timestamp = pd.Timestamp(date) + timedelta(hours=hour)
                if timestamp in df_hourly.index:
                    df_hourly.loc[timestamp, 'GHI'] = day_data['GHI'] * profile[hour]
                    df_hourly.loc[timestamp, 'DNI'] = day_data['DNI'] * profile[hour] * 1.2  # DNI peaks higher
                    df_hourly.loc[timestamp, 'DHI'] = day_data['DHI'] * profile[hour] * 0.8  # DHI more uniform
                    df_hourly.loc[timestamp, 'Temperature'] = day_data['Temperature']
                    df_hourly.loc[timestamp, 'WindSpeed'] = day_data['WindSpeed']
        
        # Copy station info
        df_hourly['station'] = df_daily['station'].iloc[0]
        df_hourly['latitude'] = lat
        df_hourly['longitude'] = lon
        
        return df_hourly
    
    def _calculate_extraterrestrial(self, timestamps: pd.DatetimeIndex, 
                                  latitude: float) -> np.ndarray:
        """Calculate extraterrestrial radiation
        
        Args:
            timestamps: Datetime index
            latitude: Station latitude in degrees
            
        Returns:
            Array of extraterrestrial radiation values
        """
        # Solar constant
        Gsc = 1367  # W/m²
        
        # Day of year
        day_of_year = timestamps.dayofyear
        
        # Solar declination
        declination = 23.45 * np.sin(np.radians(360 * (284 + day_of_year) / 365))
        
        # Hour angle
        solar_time = timestamps.hour + timestamps.minute / 60
        hour_angle = 15 * (solar_time - 12)
        
        # Extraterrestrial radiation
        lat_rad = np.radians(latitude)
        dec_rad = np.radians(declination)
        ha_rad = np.radians(hour_angle)
        
        cos_zenith = (np.sin(lat_rad) * np.sin(dec_rad) + 
                     np.cos(lat_rad) * np.cos(dec_rad) * np.cos(ha_rad))
        
        # Set negative values to 0 (sun below horizon)
        cos_zenith = np.maximum(cos_zenith, 0)
        
        # Earth-sun distance correction
        E0 = 1 + 0.033 * np.cos(np.radians(360 * day_of_year / 365))
        
        return Gsc * E0 * cos_zenith
    
    def _classify_days(self, clearness_index: pd.Series) -> pd.Series:
        """Classify days based on clearness index
        
        Args:
            clearness_index: Series of clearness index values
            
        Returns:
            Series with day classifications
        """
        # Daily mean clearness index
        daily_kt = clearness_index.resample('D').mean()
        
        # Classification thresholds
        conditions = [
            daily_kt >= 0.65,
            (daily_kt >= 0.35) & (daily_kt < 0.65),
            daily_kt < 0.35
        ]
        choices = ['clear', 'partial', 'cloudy']
        
        # Classify days
        day_types = pd.Series(
            np.select(conditions, choices, default='partial'),
            index=daily_kt.index
        )
        
        # Expand to hourly
        return day_types.reindex(clearness_index.index, method='ffill')
    
    def fetch_all_stations(self, start_year: int = 2019, 
                          end_year: int = 2023) -> Dict[str, pd.DataFrame]:
        """Fetch and process data for all stations
        
        Args:
            start_year: Start year for data
            end_year: End year for data
            
        Returns:
            Dictionary with processed data for each station
        """
        results = {}
        
        for station in self.STATIONS:
            logger.info(f"Processing station: {station}")
            try:
                # Fetch NASA POWER data
                self.fetch_nasa_power_data(station, start_year, end_year)
                
                # Process to hourly
                df_processed = self.process_solar_data(station)
                results[station] = df_processed
                
                # Small delay to avoid API rate limits
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing {station}: {e}")
                continue
        
        # Save summary statistics
        self._save_summary_stats(results)
        
        return results
    
    def _save_summary_stats(self, data_dict: Dict[str, pd.DataFrame]):
        """Save summary statistics for all stations
        
        Args:
            data_dict: Dictionary with data for each station
        """
        summary = {}
        
        for station, df in data_dict.items():
            # Annual statistics
            annual_ghi = df['GHI'].resample('Y').sum() / 1000  # MWh/m²
            
            summary[station] = {
                'annual_ghi_mean': float(annual_ghi.mean()),
                'annual_ghi_std': float(annual_ghi.std()),
                'annual_ghi_min': float(annual_ghi.min()),
                'annual_ghi_max': float(annual_ghi.max()),
                'mean_temperature': float(df['Temperature'].mean()),
                'mean_wind_speed': float(df['WindSpeed'].mean()),
                'clear_days_pct': float((df['day_type'] == 'clear').sum() / len(df) * 100),
                'partial_days_pct': float((df['day_type'] == 'partial').sum() / len(df) * 100),
                'cloudy_days_pct': float((df['day_type'] == 'cloudy').sum() / len(df) * 100)
            }
        
        # Save summary
        filename = self.processed_path / "solar_summary_stats.json"
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Saved summary statistics to {filename}")


if __name__ == "__main__":
    # Test the fetcher
    fetcher = SolarDataFetcher()
    
    # Fetch data for one station
    station = "Maquinchao"
    df = fetcher.fetch_nasa_power_data(station, 2019, 2023)
    print(f"\nFetched {len(df)} days of data for {station}")
    print(f"Mean GHI: {df['GHI'].mean():.1f} W/m²")
    
    # Process to hourly
    df_hourly = fetcher.process_solar_data(station)
    print(f"\nProcessed to {len(df_hourly)} hourly records")
    print(f"Data shape: {df_hourly.shape}")
    print(f"Columns: {df_hourly.columns.tolist()}")