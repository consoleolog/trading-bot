import os

import redis.asyncio as redis
import structlog
from redis.asyncio.client import Redis

logger = structlog.get_logger(__name__)


class RedisClient:
    """redis-py asyncio 기반 Redis 클라이언트 관리 클래스."""

    def __init__(self, config: dict) -> None:
        """설정 딕셔너리로 초기화합니다.

        Args:
            config: 연결 설정 딕셔너리. 지원하는 키:

                - ``host`` (기본값 ``redis``) - Redis 서버 호스트.
                - ``port`` (int, 기본값 6379) - Redis 서버 포트.
                - ``database`` (int, 기본값 0) - Redis DB 번호.
                - ``password`` - 인증 비밀번호 (없으면 URL에서 생략).
                - ``max_connections`` (int, 기본값 50) - 최대 연결 수.
        """
        self.config = config
        self.client: Redis | None = None
        self.is_connected: bool = False

        # Cache TTL settings (초 단위)
        self.ttl_settings = {
            # TODO: add custom ttl settings
        }

        # Pub/Sub channels
        self.channels = {
            # TODO: add channels
        }

    async def connect(self) -> None:
        """Redis 클라이언트를 생성하고 서버에 연결합니다."""
        try:
            host: str = self.config.get("host") or os.getenv("REDIS_HOST", "redis")
            port: int = int(self.config.get("port") or os.getenv("REDIS_PORT", 6379))
            database: int = int(
                self.config.get("database") if self.config.get("database") is not None else os.getenv("REDIS_DB", 0)
            )
            password: str | None = self.config.get("password") or os.getenv("REDIS_PASSWORD")

            if password:
                redis_url = f"redis://:{password}@{host}:{port}/{database}"
            else:
                redis_url = f"redis://{host}:{port}/{database}"

            logger.info("🔌 Redis 연결 중", host=host, port=port, database=database)

            self.client = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=False,  # 디코딩을 직접 처리
                socket_keepalive=True,
                max_connections=self.config.get("max_connections", 50),
                health_check_interval=30,
            )
            await self.client.ping()

            # Set up key expiration notifications
            await self._setup_keyspace_notifications()

            self.is_connected = True
            logger.info("✅ Redis 연결 성공", host=host, port=port)

        except Exception as error:
            logger.exception("❌ Redis 연결 실패", error=str(error))
            raise

    async def disconnect(self) -> None:
        """클라이언트 연결을 닫고 연결 상태를 해제합니다."""
        if self.client:
            await self.client.close()
            self.is_connected = False
            self.client = None
            logger.info("🔒 Redis 연결 해제")

    async def _setup_keyspace_notifications(self) -> None:
        """키스페이스 만료 이벤트 알림을 활성화합니다.

        설정 실패 시 경고만 남기고 예외를 전파하지 않습니다.
        """
        try:
            await self.client.config_set("notify-keyspace-events", "Ex")
        except Exception as error:
            logger.exception("⚠️ 키스페이스 알림 설정 실패", error=str(error))
