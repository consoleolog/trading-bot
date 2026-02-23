# pytest 테스트 가이드

## 개요

[pytest](https://docs.pytest.org/)는 Python 표준 테스트 프레임워크입니다.
`pytest-cov`를 함께 사용해 코드 커버리지를 측정합니다.

---

## 설치

```bash
uv add --dev pytest pytest-cov pytest-asyncio
```

---

## 설정 파일 (`pytest.ini`)

```ini
[pytest]
testpaths = tests

python_files = test_*.py
python_classes = Test*
python_functions = test_*

addopts =
    -v
    --tb=short
    --strict-markers
    --cov=.
    --cov-report=term-missing
    --cov-report=html:htmlcov

markers =
    unit: 단위 테스트
    integration: 통합 테스트
    slow: 실행 시간이 긴 테스트

filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning

asyncio_mode = auto
```

---

## 설정 항목 설명

### 기본 설정

| 옵션 | 값 | 설명 |
|------|----|------|
| `testpaths` | `tests` | 테스트 파일을 탐색할 디렉토리 |
| `python_files` | `test_*.py` | 테스트 파일로 인식할 패턴 |
| `python_classes` | `Test*` | 테스트 클래스로 인식할 패턴 |
| `python_functions` | `test_*` | 테스트 함수로 인식할 패턴 |

### addopts (기본 실행 옵션)

| 옵션 | 설명 |
|------|------|
| `-v` | 테스트 이름을 상세하게 출력 |
| `--tb=short` | 실패 시 트레이스백을 짧게 출력 |
| `--strict-markers` | 등록되지 않은 마커 사용 시 오류 발생 |
| `--cov=.` | 프로젝트 전체 커버리지 측정 |
| `--cov-report=term-missing` | 터미널에 미커버 줄 번호 출력 |
| `--cov-report=html:htmlcov` | `htmlcov/` 디렉토리에 HTML 리포트 생성 |

### markers (커스텀 마커)

`--strict-markers` 옵션으로 인해 사용할 마커는 반드시 여기에 등록해야 합니다.

| 마커 | 설명 |
|------|------|
| `unit` | 단위 테스트 — 외부 의존성 없이 단일 함수/클래스 검증 |
| `integration` | 통합 테스트 — DB, API 등 외부 시스템 연동 검증 |
| `slow` | 실행 시간이 긴 테스트 |

```python
import pytest

@pytest.mark.unit
def test_something():
    assert 1 + 1 == 2

@pytest.mark.slow
def test_heavy_computation():
    ...
```

### filterwarnings (경고 필터)

테스트 실행 시 발생하는 경고를 제어합니다.

| 설정 | 설명 |
|------|------|
| `ignore::DeprecationWarning` | 지원 중단 예정 경고 무시 |
| `ignore::PendingDeprecationWarning` | 지원 중단 대기 경고 무시 |

특정 경고만 오류로 처리하려면:

```ini
filterwarnings =
    error                          # 모든 경고를 오류로
    ignore::DeprecationWarning     # DeprecationWarning은 예외
```

### asyncio_mode (비동기 테스트 모드)

`pytest-asyncio`의 동작 방식을 지정합니다.

| 값 | 설명 |
|----|------|
| `auto` | `async def test_*` 함수를 자동으로 비동기 테스트로 처리 (권장) |
| `strict` | `@pytest.mark.asyncio` 마커를 명시해야만 비동기 테스트로 처리 |

---

## 디렉토리 구조

```
tests/
├── __init__.py
├── conftest.py          # 공통 fixture 정의
├── test_example.py      # 단위 테스트 예시
└── integration/
    └── test_api.py      # 통합 테스트 예시
```

---

## 테스트 작성 예시

### 기본 테스트

```python
# tests/test_example.py
import pytest


@pytest.mark.unit
def test_addition():
    assert 1 + 1 == 2


@pytest.mark.unit
def test_string():
    assert "hello".upper() == "HELLO"
```

### 클래스 기반 테스트

```python
@pytest.mark.unit
class TestCalculator:
    def test_add(self):
        assert 1 + 2 == 3

    def test_subtract(self):
        assert 5 - 3 == 2
```

### fixture 사용

```python
# tests/conftest.py
import pytest

@pytest.fixture
def sample_data():
    return {"name": "Alice", "age": 30}
```

```python
# tests/test_example.py
def test_name(sample_data):
    assert sample_data["name"] == "Alice"
```

### 예외 테스트

```python
def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        _ = 1 / 0
```

### 파라미터화 테스트

```python
@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
])
def test_add(a, b, expected):
    assert a + b == expected
```

### 비동기 테스트 (`pytest-asyncio`)

`asyncio_mode = auto` 설정 시, `async def` 함수를 그대로 테스트로 사용할 수 있습니다.

```python
import asyncio


@pytest.mark.unit
async def test_async_function():
    await asyncio.sleep(0)
    assert True


@pytest.mark.unit
async def test_async_with_fixture(async_fixture):
    result = await async_fixture
    assert result is not None
```

비동기 fixture도 동일하게 작성합니다:

```python
# tests/conftest.py
import pytest


@pytest.fixture
async def async_fixture():
    # 비동기 setup
    yield "value"
    # 비동기 teardown
```

---

## 실행 방법

```bash
# 전체 테스트 실행
pytest

# 특정 파일만 실행
pytest tests/test_example.py

# 특정 함수만 실행
pytest tests/test_example.py::test_addition

# 마커로 필터링
pytest -m unit
pytest -m "not slow"

# 커버리지 없이 빠르게 실행
pytest --no-cov

# 실패한 테스트만 재실행
pytest --lf
```

---

## 커버리지 리포트

터미널 출력 예시:

```
---------- coverage: platform win32, python 3.10 ----------
Name        Stmts   Miss  Cover   Missing
-----------------------------------------
main.py        4      0   100%
-----------------------------------------
TOTAL          4      0   100%
```

HTML 리포트는 `htmlcov/index.html`에서 확인할 수 있습니다.

---

## 참고 자료

- [pytest 공식 문서](https://docs.pytest.org/)
- [pytest-cov 문서](https://pytest-cov.readthedocs.io/)
- [pytest 마커 가이드](https://docs.pytest.org/en/stable/how-to/mark.html)
- [pytest-asyncio 문서](https://pytest-asyncio.readthedocs.io/)