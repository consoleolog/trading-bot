# 코드 스타일 가이드

> 이 프로젝트는 [Ruff](https://docs.astral.sh/ruff/)로 스타일을 자동 적용합니다.
> 설정 파일: `.ruff.toml` | 상세 설명: [docs/RUFF.md](../configs/RUFF.md)

---

## 기본 규칙

| 항목 | 규칙 |
|------|------|
| 줄 길이 | 최대 **120자** |
| 들여쓰기 | **스페이스 4칸** (탭 금지) |
| 따옴표 | **큰따옴표** (`"`) |
| 줄바꿈 | OS 자동 감지 |
| Python 버전 | **3.10+** 문법 사용 |

---

## 네이밍 컨벤션

| 대상 | 규칙 | 예시 |
|------|------|------|
| 변수 / 함수 / 메서드 | `snake_case` | `user_name`, `get_user()` |
| 클래스 | `PascalCase` | `UserService`, `HttpClient` |
| 상수 | `UPPER_SNAKE_CASE` | `MAX_RETRY`, `BASE_URL` |
| 비공개 멤버 | `_snake_case` (언더스코어 접두사) | `_internal_value` |
| 모듈 / 패키지 | `snake_case` | `user_service.py` |
| 미사용 변수 | `_` 또는 `_변수명` | `for _ in range(10)` |

---

## import

### 순서 (자동 정렬)

```python
# 1. 표준 라이브러리
import os
import sys

# 2. 서드파티 라이브러리
import requests

# 3. 내부 모듈 (src/)
from src.utils import helper
```

### 규칙

- 그룹 사이에 빈 줄 한 줄
- 사용하지 않는 import 금지
- `from module import *` 금지

---

## 타입 힌트

Python 3.10+ 내장 타입을 사용합니다. `typing` 모듈의 구버전 타입은 사용하지 않습니다.

```python
# 금지
from typing import List, Dict, Optional, Union

def foo(items: List[str]) -> Optional[Dict[str, int]]:
    ...

# 권장
def foo(items: list[str]) -> dict[str, int] | None:
    ...
```

| 구버전 (`typing`) | 현재 권장 |
|-------------------|-----------|
| `List[str]` | `list[str]` |
| `Dict[str, int]` | `dict[str, int]` |
| `Optional[str]` | `str \| None` |
| `Union[str, int]` | `str \| int` |
| `Tuple[int, ...]` | `tuple[int, ...]` |

---

## 함수 / 메서드

### 기본 인자로 가변 객체 금지

```python
# 금지 (B006)
def add_item(items=[]):
    items.append(1)
    return items

# 권장
def add_item(items=None):
    if items is None:
        items = []
    items.append(1)
    return items
```

### 미사용 루프 변수

```python
# 금지 (B007)
for i in range(10):
    print("hello")

# 권장
for _ in range(10):
    print("hello")
```

---

## 조건문 / 분기

### 삼항 연산자 활용

```python
# 지양
if condition:
    x = True
else:
    x = False

# 권장 (SIM108)
x = True if condition else False
```

### 중첩 if 단순화

```python
# 지양
if a:
    if b:
        do_something()

# 권장 (SIM102)
if a and b:
    do_something()
```

---

## 컴프리헨션

불필요한 중간 단계를 제거합니다.

```python
# 금지 (C400)
result = list([x for x in range(10)])

# 권장
result = [x for x in range(10)]
```

```python
# 금지 (C416)
result = [x for x in some_list]

# 권장
result = list(some_list)
```

---

## 문자열

- 기본 따옴표: **큰따옴표** (`"`)
- f-string 사용 권장

```python
# 지양
name = 'Alice'
greeting = 'Hi, ' + name

# 권장
name = "Alice"
greeting = f"Hi, {name}"
```

---

## 자동 적용 도구

커밋 시 pre-commit 훅이 아래 순서로 자동 실행됩니다.

```
1. ruff check --fix   → lint 위반 자동 수정
2. ruff format        → 포맷 자동 적용
3. pytest --no-cov    → 테스트 실행
```

수동으로 실행할 경우:

```bash
ruff check --fix . && ruff format .
```

---

## 규칙 예외 처리

불가피하게 규칙을 무시해야 할 경우 인라인 주석을 사용합니다.
**남용 금지** — 예외 처리 시 이유를 주석으로 명시합니다.

```python
# 특정 줄 무시
x = 1  # noqa: E741  # 외부 라이브러리 인터페이스와 일치시키기 위해

# 파일 전체 무시 (파일 최상단)
# ruff: noqa
```

---

## 참고 자료

- [PEP 8 — Python 스타일 가이드](https://peps.python.org/pep-0008/)
- [docs/RUFF.md](../configs/RUFF.md) — Ruff 설정 상세 설명