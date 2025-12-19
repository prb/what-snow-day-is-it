import pytest
from datetime import date
from src.analyzer import SnowAnalyzer

class TestSnowAnalyzer:
    @pytest.fixture
    def analyzer(self) -> SnowAnalyzer:
        return SnowAnalyzer()

    def test_calculate_daily_medians(self, analyzer: SnowAnalyzer):
        historical_data = [
            {"date": "2020-01-01", "value": 10},
            {"date": "2021-01-01", "value": 12},
            {"date": "2022-01-01", "value": 11},
            {"date": "2020-01-02", "value": 15},
            {"date": "2021-01-02", "value": 17},
        ]
        medians = analyzer.calculate_daily_medians(historical_data)
        assert medians["01-01"] == 11
        assert medians["01-02"] == 16.0

    def test_calculate_daily_means(self, analyzer: SnowAnalyzer):
        historical_data = [
            {"date": "2020-01-01", "value": 10},
            {"date": "2021-01-01", "value": 12},
            {"date": "2022-01-01", "value": 11},
            {"date": "2020-01-02", "value": 15},
            {"date": "2021-01-02", "value": 17},
        ]
        means = analyzer.calculate_daily_means(historical_data)
        assert means["01-01"] == 11.0
        assert means["01-02"] == 16.0

    def test_calculate_daily_medians_empty(self, analyzer: SnowAnalyzer):
        assert analyzer.calculate_daily_medians([]) == {}

    def test_calculate_daily_medians_malformed(self, analyzer: SnowAnalyzer):
        malformed = [{"date": "invalid", "value": 10}, {"date": "2020-01-01", "value": "not_a_number"}]
        assert analyzer.calculate_daily_medians(malformed) == {}

    def test_find_equivalent_days_simple(self, analyzer: SnowAnalyzer):
        # Triangle profile: 0 to 10 to 0
        profile = [
            (date(2025, 1, 1), 0.0),
            (date(2025, 1, 2), 5.0),
            (date(2025, 1, 3), 10.0),
            (date(2025, 1, 4), 5.0),
            (date(2025, 1, 5), 0.0),
        ]
        equiv = analyzer.find_equivalent_days(5.0, profile)
        assert equiv == [date(2025, 1, 2), date(2025, 1, 4)]

    def test_find_equivalent_days_camel_humps(self, analyzer: SnowAnalyzer):
        # M-shape profile: 0 -> 10 -> 2 -> 10 -> 0
        profile = [
            (date(2025, 1, 1), 0.0),
            (date(2025, 1, 2), 10.0), # Crossing 1
            (date(2025, 1, 3), 2.0),  # Crossing 2
            (date(2025, 1, 4), 10.0), # Crossing 3
            (date(2025, 1, 5), 0.0),  # Crossing 4
        ]
        # Target = 5
        # The logic picks the closer index for crossings.
        # Crossing 1: between 0 and 10 -> 10 is at 2, 0 is at 1. Closer is Jan 2 (diff 5) or Jan 1 (diff 5)?
        # Our logic picks Jan 2 in ties because abs(diffs[i]) < abs(diffs[i+1]) is False.
        equiv = analyzer.find_equivalent_days(5.0, profile)
        assert len(equiv) == 2
        assert equiv[0] == date(2025, 1, 2)
        assert equiv[-1] == date(2025, 1, 5)

    def test_find_equivalent_days_no_crossing_fallback(self, analyzer: SnowAnalyzer):
        profile = [(date(2025, 1, 1), 10.0), (date(2025, 1, 2), 20.0)]
        # Target = 5. No crossing. Closest is Jan 1.
        assert analyzer.find_equivalent_days(5.0, profile) == [date(2025, 1, 1)]

    def test_get_snow_year_dates(self, analyzer: SnowAnalyzer):
        dates = analyzer.get_snow_year_dates(2025)
        assert dates[0] == date(2024, 10, 1)
        assert dates[-1] == date(2025, 9, 30)
        assert len(dates) in (365, 366)
