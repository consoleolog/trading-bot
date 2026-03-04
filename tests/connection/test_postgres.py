"""PostgresPool 테스트 — Fake DB + Faker 연결 설정값."""

import pytest
import pytest_asyncio
from faker import Faker

from src.connection import PostgresPool

# ---------------------------------------------------------------------------
# Fake DB (asyncpg Pool / Connection / Transaction 인터페이스 모사)
# ---------------------------------------------------------------------------


class FakeTransaction:
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self) -> "FakeTransaction":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is None:
            self.committed = True
        else:
            self.rolled_back = True
        return False


class FakeConnection:
    def __init__(self) -> None:
        self.last_tx: FakeTransaction | None = None
        self.fetch_result: list = []
        self.fetchrow_result: dict | None = None
        self.execute_result: str = "OK"
        self.last_fetch_query: str | None = None
        self.last_fetch_args: tuple = ()
        self.last_execute_query: str | None = None
        self.last_execute_args: tuple = ()

    def transaction(self) -> FakeTransaction:
        self.last_tx = FakeTransaction()
        return self.last_tx

    async def fetch(self, query: str, *args) -> list:
        self.last_fetch_query = query
        self.last_fetch_args = args
        return self.fetch_result

    async def fetchrow(self, query: str, *args) -> dict | None:
        self.last_fetch_query = query
        self.last_fetch_args = args
        return self.fetchrow_result

    async def execute(self, query: str, *args) -> str:
        self.last_execute_query = query
        self.last_execute_args = args
        return self.execute_result


class FakeAcquireContext:
    def __init__(self, conn: FakeConnection) -> None:
        self._conn = conn
        self.released = False

    async def __aenter__(self) -> FakeConnection:
        return self._conn

    async def __aexit__(self, *_) -> None:
        self.released = True


class FakePool:
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.closed = False
        self._conn = FakeConnection()
        self._acquire_ctx: FakeAcquireContext | None = None

    def acquire(self) -> FakeAcquireContext:
        self._acquire_ctx = FakeAcquireContext(self._conn)
        return self._acquire_ctx

    async def close(self) -> None:
        self.closed = True


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

BASE_CONFIG: dict = {
    "pool_min": 2,
    "pool_max": 5,
    "max_queries": 1000,
    "connection_lifetime": 60,
    "command_timeout": 10,
}


@pytest.fixture(scope="module")
def fkr() -> Faker:
    """모듈 내 공유 Faker 인스턴스."""
    return Faker()


@pytest.fixture
def db_creds(fkr: Faker) -> dict:
    """테스트마다 임의의 DB 연결 정보를 생성합니다.

    패스워드에 URL 특수문자(:, @, /)가 포함되지 않도록 alphanumeric만 사용합니다.
    """
    return {
        "host": fkr.ipv4(),
        "port": fkr.random_int(min=1024, max=65535),
        "user": fkr.user_name(),
        "password": fkr.lexify("??????????", letters="abcdefghijklmnopqrstuvwxyz0123456789"),
        "database": fkr.slug(),
    }


@pytest.fixture
def db_url(db_creds: dict) -> str:
    """db_creds로부터 DATABASE_URL 문자열을 생성합니다."""
    c = db_creds
    return f"postgresql://{c['user']}:{c['password']}@{c['host']}:{c['port']}/{c['database']}"


@pytest.fixture
def fake_pool() -> FakePool:
    return FakePool()


@pytest_asyncio.fixture
async def connected_pg(fake_pool: FakePool, db_url: str, monkeypatch: pytest.MonkeyPatch) -> PostgresPool:
    """FakePool이 주입된 연결 완료 상태의 PostgresPool."""

    async def _fake_create_pool(**kwargs):
        fake_pool.kwargs = kwargs
        return fake_pool

    monkeypatch.setattr("asyncpg.create_pool", _fake_create_pool)

    pg = PostgresPool({**BASE_CONFIG, "database_url": db_url})
    await pg.connect()
    return pg


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_init_default_state():
    """생성 직후 pool은 None이고 is_connected는 False다."""
    pg = PostgresPool(BASE_CONFIG)

    assert pg.pool is None
    assert pg.is_connected is False
    assert pg.config is BASE_CONFIG


