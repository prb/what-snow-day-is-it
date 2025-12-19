from src.data_client import NWCCDataClient
from src.analyzer import SnowAnalyzer
from datetime import date, datetime, timedelta
import argparse
from typing import Optional

import sys

def run_snow_day_lookup(station_input: str, element: str, target_date: str, mode: str = "median", ref_year: Optional[int] = None, snow_year: Optional[int] = None):
    client = NWCCDataClient()
    analyzer = SnowAnalyzer()

    # Determine snow year if not provided
    dt = datetime.strptime(target_date, "%Y-%m-%d")
    if snow_year is None:
        # Snow year starts Oct 1. So Dec 2025 is snow year 2026.
        snow_year = dt.year + 1 if dt.month >= 10 else dt.year

    # Resolve station
    station_triplet = station_input
    station_name = station_input

    # Simple heuristic for triplet: contains colons
    if ":" not in station_input:
        print(f"Searching for station: '{station_input}'...")
        matches = client.search_stations(station_input)
        
        if not matches:
            print(f"Error: No stations found matching '{station_input}'.")
            return
        
        if len(matches) > 1:
            print(f"\nThere are {len(matches)} stations that have a name that matches '{station_input}':")
            for m in matches:
                triplet = m.get("stationTriplet")
                name = m.get("name")
                state = m.get("stateCode")
                print(f"- {triplet} : {name} ({state})")
            print("\nPlease use a more specific name or the station triplet.")
            return

        # Single match found
        m = matches[0]
        station_triplet = m["stationTriplet"]
        station_name = m["name"]
        print(f"Found: {station_name} ({station_triplet})")

    print(f"\n--- Snow Day Lookup for {station_name} ({element}) on {target_date} ---")
    print(f"Comparison Mode: {mode.capitalize()}" + (f" ({ref_year})" if mode == "year" else ""))

    # 1. Fetch current value (with fallback for recent missing data)
    current_val = None
    check_date = dt
    for _ in range(4): # Check today + 3 days back
        d_str = check_date.strftime("%Y-%m-%d")
        current_data = client.fetch_station_data(station_triplet, element, d_str, d_str)
        if current_data and current_data[0].get("value") is not None:
            current_val = current_data[0]["value"]
            if check_date.date() != dt.date():
                print(f"Note: Using most recent data from {d_str} (today's data not yet available).")
            break
        check_date -= timedelta(days=1)

    if current_val is None:
        print(f"Error: Could not fetch data for {target_date} or recent days.")
        return
    
    print(f"Current Value: {current_val}")

    # 2. Fetch or Calculate Comparison Profile
    profile = []
    # Use a completed snow year for reference when fetching median/mean
    # to ensure the API returns a full 365-day profile (it often only returns
    # data for dates that have already passed in the requested calendar range).
    ref_sy = snow_year - 1
    sy_start = date(ref_sy - 1, 10, 1).strftime("%Y-%m-%d")
    sy_end = date(ref_sy, 9, 30).strftime("%Y-%m-%d")

    if mode == "year":
        if not ref_year:
            print("Error: --ref-year must be specified for 'year' mode.")
            return
        print(f"Fetching data for reference year {ref_year}...")
        ref_start = date(ref_year - 1, 10, 1).strftime("%Y-%m-%d")
        ref_end = date(ref_year, 9, 30).strftime("%Y-%m-%d")
        ref_data = client.fetch_station_data(station_triplet, element, ref_start, ref_end)
        
        # Map ref data to current snow year dates for comparison
        sy_dates = analyzer.get_snow_year_dates(snow_year)
        ref_map = {datetime.strptime(entry["date"], "%Y-%m-%d").strftime("%m-%d"): entry["value"] for entry in ref_data}
        
        for d in sy_dates:
            mm_dd = d.strftime("%m-%d")
            val = ref_map.get(mm_dd)
            if val is not None:
                profile.append((d, float(val)))

    elif mode in ["median", "mean"]:
        tendency = "MEDIAN" if mode == "median" else "AVERAGE"
        val_key = mode # "median" or "average" (API returns "average" for "AVERAGE")
        if mode == "mean":
             val_key = "average"

        print(f"Fetching {mode} profile...")
        tendency_data = client.fetch_station_data(station_triplet, element, sy_start, sy_end, central_tendency_type=tendency)
        
        if tendency_data and any(val_key in entry for entry in tendency_data):
            print(f"Using API-provided {mode}s.")
            for entry in tendency_data:
                val = entry.get(val_key)
                if val is not None:
                    d = datetime.strptime(entry["date"], "%Y-%m-%d").date()
                    profile.append((d, val))
        else:
            print(f"API {mode}s unavailable. Calculating from historical data (Last 10 years)...")
            start_year = datetime.strptime(target_date, "%Y-%m-%d").year - 10
            hist_start = f"{start_year}-10-01"
            hist_end = f"{datetime.strptime(target_date, "%Y-%m-%d").year}-09-30"
            historical_data = client.fetch_historical_data(station_triplet, element, hist_start, hist_end)
            
            if mode == "median":
                stats_map = analyzer.calculate_daily_medians(historical_data)
            else:
                stats_map = analyzer.calculate_daily_means(historical_data)

            sy_dates = analyzer.get_snow_year_dates(snow_year)
            for d in sy_dates:
                mm_dd = d.strftime("%m-%d")
                val = stats_map.get(mm_dd)
                if val is not None:
                    profile.append((d, val))

    # 3. Find equivalent days
    if not profile:
        print("Error: Could not build comparison profile.")
        return

    equiv_days = analyzer.find_equivalent_days(float(current_val), profile)
    
    print(f"\nEquivalent days in a {mode if mode != 'year' else ref_year} year:")
    for d in equiv_days:
        print(f"- {d.strftime('%B %d')}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="What Snow Day Is It? Demo")
    parser.add_argument("--station", default="Easy Pass", help="Station Triplet or Name (e.g. 998:WA:SNTL or 'Easy Pass')")
    parser.add_argument("--element", default="WTEQ", help="Element Code (WTEQ or SNWD)")
    parser.add_argument("--date", default=date.today().strftime("%Y-%m-%d"), help="Target Date (YYYY-MM-DD)")
    parser.add_argument("--mode", choices=["median", "mean", "year"], default="median", help="Comparison mode")
    parser.add_argument("--ref-year", type=int, help="Reference year for 'year' mode")
    
    args = parser.parse_args()
    run_snow_day_lookup(args.station, args.element, args.date, mode=args.mode, ref_year=args.ref_year)
