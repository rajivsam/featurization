import re
import pandas as pd
import numpy as np
import pgeocode
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

def build_address_strings(df: pd.DataFrame, prefix: str, columns: list) -> pd.Series:
    """Combines available geographic columns into clean address strings safely."""
    group_cols = [c for c in columns if c.startswith(prefix) and c in df.columns]
    if not group_cols:
        return pd.Series("", index=df.index)
        
    group_cols.sort(key=lambda x: ('Street' in x, 'City' in x, 'State' in x, 'Zip' in x), reverse=True)
    return df[group_cols].astype(str).agg(', '.join, axis=1).str.replace(r',\s*,', ',', regex=True).str.strip(', ')

def compute_geo_coordinates(df: pd.DataFrame, entity_mappings: dict, country_code: str = "us") -> pd.DataFrame:
    """Generates Lat/Lon proxies safely protecting against missing or dropped attributes."""
    df = df.copy()
    geolocator = Nominatim(user_agent="kmds_featurization_agent")
    
    try:
        nomi = pgeocode.Nominatim(country_code)
    except Exception:
        nomi = None
    
    for entity, cols in entity_mappings.items():
        if entity in ['SBA', 'Unassigned_Entity']:
            continue
            
        lat_col = f"{entity.lower()}_proxy_lat"
        lon_col = f"{entity.lower()}_proxy_lon"
        
        df[lat_col] = np.nan
        df[lon_col] = np.nan
        
        zip_col = next((c for c in cols if 'Zip' in c and c in df.columns), None)
        if zip_col and nomi is not None:
            zip_clean = df[zip_col].astype(str).str.split('.').str.tolist()
            try:
                zip_data = nomi.query_postal_code(zip_clean)
                if zip_data is not None and 'latitude' in zip_data:
                    df[lat_col] = zip_data['latitude'].values
                    df[lon_col] = zip_data['longitude'].values
            except Exception:
                pass

        address_series = build_address_strings(df, entity[:4], cols)
        unique_addresses = address_series[address_series != ""].unique()
        
        address_cache = {}
        for addr in unique_addresses[:20]:
            if pd.isna(addr) or addr.strip() == "":
                continue
            try:
                location = geolocator.geocode(addr, timeout=2)
                if location:
                    address_cache[addr] = (location.latitude, location.longitude)
            except GeocoderTimedOut:
                continue
                
        for idx, addr in address_series.items():
            if addr in address_cache:
                df.at[idx, lat_col] = address_cache[addr]
                df.at[idx, lon_col] = address_cache[addr]
                
    return df
