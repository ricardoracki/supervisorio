from datetime import date
from supervisorio.utils.date import range_date


def test_range_date():
    assert range_date(date(2022, 1, 15), 15) == (
        date(2021, 12, 31), date(2022, 1, 30))