# ---------------------------------------------------------------------------
# connect() — database_url
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_sets_connected_state(connected_pg: PostgresPool, fake_pool: FakePool):
    """connect() 후 is_connected가 True이고 pool이 설정된다."""
    assert connected_pg.is_connected is True
    assert connected_pg.pool is fake_pool


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_parses_url_correctly(connected_pg: PostgresPool, fake_pool: FakePool, db_creds: dict):
    """Faker로 생성한 URL이 올바르게 파싱돼 create_pool에 전달된다."""
    assert fake_pool.kwargs["host"] == db_creds["host"]
    assert fake_pool.kwargs["port"] == db_creds["port"]
    assert fake_pool.kwargs["user"] == db_creds["user"]
    assert fake_pool.kwargs["password"] == db_creds["password"]
    assert fake_pool.kwargs["database"] == db_creds["database"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_passes_pool_config(connected_pg: PostgresPool, fake_pool: FakePool):
    """pool 설정 값이 create_pool에 올바르게 전달된다."""
    assert fake_pool.kwargs["min_size"] == BASE_CONFIG["pool_min"]
    assert fake_pool.kwargs["max_size"] == BASE_CONFIG["pool_max"]
    assert fake_pool.kwargs["max_queries"] == BASE_CONFIG["max_queries"]
    assert fake_pool.kwargs["max_inactive_connection_lifetime"] == BASE_CONFIG["connection_lifetime"]
    assert fake_pool.kwargs["command_timeout"] == BASE_CONFIG["command_timeout"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_uses_default_pool_config(db_url: str, monkeypatch: pytest.MonkeyPatch):
    """pool 설정 키가 없으면 기본값이 create_pool에 전달된다."""
    captured: dict = {}

    async def _fake_create_pool(**kwargs):
        captured.update(kwargs)
        return FakePool()

    monkeypatch.setattr("asyncpg.create_pool", _fake_create_pool)

    pg = PostgresPool({"database_url": db_url})
    await pg.connect()

    assert captured["min_size"] == 10
    assert captured["max_size"] == 20
    assert captured["max_queries"] == 50000
    assert captured["max_inactive_connection_lifetime"] == 300
    assert captured["command_timeout"] == 60


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_with_env_var_url(db_url: str, db_creds: dict, monkeypatch: pytest.MonkeyPatch):
    """DATABASE_URL 환경 변수로 연결하면 URL이 올바르게 파싱된다."""
    monkeypatch.setenv("DATABASE_URL", db_url)
    captured: dict = {}

    async def _fake_create_pool(**kwargs):
        captured.update(kwargs)
        return FakePool()

    monkeypatch.setattr("asyncpg.create_pool", _fake_create_pool)

    pg = PostgresPool(BASE_CONFIG)
    await pg.connect()

    assert pg.is_connected is True
    assert captured["host"] == db_creds["host"]
    assert captured["port"] == db_creds["port"]
    assert captured["user"] == db_creds["user"]
    assert captured["password"] == db_creds["password"]
    assert captured["database"] == db_creds["database"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_with_individual_params(db_creds: dict, monkeypatch: pytest.MonkeyPatch):
    """개별 host/port/user/password/database 키로 연결한다."""
    captured: dict = {}

    async def _fake_create_pool(**kwargs):
        captured.update(kwargs)
        return FakePool()

    monkeypatch.setattr("asyncpg.create_pool", _fake_create_pool)

    config = {**BASE_CONFIG, **db_creds}
    pg = PostgresPool(config)
    await pg.connect()

    assert pg.is_connected is True
    assert captured["host"] == db_creds["host"]
    assert captured["port"] == db_creds["port"]
    assert captured["user"] == db_creds["user"]
    assert captured["password"] == db_creds["password"]
    assert captured["database"] == db_creds["database"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_with_individual_env_vars(db_creds: dict, monkeypatch: pytest.MonkeyPatch):
    """DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME 환경 변수로 연결한다."""
    monkeypatch.setenv("DB_HOST", db_creds["host"])
    monkeypatch.setenv("DB_PORT", str(db_creds["port"]))
    monkeypatch.setenv("DB_USER", db_creds["user"])
    monkeypatch.setenv("DB_PASSWORD", db_creds["password"])
    monkeypatch.setenv("DB_NAME", db_creds["database"])
    captured: dict = {}

    async def _fake_create_pool(**kwargs):
        captured.update(kwargs)
        return FakePool()

    monkeypatch.setattr("asyncpg.create_pool", _fake_create_pool)

    pg = PostgresPool(BASE_CONFIG)
    await pg.connect()

    assert pg.is_connected is True
    assert captured["host"] == db_creds["host"]
    assert captured["port"] == db_creds["port"]
    assert captured["user"] == db_creds["user"]
    assert captured["password"] == db_creds["password"]
    assert captured["database"] == db_creds["database"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_failure_keeps_disconnected(db_url: str, monkeypatch: pytest.MonkeyPatch):
    """연결 실패 시 예외가 전파되고 is_connected는 False를 유지한다."""

    async def _failing_create_pool(**_):
        raise OSError("connection refused")

    monkeypatch.setattr("asyncpg.create_pool", _failing_create_pool)

    pg = PostgresPool({**BASE_CONFIG, "database_url": db_url})

    with pytest.raises(OSError, match="connection refused"):
        await pg.connect()

    assert pg.is_connected is False
    assert pg.pool is None


# ---------------------------------------------------------------------------
# disconnect()
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_disconnect_closes_pool(connected_pg: PostgresPool, fake_pool: FakePool):
    """disconnect() 호출 시 pool이 닫히고 is_connected가 False가 된다."""
    await connected_pg.disconnect()

    assert fake_pool.closed is True
    assert connected_pg.pool is None
    assert connected_pg.is_connected is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_disconnect_without_connect_is_safe():
    """connect() 없이 disconnect()를 호출해도 예외가 발생하지 않는다."""
    pg = PostgresPool(BASE_CONFIG)
    await pg.disconnect()


# ---------------------------------------------------------------------------
# acquire()
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_acquire_yields_connection(connected_pg: PostgresPool, fake_pool: FakePool):
    """acquire()가 FakeConnection을 컨텍스트 변수로 전달한다."""
    async with connected_pg.acquire() as conn:
        assert conn is fake_pool._conn


@pytest.mark.unit
@pytest.mark.asyncio
async def test_acquire_releases_connection_on_exit(connected_pg: PostgresPool, fake_pool: FakePool):
    """블록 정상 종료 시 커넥션이 풀에 반환된다."""
    async with connected_pg.acquire():
        pass

    assert fake_pool._acquire_ctx.released is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_acquire_releases_connection_on_exception(connected_pg: PostgresPool, fake_pool: FakePool):
    """블록에서 예외가 발생해도 커넥션이 반환되고 예외가 전파된다."""
    with pytest.raises(RuntimeError, match="query error"):
        async with connected_pg.acquire():
            raise RuntimeError("query error")

    assert fake_pool._acquire_ctx.released is True


# ---------------------------------------------------------------------------
# transaction()
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transaction_yields_connection(connected_pg: PostgresPool, fake_pool: FakePool):
    """transaction()이 FakeConnection을 컨텍스트 변수로 전달한다."""
    async with connected_pg.transaction() as conn:
        assert conn is fake_pool._conn


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transaction_commits_on_success(connected_pg: PostgresPool, fake_pool: FakePool):
    """블록이 정상 종료되면 트랜잭션이 커밋된다."""
    async with connected_pg.transaction():
        pass

    assert fake_pool._conn.last_tx.committed is True
    assert fake_pool._conn.last_tx.rolled_back is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transaction_rolls_back_on_exception(connected_pg: PostgresPool, fake_pool: FakePool):
    """블록에서 예외가 발생하면 트랜잭션이 롤백되고 예외가 전파된다."""
    with pytest.raises(ValueError, match="tx error"):
        async with connected_pg.transaction():
            raise ValueError("tx error")

    assert fake_pool._conn.last_tx.rolled_back is True
    assert fake_pool._conn.last_tx.committed is False


# ---------------------------------------------------------------------------
# fetch_all()
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_all_returns_rows(connected_pg: PostgresPool, fake_pool: FakePool):
    """fetch_all()이 conn.fetch()의 결과를 그대로 반환한다."""
    fake_pool._conn.fetch_result = [{"id": 1}, {"id": 2}]

    result = await connected_pg.fetch_all("SELECT * FROM t")

    assert result == [{"id": 1}, {"id": 2}]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_all_passes_query_and_args(connected_pg: PostgresPool, fake_pool: FakePool):
    """fetch_all()이 쿼리와 바인딩 파라미터를 conn.fetch()에 그대로 전달한다."""
    await connected_pg.fetch_all("SELECT * FROM t WHERE id = $1", 42)

    assert fake_pool._conn.last_fetch_query == "SELECT * FROM t WHERE id = $1"
    assert fake_pool._conn.last_fetch_args == (42,)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_all_returns_empty_when_not_connected():
    """연결되지 않은 상태에서 fetch_all()은 빈 리스트를 반환한다."""
    pg = PostgresPool(BASE_CONFIG)

    result = await pg.fetch_all("SELECT * FROM t")

    assert result == []


# ---------------------------------------------------------------------------
# fetch_one()
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_one_returns_row(connected_pg: PostgresPool, fake_pool: FakePool):
    """fetch_one()이 conn.fetchrow()의 결과를 그대로 반환한다."""
    fake_pool._conn.fetchrow_result = {"id": 1, "name": "test"}

    result = await connected_pg.fetch_one("SELECT * FROM t WHERE id = $1", 1)

    assert result == {"id": 1, "name": "test"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_one_passes_query_and_args(connected_pg: PostgresPool, fake_pool: FakePool):
    """fetch_one()이 쿼리와 바인딩 파라미터를 conn.fetchrow()에 그대로 전달한다."""
    await connected_pg.fetch_one("SELECT * FROM t WHERE id = $1", 99)

    assert fake_pool._conn.last_fetch_query == "SELECT * FROM t WHERE id = $1"
    assert fake_pool._conn.last_fetch_args == (99,)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_one_returns_none_when_not_connected():
    """연결되지 않은 상태에서 fetch_one()은 None을 반환한다."""
    pg = PostgresPool(BASE_CONFIG)

    result = await pg.fetch_one("SELECT * FROM t WHERE id = $1", 1)

    assert result is None


# ---------------------------------------------------------------------------
# execute()
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_returns_status(connected_pg: PostgresPool, fake_pool: FakePool):
    """execute()가 conn.execute()의 명령 상태 문자열을 그대로 반환한다."""
    fake_pool._conn.execute_result = "INSERT 0 1"

    result = await connected_pg.execute("INSERT INTO t (v) VALUES ($1)", 1)

    assert result == "INSERT 0 1"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_passes_query_and_args(connected_pg: PostgresPool, fake_pool: FakePool):
    """execute()가 쿼리와 바인딩 파라미터를 conn.execute()에 그대로 전달한다."""
    await connected_pg.execute("DELETE FROM t WHERE id = $1", 7)

    assert fake_pool._conn.last_execute_query == "DELETE FROM t WHERE id = $1"
    assert fake_pool._conn.last_execute_args == (7,)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_returns_none_when_not_connected():
    """연결되지 않은 상태에서 execute()는 None을 반환한다."""
    pg = PostgresPool(BASE_CONFIG)

    result = await pg.execute("DELETE FROM t WHERE id = $1", 1)

    assert result is None
