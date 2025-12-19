import requests
from typing import List, Dict, Any, Optional
from datetime import datetime

class NWCCDataClient:
    """
    Client for interacting with the NWCC AWDB REST API to retrieve
    snowpack water equivalent (SWE) and snow depth data.
    """
    BASE_URL = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data"
    STATIONS_URL = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/stations"

    def __init__(self) -> None:
        """Initializes the data client with a persistent session."""
        self.session = requests.Session()

    def search_stations(self, name_pattern: str) -> List[Dict[str, Any]]:
        """
        Searches for stations by name pattern.
        
        Args:
            name_pattern: Name or pattern to search for (e.g., 'Easy Pass' or '*Creek*').
            
        Returns:
            A list of station metadata dictionaries.
        """
        # Wrap in wildcards if not already present
        if "*" not in name_pattern:
            name_pattern = f"*{name_pattern}*"
            
        params = {
            "stationNames": name_pattern,
            "activeOnly": "true"
        }
        
        response = self.session.get(self.STATIONS_URL, params=params)
        response.raise_for_status()
        
        return response.json()

    def fetch_station_data(
        self, 
        station_triplet: str, 
        element_code: str, 
        begin_date: str, 
        end_date: str,
        central_tendency_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetches daily data for a specific station and element.

        Args:
            station_triplet: Station identifier (e.g., '998:WA:SNTL').
            element_code: The data element (e.g., 'WTEQ', 'SNWD').
            begin_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).
            central_tendency_type: Optional Normal type ('MEDIAN' or 'AVERAGE').

        Returns:
            A list of data point dictionaries containing 'date' and 'value'.
            If central_tendency_type is used, points also include a 'median' or 'average' field.
        """
        params: Dict[str, Any] = {
            "stationTriplets": station_triplet,
            "elements": element_code,
            "beginDate": begin_date,
            "endDate": end_date,
            "period": "DAILY",
            "duration": "DAILY"
        }
        if central_tendency_type:
            params["centralTendencyType"] = central_tendency_type

        response = self.session.get(self.BASE_URL, params=params)
        response.raise_for_status()
        
        data = response.json()
        if not data:
            return []
            
        try:
            # API returns a nested structure: List[StationResult] -> data: List[ElementResult] -> values: List[DataPoint]
            values: List[Dict[str, Any]] = data[0]["data"][0]["values"]
            return values
        except (IndexError, KeyError):
            return []

    def fetch_historical_data(
        self, 
        station_triplet: str, 
        element_code: str, 
        begin_date: str, 
        end_date: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieves raw historical data for custom aggregation.
        """
        return self.fetch_station_data(station_triplet, element_code, begin_date, end_date)

if __name__ == "__main__":
    # Quick test
    client = NWCCDataClient()
    # Easy Pass SWE with Median
    results = client.fetch_station_data("998:WA:SNTL", "WTEQ", "2024-11-01", "2024-11-02", central_tendency_type="MEDIAN")
    print(results)
