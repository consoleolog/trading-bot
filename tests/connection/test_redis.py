"""RedisClient 테스트 — Fake Redis + Faker 연결 설정값."""

import pytest
import pytest_asyncio
from faker import Faker

from src.connection import RedisClient

# ---------------------------------------------------------------------------
# Fake Redis
# ---------------------------------------------------------------------------


class FakeRedis:
    def __init__(self) -> None:
        self.url: str | None = None
        self.kwargs: dict = {}
        self.pinged: bool = False
        self.closed: bool = False
        self.config_set_calls: list[tuple] = []

    async def ping(self) -> None:
        self.pinged = True

    async def close(self) -> None:
        self.closed = True

    async def config_set(self, key: str, value: str) -> None:
        self.config_set_calls.append((key, value))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

BASE_CONFIG: dict = {"max_connections": 10}


@pytest.fixture(scope="module")
def fkr() -> Faker:
    """모듈 내 공유 Faker 인스턴스."""
    return Faker()


@pytest.fixture
def redis_creds(fkr: Faker) -> dict:
    """테스트마다 임의의 Redis 연결 정보를 생성합니다.

    패스워드에 URL 특수문자가 포함되지 않도록 alphanumeric만 사용합니다.
    """
    return {
        "host": fkr.ipv4(),
        "port": fkr.random_int(min=1024, max=65535),
        "database": fkr.random_int(min=0, max=15),
        "password": fkr.lexify("??????????", letters="abcdefghijklmnopqrstuvwxyz0123456789"),
    }


@pytest.fixture
def fake_redis() -> FakeRedis:
    return FakeRedis()


@pytest_asyncio.fixture
async def connected_rc(fake_redis: FakeRedis, redis_creds: dict, monkeypatch: pytest.MonkeyPatch) -> RedisClient:
    """FakeRedis가 주입된 연결 완료 상태의 RedisClient."""

    def _fake_from_url(url, **kwargs):
        fake_redis.url = url
        fake_redis.kwargs = kwargs
        return fake_redis

    monkeypatch.setattr("redis.asyncio.from_url", _fake_from_url)

    rc = RedisClient({**BASE_CONFIG, **redis_creds})
    await rc.connect()
    return rc


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_init_default_state():
    """생성 직후 client는 None이고 is_connected는 False다."""
    rc = RedisClient(BASE_CONFIG)

    assert rc.client is None
    assert rc.is_connected is False
    assert rc.config is BASE_CONFIG


