# What Snow Day Is It?

A simple tool to determine which day or days of a median snow year current snow conditions represent.

By mapping current Snow Water Equivalent (SWE) or Snow Depth back to a median (or mean) historical profile, this application answers the question: "Given the current snowpack, what time of year is it usually?"

## Features

- **Search by Name**: Lookup stations by friendly name (e.g., "Easy Pass", "Paradise") with wildcard support.
- **Station Triplets**: Direct support for NWCC station triplets (e.g., `998:WA:SNTL`).
- **Multiple Modes**:
  - **Median**: Compare against the 50th percentile historical profile (default).
  - **Mean**: Compare against the arithmetic average profile.
  - **Year**: Compare against a specific historical snow year (e.g., 2017).
- **Major Data Types**: Support for both Snow Water Equivalent (`WTEQ`) and Snow Depth (`SNWD`).
- **Smart Fallback**: Automatically falls back to the most recent available data (up to 3 days) if the current day's reading hasn't been posted yet.
- **Full Cycle Analysis**: Correctly identifies both the **accumulation phase** and **melt phase** equivalent dates.

## Setup

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

1. Ensure you have Python 3.13 or later.
2. Clone the repository.
3. Sync dependencies:
   ```bash
   uv sync
   ```

## Usage

Run the demo script to find the equivalent days for a station:

```bash
uv run python demo.py --station "Easy Pass"
```

### Options

| Flag | Description | Default |
| :--- | :--- | :--- |
| `--station` | Station name or triplet | `"Easy Pass"` |
| `--element` | Data element (`WTEQ` or `SNWD`) | `"WTEQ"` |
| `--date` | Target date for comparison (`YYYY-MM-DD`) | Today |
| `--mode` | Comparison mode (`median`, `mean`, `year`) | `median` |
| `--ref-year` | Reference year (required for `year` mode) | None |

### Examples

**Compare to the historical mean:**
```bash
uv run python demo.py --station "Paradise" --mode mean
```

**Compare today to the 2023 snow year:**
```bash
uv run python demo.py --station "Morse Creek" --mode year --ref-year 2023
```

**Search for a station and disambiguate:**
```bash
uv run python demo.py --station "Creek"
```

## How It Works

1. **Profile Acquisition**: The tool fetches a full 365-day profile (starting October 1st) for the requested station and mode (Median, Mean, or Specific Year).
2. **Equivalent Mapping**: It solves for `inverse(Profile) o Current_Value`, identifying the dates in the reference year where the snow levels match current conditions.
3. **Dual Identification**: Because snow years typically have both an accumulation phase and a melt phase, the tool identifies both crossings (e.g., "Early Winter" vs "Late Spring").

## License

This project is licensed under the [CC0 1.0 Universal](LICENSE) (Public Domain Dedication).
