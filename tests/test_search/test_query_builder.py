"""
Tests for query_builder date interval functions.
"""
import pytest
import pandas as pd
from bigdata_research_tools.search.query_builder import create_date_intervals, create_date_ranges


class TestCreateDateIntervals:
    """Test create_date_intervals function with various scenarios."""
    
    def test_weekly_with_partial_first_interval(self):
        """Test weekly frequency when start date is mid-week (loses initial days without fix)."""
        start_date = "2025-10-01"  # Wednesday
        end_date = "2025-10-11"    # Saturday (10 days later)
        freq = "W"  # Weekly (defaults to Sunday)
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        # Should generate 2 intervals:
        # 1. Partial: 2025-10-01 to 2025-10-04 (Wed-Sat, before first Sunday)
        # 2. Full week: 2025-10-05 to 2025-10-11 (Sun-Sat)
        assert len(intervals) == 2
        
        # Check first partial interval
        assert intervals[0][0] == pd.Timestamp("2025-10-01 00:00:00")
        assert intervals[0][1] == pd.Timestamp("2025-10-04 23:59:59")
        
        # Check second interval
        assert intervals[1][0] == pd.Timestamp("2025-10-05 00:00:00")
        assert intervals[1][1] == pd.Timestamp("2025-10-11 23:59:59")
    
    def test_monthly_aligned_start(self):
        """Test monthly frequency when start date aligns with month start."""
        start_date = "2025-01-01"
        end_date = "2025-03-31"
        freq = "M"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        # Should generate 3 intervals (Jan, Feb, Mar)
        assert len(intervals) == 3
        
        # Check January
        assert intervals[0][0] == pd.Timestamp("2025-01-01 00:00:00")
        assert intervals[0][1] == pd.Timestamp("2025-01-31 23:59:59")
        
        # Check February
        assert intervals[1][0] == pd.Timestamp("2025-02-01 00:00:00")
        assert intervals[1][1] == pd.Timestamp("2025-02-28 23:59:59")
        
        # Check March
        assert intervals[2][0] == pd.Timestamp("2025-03-01 00:00:00")
        assert intervals[2][1] == pd.Timestamp("2025-03-31 23:59:59")
    
    def test_monthly_mid_month_start(self):
        """Test monthly frequency when start date is mid-month."""
        start_date = "2025-01-15"
        end_date = "2025-03-31"
        freq = "M"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        # Should generate 3 intervals:
        # 1. Partial: 2025-01-15 to 2025-01-31
        # 2. Full: 2025-02-01 to 2025-02-28
        # 3. Full: 2025-03-01 to 2025-03-31
        assert len(intervals) == 3
        
        # Check partial first interval
        assert intervals[0][0] == pd.Timestamp("2025-01-15 00:00:00")
        assert intervals[0][1] == pd.Timestamp("2025-01-31 23:59:59")
    
    def test_quarterly_frequency(self):
        """Test quarterly frequency (3M)."""
        start_date = "2025-01-01"
        end_date = "2025-12-31"
        freq = "3M"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        # Should generate 4 quarters
        assert len(intervals) == 4
        
        # Q1
        assert intervals[0][0] == pd.Timestamp("2025-01-01 00:00:00")
        assert intervals[0][1] == pd.Timestamp("2025-03-31 23:59:59")
        
        # Q4
        assert intervals[3][0] == pd.Timestamp("2025-10-01 00:00:00")
        assert intervals[3][1] == pd.Timestamp("2025-12-31 23:59:59")
    
    def test_daily_frequency(self):
        """Test daily frequency."""
        start_date = "2025-10-01"
        end_date = "2025-10-05"
        freq = "D"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        # Should generate 5 daily intervals
        assert len(intervals) == 5
        
        # Check first day
        assert intervals[0][0] == pd.Timestamp("2025-10-01 00:00:00")
        assert intervals[0][1] == pd.Timestamp("2025-10-01 23:59:59")
        
        # Check last day
        assert intervals[4][0] == pd.Timestamp("2025-10-05 00:00:00")
        assert intervals[4][1] == pd.Timestamp("2025-10-05 23:59:59")
    
    def test_yearly_frequency(self):
        """Test yearly frequency."""
        start_date = "2023-01-01"
        end_date = "2025-12-31"
        freq = "Y"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        # Should generate 3 years
        assert len(intervals) == 3
        
        # Check 2023
        assert intervals[0][0] == pd.Timestamp("2023-01-01 00:00:00")
        assert intervals[0][1] == pd.Timestamp("2023-12-31 23:59:59")
        
        # Check 2025
        assert intervals[2][0] == pd.Timestamp("2025-01-01 00:00:00")
        assert intervals[2][1] == pd.Timestamp("2025-12-31 23:59:59")
    
    def test_single_day_range(self):
        """Test when start and end date are the same."""
        start_date = "2025-10-01"
        end_date = "2025-10-01"
        freq = "D"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        # Should generate 1 interval for single day
        assert len(intervals) == 1
        assert intervals[0][0] == pd.Timestamp("2025-10-01 00:00:00")
        assert intervals[0][1] == pd.Timestamp("2025-10-01 23:59:59")
    
    def test_short_range_weekly(self):
        """Test weekly frequency with range shorter than a week."""
        start_date = "2025-10-01"  # Wednesday
        end_date = "2025-10-03"    # Friday
        freq = "W"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        # Should generate 1 interval (no Sunday in range)
        # Interval should cover the entire range
        assert len(intervals) == 1
        assert intervals[0][0] == pd.Timestamp("2025-10-01 00:00:00")
        assert intervals[0][1] == pd.Timestamp("2025-10-03 23:59:59")
    
    def test_biweekly_frequency(self):
        """Test bi-weekly frequency (2W)."""
        start_date = "2025-10-01"
        end_date = "2025-10-31"
        freq = "2W"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        # Should generate multiple intervals
        assert len(intervals) > 1
        
        # First interval should start at start_date
        assert intervals[0][0] == pd.Timestamp("2025-10-01 00:00:00")
        
        # Last interval should end at end_date
        assert intervals[-1][1] == pd.Timestamp("2025-10-31 23:59:59")
    
    def test_no_gaps_in_intervals(self):
        """Test that there are no gaps between intervals."""
        start_date = "2025-01-15"
        end_date = "2025-04-30"
        freq = "M"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        # Check no gaps between consecutive intervals
        for i in range(len(intervals) - 1):
            end_of_current = intervals[i][1]
            start_of_next = intervals[i + 1][0]
            
            # Next interval should start 1 second after current ends
            expected_next_start = end_of_current + pd.Timedelta(seconds=1)
            assert start_of_next == expected_next_start
    
    def test_coverage_of_entire_range(self):
        """Test that intervals cover the entire date range."""
        start_date = "2025-10-01"
        end_date = "2025-10-11"
        freq = "W"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        # First interval should start at start_date
        assert intervals[0][0] == pd.Timestamp("2025-10-01 00:00:00")
        
        # Last interval should end at end_date
        assert intervals[-1][1] == pd.Timestamp("2025-10-11 23:59:59")
    
    def test_invalid_frequency_raises_error(self):
        """Test that invalid frequency raises ValueError."""
        start_date = "2025-10-01"
        end_date = "2025-10-11"
        freq = "X"  # Invalid frequency
        
        with pytest.raises(ValueError, match="Invalid frequency"):
            create_date_intervals(start_date, end_date, freq)


