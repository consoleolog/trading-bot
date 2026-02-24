from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class Candle:
    """
    캔들 데이터

    Attributes:
        market: 페어의 코드
        timeframe: 캔들 조회 기간
        open: 시가
        high: 고가
        low: 저가
        close: 종가
        volume: 거래량
        open_time: 캔들 시작 시간
        close_time: 캔들 마감 시간
    """

    market: str
    timeframe: str

    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    open_time: datetime
    close_time: datetime

    def __post_init__(self):
        # int, float, str 로 값이 들어온다면 Decimal 로 변환해서 저장
        for field_name in ["open", "high", "low", "close", "volume"]:
            value = getattr(self, field_name)
            if isinstance(value, (int, float, str)):
                setattr(self, field_name, Decimal(str(value)))
        # str 로 값이 들어온다면 datetime 으로 변환해서 저장
        for field_name in ["open_time", "close_time"]:
            value = getattr(self, field_name)
            if isinstance(value, str):
                setattr(self, field_name, datetime.fromisoformat(value))