# ---------------------------------------------------------------------------
# connect()
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_sets_connected_state(connected_rc: RedisClient, fake_redis: FakeRedis):
    """connect() 후 is_connected가 True이고 client가 설정된다."""
    assert connected_rc.is_connected is True
    assert connected_rc.client is fake_redis


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_pings_server(connected_rc: RedisClient, fake_redis: FakeRedis):
    """connect() 시 ping()을 호출해 연결을 검증한다."""
    assert fake_redis.pinged is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_builds_url_with_password(
    redis_creds: dict, fake_redis: FakeRedis, monkeypatch: pytest.MonkeyPatch
):
    """패스워드가 있으면 redis://:{password}@{host}:{port}/{database} 형식으로 URL을 생성한다."""

    def _fake_from_url(url, **kwargs):
        fake_redis.url = url
        return fake_redis

    monkeypatch.setattr("redis.asyncio.from_url", _fake_from_url)

    rc = RedisClient({**BASE_CONFIG, **redis_creds})
    await rc.connect()

    c = redis_creds
    assert fake_redis.url == f"redis://:{c['password']}@{c['host']}:{c['port']}/{c['database']}"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_builds_url_without_password(
    redis_creds: dict, fake_redis: FakeRedis, monkeypatch: pytest.MonkeyPatch
):
    """패스워드가 없으면 redis://{host}:{port}/{database} 형식으로 URL을 생성한다."""

    def _fake_from_url(url, **kwargs):
        fake_redis.url = url
        return fake_redis

    monkeypatch.setattr("redis.asyncio.from_url", _fake_from_url)

    creds_no_pwd = {k: v for k, v in redis_creds.items() if k != "password"}
    rc = RedisClient({**BASE_CONFIG, **creds_no_pwd})
    await rc.connect()

    c = creds_no_pwd
    assert fake_redis.url == f"redis://{c['host']}:{c['port']}/{c['database']}"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_with_env_vars(redis_creds: dict, fake_redis: FakeRedis, monkeypatch: pytest.MonkeyPatch):
    """REDIS_HOST/REDIS_PORT/REDIS_DB/REDIS_PASSWORD 환경 변수로 연결한다."""
    monkeypatch.setenv("REDIS_HOST", redis_creds["host"])
    monkeypatch.setenv("REDIS_PORT", str(redis_creds["port"]))
    monkeypatch.setenv("REDIS_DB", str(redis_creds["database"]))
    monkeypatch.setenv("REDIS_PASSWORD", redis_creds["password"])

    def _fake_from_url(url, **kwargs):
        fake_redis.url = url
        return fake_redis

    monkeypatch.setattr("redis.asyncio.from_url", _fake_from_url)

    rc = RedisClient(BASE_CONFIG)
    await rc.connect()

    assert rc.is_connected is True
    c = redis_creds
    assert fake_redis.url == f"redis://:{c['password']}@{c['host']}:{c['port']}/{c['database']}"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_database_zero_is_not_ignored(fake_redis: FakeRedis, monkeypatch: pytest.MonkeyPatch):
    """database=0을 명시적으로 전달하면 환경 변수(REDIS_DB)로 silently fallback되지 않는다."""
    monkeypatch.setenv("REDIS_DB", "5")

    def _fake_from_url(url, **kwargs):
        fake_redis.url = url
        return fake_redis

    monkeypatch.setattr("redis.asyncio.from_url", _fake_from_url)

    rc = RedisClient({**BASE_CONFIG, "host": "localhost", "database": 0})
    await rc.connect()

    assert fake_redis.url.endswith("/0")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_failure_keeps_disconnected(redis_creds: dict, monkeypatch: pytest.MonkeyPatch):
    """연결 실패 시 예외가 전파되고 is_connected는 False를 유지한다."""

    def _failing_from_url(url, **kwargs):
        raise OSError("connection refused")

    monkeypatch.setattr("redis.asyncio.from_url", _failing_from_url)

    rc = RedisClient({**BASE_CONFIG, **redis_creds})

    with pytest.raises(OSError, match="connection refused"):
        await rc.connect()

    assert rc.is_connected is False
    assert rc.client is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_failure_on_ping_keeps_disconnected(redis_creds: dict, monkeypatch: pytest.MonkeyPatch):
    """ping() 실패 시 예외가 전파되고 is_connected는 False를 유지한다."""

    class FakeRedisWithFailingPing(FakeRedis):
        async def ping(self) -> None:
            raise OSError("connection refused")

    fake = FakeRedisWithFailingPing()
    monkeypatch.setattr("redis.asyncio.from_url", lambda url, **kw: fake)

    rc = RedisClient({**BASE_CONFIG, **redis_creds})

    with pytest.raises(OSError, match="connection refused"):
        await rc.connect()

    assert rc.is_connected is False


# ---------------------------------------------------------------------------
# disconnect()
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_disconnect_closes_client(connected_rc: RedisClient, fake_redis: FakeRedis):
    """disconnect() 호출 시 client가 닫히고 is_connected가 False가 된다."""
    await connected_rc.disconnect()

    assert fake_redis.closed is True
    assert connected_rc.client is None
    assert connected_rc.is_connected is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_disconnect_without_connect_is_safe():
    """connect() 없이 disconnect()를 호출해도 예외가 발생하지 않는다."""
    rc = RedisClient(BASE_CONFIG)
    await rc.disconnect()


# ---------------------------------------------------------------------------
# _setup_keyspace_notifications()
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_setup_keyspace_notifications_configures_events(connected_rc: RedisClient, fake_redis: FakeRedis):
    """connect() 시 키스페이스 만료 이벤트(Ex) 알림이 설정된다."""
    assert ("notify-keyspace-events", "Ex") in fake_redis.config_set_calls


@pytest.mark.unit
@pytest.mark.asyncio
async def test_setup_keyspace_notifications_failure_is_silent(redis_creds: dict, monkeypatch: pytest.MonkeyPatch):
    """config_set() 실패 시 예외가 전파되지 않고 연결은 성공한다."""

    class FakeRedisWithFailingConfigSet(FakeRedis):
        async def config_set(self, key: str, value: str) -> None:
            raise OSError("permission denied")

    fake = FakeRedisWithFailingConfigSet()

    def _fake_from_url(url, **kwargs):
        return fake

    monkeypatch.setattr("redis.asyncio.from_url", _fake_from_url)

    rc = RedisClient({**BASE_CONFIG, **redis_creds})
    await rc.connect()

    assert rc.is_connected is True
