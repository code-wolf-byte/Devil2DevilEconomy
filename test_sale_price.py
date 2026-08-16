"""Self-check for the store-wide sale math. Run: python test_sale_price.py"""

from shared import sale_price


def test_sale_price():
    # Toggle off: full price, always.
    assert sale_price(100, 0) == 100
    assert sale_price(0, 0) == 0

    # Toggle on at 20%: matches the old hardcoded int(price * 0.8).
    for price in (0, 1, 5, 99, 100, 999, 12345):
        assert sale_price(price, 20) == int(price * 0.8), price

    # Truncates down, never charges more than the listed price.
    assert sale_price(9, 15) == 7  # 7.65 -> 7
    assert sale_price(100, 100) == 0


if __name__ == "__main__":
    test_sale_price()
    print("ok")
