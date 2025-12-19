import statistics
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Tuple, Optional

class SnowAnalyzer:
    """
    Analyzes snowpack data to perform mapping between current snow levels
    and equivalent dates in a median snow year.
    """

    def __init__(self) -> None:
        """Initializes the SnowAnalyzer."""
        pass

    def calculate_daily_medians(self, historical_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculates medians for each calendar day (month-day) from historical data.

        Args:
            historical_data: A list of dicts containing "date" (YYYY-MM-DD) and "value".

        Returns:
            A dictionary mapping "MM-DD" strings to median float values.
        """
        day_buckets: Dict[str, List[float]] = {}
        for entry in historical_data:
            d_str = entry.get("date")
            val = entry.get("value")
            if d_str is None or val is None:
                continue
            
            try:
                dt = datetime.strptime(d_str, "%Y-%m-%d")
                mm_dd = dt.strftime("%m-%d")
                if mm_dd not in day_buckets:
                    day_buckets[mm_dd] = []
                day_buckets[mm_dd].append(float(val))
            except (ValueError, TypeError):
                continue

        medians: Dict[str, float] = {}
        for mm_dd, vals in day_buckets.items():
            if vals:
                medians[mm_dd] = statistics.median(vals)
        
        return medians

    def calculate_daily_means(self, historical_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculates means for each calendar day (month-day) from historical data.

        Args:
            historical_data: A list of dicts containing "date" (YYYY-MM-DD) and "value".

        Returns:
            A dictionary mapping "MM-DD" strings to mean float values.
        """
        day_buckets: Dict[str, List[float]] = {}
        for entry in historical_data:
            d_str = entry.get("date")
            val = entry.get("value")
            if d_str is None or val is None:
                continue
            
            try:
                dt = datetime.strptime(d_str, "%Y-%m-%d")
                mm_dd = dt.strftime("%m-%d")
                if mm_dd not in day_buckets:
                    day_buckets[mm_dd] = []
                day_buckets[mm_dd].append(float(val))
            except (ValueError, TypeError):
                continue

        means: Dict[str, float] = {}
        for mm_dd, vals in day_buckets.items():
            if vals:
                means[mm_dd] = statistics.mean(vals)
        
        return means

    def find_equivalent_days(
        self, 
        current_value: float, 
        median_year_data: List[Tuple[date, float]]
    ) -> List[date]:
        """
        Finds the dates in the median year where the snow level is closest to current_value.
        Handles erratic patterns ("camel humps") by returning the earliest and latest crossings.

        Args:
            current_value: The target snow level to map.
            median_year_data: A sorted list of (date, value) tuples representing a median year.

        Returns:
            A list containing the earliest and (if different) latest dates that match the value.
        """
        if not median_year_data:
            return []

        # Find all points where the difference changes sign or is very small
        candidates: List[date] = []
        
        # Calculate differences from target
        diffs = [val - current_value for _, val in median_year_data]
        
        for i in range(len(diffs) - 1):
            # Exact match
            if diffs[i] == 0:
                candidates.append(median_year_data[i][0])
                continue
                
            # Sign change indicates crossing
            if (diffs[i] > 0 and diffs[i+1] < 0) or (diffs[i] < 0 and diffs[i+1] > 0):
                # Pick the closer of the two surrounding dates
                if abs(diffs[i]) < abs(diffs[i+1]):
                    candidates.append(median_year_data[i][0])
                else:
                    candidates.append(median_year_data[i+1][0])

        # Final check for the last point
        if diffs and diffs[-1] == 0:
            candidates.append(median_year_data[-1][0])

        if not candidates:
            # Fallback: single closest point throughout the year
            if not diffs:
                return []
            closest_idx = 0
            min_abs_diff = abs(diffs[0])
            for i, d_val in enumerate(diffs):
                if abs(d_val) < min_abs_diff:
                    min_abs_diff = abs(d_val)
                    closest_idx = i
            return [median_year_data[closest_idx][0]]

        # Order unique candidates
        unique_candidates = sorted(list(set(candidates)))
        
        results: List[date] = []
        if unique_candidates:
            results.append(unique_candidates[0])
            if len(unique_candidates) > 1:
                results.append(unique_candidates[-1])
        
        return results

    def get_snow_year_dates(self, snow_year_start: int) -> List[date]:
        """
        Generates a continuous list of dates for a given snow year.
        Snow years start October 1st of (snow_year_start - 1) and end September 30th of snow_year_start.

        Args:
            snow_year_start: The year the snow season ends (e.g., 2025).

        Returns:
            A list of date objects.
        """
        start_date = date(snow_year_start - 1, 10, 1)
        dates: List[date] = []
        # Support leap years by iterating up to 366 days
        for i in range(366):
            d = start_date + timedelta(days=i)
            # Stop if we looped back to next Oct 1
            if d.month == 10 and d.day == 1 and i > 0:
                break
            dates.append(d)
        return dates

if __name__ == "__main__":
    # Internal test
    analyzer = SnowAnalyzer()
    
    # Mock some data
    historical = [
        {"date": "2020-01-01", "value": 10},
        {"date": "2021-01-01", "value": 12},
        {"date": "2022-01-01", "value": 11},
        {"date": "2020-01-02", "value": 15},
        {"date": "2021-01-02", "value": 17},
    ]
    
    medians = analyzer.calculate_daily_medians(historical)
    print(f"Medians: {medians}")
    
    # Test mapping
    # Simple triangle profile: 0 to 10 to 0 over 10 days
    median_profile = []
    for i in range(6): # Accumulation
        median_profile.append((date(2025, 1, i+1), float(i*2)))
    for i in range(1, 6): # Melt
        median_profile.append((date(2025, 1, 6+i), float(10 - i*2)))
    
    print(f"Profile: {median_profile}")
    equiv = analyzer.find_equivalent_days(5.0, median_profile)
    print(f"Equivalent days for 5.0: {equiv}")
