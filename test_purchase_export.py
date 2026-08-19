"""Self-check for the purchases export date filter. Run: python test_purchase_export.py"""

from datetime import datetime

from routes.api import _day_window


def test_day_window():
    # No filter at all.
    assert _day_window(None, None) == (None, None)
    assert _day_window('', '') == (None, None)

    # Open-ended on either side.
    assert _day_window('2026-01-05', None) == (datetime(2026, 1, 5), None)
    assert _day_window(None, '2026-01-05') == (None, datetime(2026, 1, 6))

    # The end day is included: a purchase at 23:59 on the end date still exports.
    lower, upper = _day_window('2026-01-01', '2026-01-31')
    assert lower == datetime(2026, 1, 1)
    assert datetime(2026, 1, 31, 23, 59) < upper
    assert datetime(2026, 2, 1) >= upper

    # Junk dates are rejected, not silently ignored.
    for bad in ('yesterday', '01/02/2026', '2026-13-01'):
        try:
            _day_window(bad, None)
        except ValueError:
            continue
        raise AssertionError(bad)


if __name__ == "__main__":
    test_day_window()
    print("ok")