class TestCreateDateIntervalsExtreme:
    """Extreme edge case tests focusing on first and last intervals."""
    
    # ==================== DAILY FREQUENCY TESTS ====================
    
    def test_daily_single_day(self):
        """Daily: Single day - first and last should be same."""
        start_date = "2025-06-15"
        end_date = "2025-06-15"
        freq = "D"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        assert len(intervals) == 1
        # First interval
        assert intervals[0][0] == pd.Timestamp("2025-06-15 00:00:00")
        assert intervals[0][1] == pd.Timestamp("2025-06-15 23:59:59")
        # Last interval (same as first)
        assert intervals[-1][0] == pd.Timestamp("2025-06-15 00:00:00")
        assert intervals[-1][1] == pd.Timestamp("2025-06-15 23:59:59")
    
    def test_daily_two_days(self):
        """Daily: Two days - verify first and last."""
        start_date = "2025-12-30"
        end_date = "2025-12-31"
        freq = "D"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        assert len(intervals) == 2
        # First interval
        assert intervals[0][0] == pd.Timestamp("2025-12-30 00:00:00")
        assert intervals[0][1] == pd.Timestamp("2025-12-30 23:59:59")
        # Last interval
        assert intervals[-1][0] == pd.Timestamp("2025-12-31 00:00:00")
        assert intervals[-1][1] == pd.Timestamp("2025-12-31 23:59:59")
    
    def test_daily_across_year_boundary(self):
        """Daily: Across year boundary - verify first and last."""
        start_date = "2024-12-30"
        end_date = "2025-01-02"
        freq = "D"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        assert len(intervals) == 4
        # First interval (2024)
        assert intervals[0][0] == pd.Timestamp("2024-12-30 00:00:00")
        assert intervals[0][1] == pd.Timestamp("2024-12-30 23:59:59")
        # Last interval (2025)
        assert intervals[-1][0] == pd.Timestamp("2025-01-02 00:00:00")
        assert intervals[-1][1] == pd.Timestamp("2025-01-02 23:59:59")
    
    def test_daily_leap_year_feb_29(self):
        """Daily: Including Feb 29 in leap year."""
        start_date = "2024-02-28"
        end_date = "2024-03-01"
        freq = "D"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        assert len(intervals) == 3  # 28, 29, Mar 1
        # First interval
        assert intervals[0][0] == pd.Timestamp("2024-02-28 00:00:00")
        assert intervals[0][1] == pd.Timestamp("2024-02-28 23:59:59")
        # Last interval
        assert intervals[-1][0] == pd.Timestamp("2024-03-01 00:00:00")
        assert intervals[-1][1] == pd.Timestamp("2024-03-01 23:59:59")
    
    # ==================== WEEKLY FREQUENCY TESTS ====================
    
    def test_weekly_starts_on_sunday(self):
        """Weekly: Start on Sunday - no partial first interval."""
        start_date = "2025-10-05"  # Sunday
        end_date = "2025-10-25"    # Saturday
        freq = "W"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        assert len(intervals) == 3
        # First interval (should start on Sunday, no partial)
        assert intervals[0][0] == pd.Timestamp("2025-10-05 00:00:00")
        assert intervals[0][1] == pd.Timestamp("2025-10-11 23:59:59")
        # Last interval
        assert intervals[-1][0] == pd.Timestamp("2025-10-19 00:00:00")
        assert intervals[-1][1] == pd.Timestamp("2025-10-25 23:59:59")
    
    def test_weekly_starts_on_saturday(self):
        """Weekly: Start on Saturday - partial first interval (1 day)."""
        start_date = "2025-10-04"  # Saturday
        end_date = "2025-10-18"    # Saturday
        freq = "W"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        assert len(intervals) == 3
        # First interval (partial: just Saturday)
        assert intervals[0][0] == pd.Timestamp("2025-10-04 00:00:00")
        assert intervals[0][1] == pd.Timestamp("2025-10-04 23:59:59")
        # Last interval
        assert intervals[-1][0] == pd.Timestamp("2025-10-12 00:00:00")
        assert intervals[-1][1] == pd.Timestamp("2025-10-18 23:59:59")
    
    def test_weekly_starts_on_monday(self):
        """Weekly: Start on Monday - partial first interval."""
        start_date = "2025-09-29"  # Monday
        end_date = "2025-10-12"    # Sunday
        freq = "W"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        assert len(intervals) == 3
        # First interval (partial: Mon-Sat, 6 days)
        assert intervals[0][0] == pd.Timestamp("2025-09-29 00:00:00")
        assert intervals[0][1] == pd.Timestamp("2025-10-04 23:59:59")
        # Second interval (full week: Sun-Sat, 7 days)
        assert intervals[1][0] == pd.Timestamp("2025-10-05 00:00:00")
        assert intervals[1][1] == pd.Timestamp("2025-10-11 23:59:59")
        # Last interval (partial: just Sunday, 1 day)
        assert intervals[-1][0] == pd.Timestamp("2025-10-12 00:00:00")
        assert intervals[-1][1] == pd.Timestamp("2025-10-12 23:59:59")
    
    def test_weekly_ends_mid_week(self):
        """Weekly: End on Wednesday - last interval should end on Wednesday."""
        start_date = "2025-10-01"  # Wednesday
        end_date = "2025-10-15"    # Wednesday
        freq = "W"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        assert len(intervals) == 3
        # First interval (partial: Wed-Sat)
        assert intervals[0][0] == pd.Timestamp("2025-10-01 00:00:00")
        assert intervals[0][1] == pd.Timestamp("2025-10-04 23:59:59")
        # Last interval (partial: Sun-Wed)
        assert intervals[-1][0] == pd.Timestamp("2025-10-12 00:00:00")
        assert intervals[-1][1] == pd.Timestamp("2025-10-15 23:59:59")
    
    def test_weekly_exactly_one_week(self):
        """Weekly: Exactly one week (Sun-Sat)."""
        start_date = "2025-10-05"  # Sunday
        end_date = "2025-10-11"    # Saturday
        freq = "W"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        assert len(intervals) == 1
        # First and last (same interval)
        assert intervals[0][0] == pd.Timestamp("2025-10-05 00:00:00")
        assert intervals[-1][1] == pd.Timestamp("2025-10-11 23:59:59")
    
    # ==================== MONTHLY FREQUENCY TESTS ====================
    
    def test_monthly_starts_first_day(self):
        """Monthly: Start on 1st - no partial first interval."""
        start_date = "2025-01-01"
        end_date = "2025-03-31"
        freq = "M"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        assert len(intervals) == 3
        # First interval (full month)
        assert intervals[0][0] == pd.Timestamp("2025-01-01 00:00:00")
        assert intervals[0][1] == pd.Timestamp("2025-01-31 23:59:59")
        # Last interval
        assert intervals[-1][0] == pd.Timestamp("2025-03-01 00:00:00")
        assert intervals[-1][1] == pd.Timestamp("2025-03-31 23:59:59")
    
    def test_monthly_starts_last_day(self):
        """Monthly: Start on 31st - partial first interval (1 day)."""
        start_date = "2025-01-31"
        end_date = "2025-03-15"
        freq = "M"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        assert len(intervals) == 3
        # First interval (partial: just Jan 31)
        assert intervals[0][0] == pd.Timestamp("2025-01-31 00:00:00")
        assert intervals[0][1] == pd.Timestamp("2025-01-31 23:59:59")
        # Last interval (partial: Mar 1-15)
        assert intervals[-1][0] == pd.Timestamp("2025-03-01 00:00:00")
        assert intervals[-1][1] == pd.Timestamp("2025-03-15 23:59:59")
    
    def test_monthly_starts_mid_month(self):
        """Monthly: Start on 15th - partial first interval."""
        start_date = "2025-05-15"
        end_date = "2025-08-31"
        freq = "M"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        assert len(intervals) == 4
        # First interval (partial: May 15-31)
        assert intervals[0][0] == pd.Timestamp("2025-05-15 00:00:00")
        assert intervals[0][1] == pd.Timestamp("2025-05-31 23:59:59")
        # Last interval (full month)
        assert intervals[-1][0] == pd.Timestamp("2025-08-01 00:00:00")
        assert intervals[-1][1] == pd.Timestamp("2025-08-31 23:59:59")
    
    def test_monthly_ends_mid_month(self):
        """Monthly: End on 10th - last interval should end on 10th."""
        start_date = "2025-01-01"
        end_date = "2025-03-10"
        freq = "M"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        assert len(intervals) == 3
        # First interval (full month)
        assert intervals[0][0] == pd.Timestamp("2025-01-01 00:00:00")
        assert intervals[0][1] == pd.Timestamp("2025-01-31 23:59:59")
        # Last interval (partial: Mar 1-10)
        assert intervals[-1][0] == pd.Timestamp("2025-03-01 00:00:00")
        assert intervals[-1][1] == pd.Timestamp("2025-03-10 23:59:59")
    
    def test_monthly_february_non_leap_year(self):
        """Monthly: February in non-leap year."""
        start_date = "2025-01-15"
        end_date = "2025-03-15"
        freq = "M"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        assert len(intervals) == 3
        # Check February (28 days)
        assert intervals[1][0] == pd.Timestamp("2025-02-01 00:00:00")
        assert intervals[1][1] == pd.Timestamp("2025-02-28 23:59:59")
    
    def test_monthly_february_leap_year(self):
        """Monthly: February in leap year."""
        start_date = "2024-01-15"
        end_date = "2024-03-15"
        freq = "M"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        assert len(intervals) == 3
        # Check February (29 days)
        assert intervals[1][0] == pd.Timestamp("2024-02-01 00:00:00")
        assert intervals[1][1] == pd.Timestamp("2024-02-29 23:59:59")
    
    def test_monthly_exactly_one_month(self):
        """Monthly: Exactly one month."""
        start_date = "2025-06-01"
        end_date = "2025-06-30"
        freq = "M"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        assert len(intervals) == 1
        # First and last (same interval)
        assert intervals[0][0] == pd.Timestamp("2025-06-01 00:00:00")
        assert intervals[-1][1] == pd.Timestamp("2025-06-30 23:59:59")
    
    def test_monthly_across_year_boundary(self):
        """Monthly: Across year boundary."""
        start_date = "2024-11-15"
        end_date = "2025-02-20"
        freq = "M"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        assert len(intervals) == 4
        # First interval (partial Nov 2024)
        assert intervals[0][0] == pd.Timestamp("2024-11-15 00:00:00")
        assert intervals[0][1] == pd.Timestamp("2024-11-30 23:59:59")
        # Last interval (partial Feb 2025)
        assert intervals[-1][0] == pd.Timestamp("2025-02-01 00:00:00")
        assert intervals[-1][1] == pd.Timestamp("2025-02-20 23:59:59")
    
    # ==================== YEARLY FREQUENCY TESTS ====================
    
    def test_yearly_starts_jan_1(self):
        """Yearly: Start on Jan 1 - no partial first interval."""
        start_date = "2023-01-01"
        end_date = "2025-12-31"
        freq = "Y"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        assert len(intervals) == 3
        # First interval (full year 2023)
        assert intervals[0][0] == pd.Timestamp("2023-01-01 00:00:00")
        assert intervals[0][1] == pd.Timestamp("2023-12-31 23:59:59")
        # Last interval (full year 2025)
        assert intervals[-1][0] == pd.Timestamp("2025-01-01 00:00:00")
        assert intervals[-1][1] == pd.Timestamp("2025-12-31 23:59:59")
    
    def test_yearly_starts_mid_year(self):
        """Yearly: Start on July 1 - partial first interval."""
        start_date = "2023-07-01"
        end_date = "2025-06-30"
        freq = "Y"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        assert len(intervals) == 3
        # First interval (partial: Jul-Dec 2023)
        assert intervals[0][0] == pd.Timestamp("2023-07-01 00:00:00")
        assert intervals[0][1] == pd.Timestamp("2023-12-31 23:59:59")
        # Last interval (partial: Jan-Jun 2025)
        assert intervals[-1][0] == pd.Timestamp("2025-01-01 00:00:00")
        assert intervals[-1][1] == pd.Timestamp("2025-06-30 23:59:59")
    
    def test_yearly_starts_dec_31(self):
        """Yearly: Start on Dec 31 - partial first interval (1 day)."""
        start_date = "2023-12-31"
        end_date = "2025-01-15"
        freq = "Y"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        assert len(intervals) == 3
        # First interval (partial: just Dec 31, 2023)
        assert intervals[0][0] == pd.Timestamp("2023-12-31 00:00:00")
        assert intervals[0][1] == pd.Timestamp("2023-12-31 23:59:59")
        # Last interval (partial: Jan 1-15, 2025)
        assert intervals[-1][0] == pd.Timestamp("2025-01-01 00:00:00")
        assert intervals[-1][1] == pd.Timestamp("2025-01-15 23:59:59")
    
    def test_yearly_ends_mid_year(self):
        """Yearly: End on June 30 - last interval should end on June 30."""
        start_date = "2023-01-01"
        end_date = "2025-06-30"
        freq = "Y"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        assert len(intervals) == 3
        # First interval (full year)
        assert intervals[0][0] == pd.Timestamp("2023-01-01 00:00:00")
        assert intervals[0][1] == pd.Timestamp("2023-12-31 23:59:59")
        # Last interval (partial: Jan-Jun 2025)
        assert intervals[-1][0] == pd.Timestamp("2025-01-01 00:00:00")
        assert intervals[-1][1] == pd.Timestamp("2025-06-30 23:59:59")
    
    def test_yearly_exactly_one_year(self):
        """Yearly: Exactly one year."""
        start_date = "2025-01-01"
        end_date = "2025-12-31"
        freq = "Y"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        assert len(intervals) == 1
        # First and last (same interval)
        assert intervals[0][0] == pd.Timestamp("2025-01-01 00:00:00")
        assert intervals[-1][1] == pd.Timestamp("2025-12-31 23:59:59")
    
    def test_yearly_less_than_one_year(self):
        """Yearly: Less than one year - should return single interval."""
        start_date = "2025-03-15"
        end_date = "2025-09-20"
        freq = "Y"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        # Should return 1 interval covering entire range
        assert len(intervals) == 1
        assert intervals[0][0] == pd.Timestamp("2025-03-15 00:00:00")
        assert intervals[-1][1] == pd.Timestamp("2025-09-20 23:59:59")
    
    def test_yearly_includes_leap_year(self):
        """Yearly: Including leap year 2024."""
        start_date = "2023-06-01"
        end_date = "2025-06-01"
        freq = "Y"
        
        intervals = create_date_intervals(start_date, end_date, freq)
        
        assert len(intervals) == 3
        # First interval
        assert intervals[0][0] == pd.Timestamp("2023-06-01 00:00:00")
        assert intervals[0][1] == pd.Timestamp("2023-12-31 23:59:59")
        # Check 2024 (leap year)
        assert intervals[1][0] == pd.Timestamp("2024-01-01 00:00:00")
        assert intervals[1][1] == pd.Timestamp("2024-12-31 23:59:59")
        # Last interval
        assert intervals[-1][0] == pd.Timestamp("2025-01-01 00:00:00")
        assert intervals[-1][1] == pd.Timestamp("2025-06-01 23:59:59")


class TestCreateDateRanges:
    """Test create_date_ranges function."""
    
    def test_returns_absolute_date_ranges(self):
        """Test that function returns list of AbsoluteDateRange objects."""
        start_date = "2025-01-01"
        end_date = "2025-03-31"
        freq = "M"
        
        date_ranges = create_date_ranges(start_date, end_date, freq)
        
        # Should return list
        assert isinstance(date_ranges, list)
        assert len(date_ranges) == 3
        
        # Each element should be an AbsoluteDateRange
        from bigdata_client.daterange import AbsoluteDateRange
        for date_range in date_ranges:
            assert isinstance(date_range, AbsoluteDateRange)
    
    def test_weekly_date_ranges(self):
        """Test weekly date ranges creation."""
        start_date = "2025-10-01"
        end_date = "2025-10-11"
        freq = "W"
        
        date_ranges = create_date_ranges(start_date, end_date, freq)
        
        # Should create 2 date ranges (partial week + full week)
        assert len(date_ranges) == 2


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/test_search/test_query_builder.py -v
    pytest.main([__file__, "-v"])

