from datetime import datetime
from decimal import Decimal

import pytest

from src.models.candle import Candle


@pytest.fixture
def base_candle():
    return Candle(
        market="KRW-BTC",
        timeframe="1m",
        open=Decimal("50000000"),
        high=Decimal("51000000"),
        low=Decimal("49000000"),
        close=Decimal("50500000"),
        volume=Decimal("1.5"),
        open_time=datetime(2024, 1, 1, 9, 0, 0),
        close_time=datetime(2024, 1, 1, 9, 1, 0),
    )


@pytest.mark.unit
class TestCandleCreation:
    def test_decimal_fields_stored_as_decimal(self, base_candle):
        for field in ("open", "high", "low", "close", "volume"):
            assert isinstance(getattr(base_candle, field), Decimal)

    def test_int_converted_to_decimal(self):
        candle = Candle(
            market="KRW-BTC",
            timeframe="1m",
            open=50000000,
            high=51000000,
            low=49000000,
            close=50500000,
            volume=1,
            open_time=datetime(2024, 1, 1, 9, 0, 0),
            close_time=datetime(2024, 1, 1, 9, 1, 0),
        )
        for field in ("open", "high", "low", "close", "volume"):
            assert isinstance(getattr(candle, field), Decimal)

    def test_float_converted_to_decimal(self):
        candle = Candle(
            market="KRW-ETH",
            timeframe="5m",
            open=3000000.5,
            high=3100000.0,
            low=2900000.0,
            close=3050000.25,
            volume=2.75,
            open_time=datetime(2024, 1, 1, 9, 0, 0),
            close_time=datetime(2024, 1, 1, 9, 5, 0),
        )
        for field in ("open", "high", "low", "close", "volume"):
            assert isinstance(getattr(candle, field), Decimal)

    def test_str_converted_to_decimal(self):
        candle = Candle(
            market="KRW-BTC",
            timeframe="1h",
            open="50000000",
            high="51000000",
            low="49000000",
            close="50500000",
            volume="1.23456789",
            open_time=datetime(2024, 1, 1, 9, 0, 0),
            close_time=datetime(2024, 1, 1, 10, 0, 0),
        )
        for field in ("open", "high", "low", "close", "volume"):
            assert isinstance(getattr(candle, field), Decimal)
        assert candle.volume == Decimal("1.23456789")

    def test_decimal_input_unchanged(self, base_candle):
        assert base_candle.open == Decimal("50000000")
        assert base_candle.volume == Decimal("1.5")

    def test_str_fields_stored_as_is(self, base_candle):
        assert base_candle.market == "KRW-BTC"
        assert base_candle.timeframe == "1m"

    def test_datetime_fields_stored_as_is(self, base_candle):
        assert base_candle.open_time == datetime(2024, 1, 1, 9, 0, 0)
        assert base_candle.close_time == datetime(2024, 1, 1, 9, 1, 0)

    def test_str_converted_to_datetime(self):
        candle = Candle(
            market="KRW-BTC",
            timeframe="1m",
            open=Decimal("50000000"),
            high=Decimal("51000000"),
            low=Decimal("49000000"),
            close=Decimal("50500000"),
            volume=Decimal("1.5"),
            open_time="2024-01-01T09:00:00",
            close_time="2024-01-01T09:01:00",
        )
        assert candle.open_time == datetime(2024, 1, 1, 9, 0, 0)
        assert candle.close_time == datetime(2024, 1, 1, 9, 1, 0)


@pytest.mark.unit
class TestCandleEquality:
    def test_equal_candles(self, base_candle):
        other = Candle(
            market="KRW-BTC",
            timeframe="1m",
            open=Decimal("50000000"),
            high=Decimal("51000000"),
            low=Decimal("49000000"),
            close=Decimal("50500000"),
            volume=Decimal("1.5"),
            open_time=datetime(2024, 1, 1, 9, 0, 0),
            close_time=datetime(2024, 1, 1, 9, 1, 0),
        )
        assert base_candle == other

    def test_different_market_not_equal(self, base_candle):
        other = Candle(
            market="KRW-ETH",
            timeframe="1m",
            open=Decimal("50000000"),
            high=Decimal("51000000"),
            low=Decimal("49000000"),
            close=Decimal("50500000"),
            volume=Decimal("1.5"),
            open_time=datetime(2024, 1, 1, 9, 0, 0),
            close_time=datetime(2024, 1, 1, 9, 1, 0),
        )
        assert base_candle != other

    def test_int_and_decimal_equal(self):
        c1 = Candle(
            market="KRW-BTC",
            timeframe="1m",
            open=50000000,
            high=51000000,
            low=49000000,
            close=50500000,
            volume=1,
            open_time=datetime(2024, 1, 1, 9, 0, 0),
            close_time=datetime(2024, 1, 1, 9, 1, 0),
        )
        c2 = Candle(
            market="KRW-BTC",
            timeframe="1m",
            open=Decimal("50000000"),
            high=Decimal("51000000"),
            low=Decimal("49000000"),
            close=Decimal("50500000"),
            volume=Decimal("1"),
            open_time=datetime(2024, 1, 1, 9, 0, 0),
            close_time=datetime(2024, 1, 1, 9, 1, 0),
        )
        assert c1 == c2
