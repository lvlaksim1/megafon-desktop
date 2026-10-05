from decimal import Decimal

from megafon_desktop.megafon.http_transport import DirectHttpTransport


def test_decimal_parser():
    assert DirectHttpTransport._decimal("12,34") == Decimal("12.34")
    assert DirectHttpTransport._decimal(5) == Decimal("5")
    assert DirectHttpTransport._decimal(None) is None
