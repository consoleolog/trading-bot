# Ruff 설정 가이드

## 개요

[Ruff](https://docs.astral.sh/ruff/)는 Rust로 작성된 고속 Python 린터 및 포매터입니다.
기존 `flake8`, `isort`, `black` 등 여러 도구를 단일 도구로 대체합니다.

---

## 설치

```bash
uv add --dev ruff pre-commit
```

---

## pre-commit 연동

커밋 시 ruff가 자동으로 실행되도록 pre-commit 훅을 설정합니다.

### 설정 파일 (`.pre-commit-config.yaml`)

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.2
    hooks:
      - id: ruff          # lint + 자동 수정
        args: [--fix]
      - id: ruff-format   # 포맷
```

### 훅 등록

```bash
pre-commit install
```

`git commit` 실행 시 아래 순서로 자동 실행됩니다.

```
ruff (lint)     → 위반 코드 자동 수정 후 중단 (수정된 파일 재스테이징 필요)
ruff-format     → 포맷 자동 적용
```

### 동작 예시

```bash
$ git commit -m "feat: 새 기능 추가"

ruff.....................................................................Failed
- hook id: ruff
- files were modified by this hook   ← lint 자동 수정 발생

ruff-format..............................................................Passed
```

lint 수정이 발생한 경우 변경 파일을 다시 스테이징한 후 재커밋합니다.

```bash
git add .
git commit -m "feat: 새 기능 추가"
```

### 전체 파일 수동 실행

커밋 없이 전체 파일에 pre-commit을 실행합니다.

```bash
pre-commit run --all-files
```

### 훅 버전 업데이트

```bash
pre-commit autoupdate
```

---

## 설정 파일

프로젝트 루트의 `.ruff.toml`에서 관리합니다.

```toml
line-length = 120
target-version = "py310"

[lint]
select = [...]
ignore = [...]

[format]
quote-style = "double"
```

---

## 주요 설정 설명

### 기본 설정

| 옵션 | 값 | 설명 |
|------|----|------|
| `line-length` | `120` | 한 줄 최대 길이 |
| `target-version` | `"py310"` | 대상 Python 버전 (3.10) |

---

### lint 규칙

활성화된 규칙 목록(`select`)입니다.

| 코드 | 출처 | 설명 |
|------|------|------|
| `E` | pycodestyle | PEP 8 스타일 오류 |
| `W` | pycodestyle | PEP 8 스타일 경고 |
| `F` | Pyflakes | 미사용 변수, 정의되지 않은 이름 등 |
| `I` | isort | import 정렬 |
| `N` | pep8-naming | 네이밍 컨벤션 (클래스는 PascalCase 등) |
| `UP` | pyupgrade | 구버전 Python 문법을 최신 문법으로 자동 업그레이드 |
| `B` | flake8-bugbear | 잠재적 버그 및 안티패턴 감지 |
| `C4` | flake8-comprehensions | 불필요한 comprehension 단순화 |
| `SIM` | flake8-simplify | 코드 단순화 제안 |
| `RUF` | Ruff-specific | Ruff 자체 규칙 |

비활성화된 규칙 목록(`ignore`)입니다.

| 코드 | 이유 |
|------|------|
| `E501` | 줄 길이 검사는 formatter(`ruff format`)에 위임 |

---

### 규칙별 수정 예시

#### `E` / `W` — pycodestyle

PEP 8 스타일 위반을 감지합니다.

```python
# 수정 전
x=1
y = x+1
def foo () :
    pass

# 수정 후
x = 1
y = x + 1
def foo():
    pass
```

#### `F` — Pyflakes

사용하지 않는 import, 정의되지 않은 이름 등 논리적 오류를 감지합니다.

```python
# 수정 전 (F401: 미사용 import)
import os
import sys

print("hello")

# 수정 후
print("hello")
```

```python
# 수정 전 (F841: 미사용 변수)
def foo():
    result = expensive_call()
    return 42

# 수정 후
def foo():
    return 42
```

#### `I` — isort

import 순서를 표준 라이브러리 → 서드파티 → 내부 모듈 순으로 정렬합니다.

```python
# 수정 전
import mymodule
import os
import requests
import sys

# 수정 후
import os
import sys

import requests

import mymodule
```

#### `N` — pep8-naming

네이밍 컨벤션을 강제합니다.

```python
# 수정 전 (N801: 클래스명은 PascalCase)
class my_class:
    pass

# 수정 전 (N803: 함수 인자는 snake_case)
def foo(myArg):
    pass

# 수정 후
class MyClass:
    pass

def foo(my_arg):
    pass
```

#### `UP` — pyupgrade

구버전 문법을 최신 Python 문법으로 자동 업그레이드합니다.

```python
# 수정 전 (UP006: 구버전 타입 힌트)
from typing import List, Dict, Optional

def foo(items: List[str]) -> Optional[Dict[str, int]]:
    pass

# 수정 후 (Python 3.10+)
def foo(items: list[str]) -> dict[str, int] | None:
    pass
```

#### `B` — flake8-bugbear

잠재적 버그와 안티패턴을 감지합니다.

```python
# 수정 전 (B006: 가변 기본 인자)
def foo(items=[]):
    items.append(1)
    return items

# 수정 후
def foo(items=None):
    if items is None:
        items = []
    items.append(1)
    return items
```

```python
# 수정 전 (B007: 루프 변수 미사용)
for i in range(10):
    print("hello")

# 수정 후
for _ in range(10):
    print("hello")
```

#### `C4` — flake8-comprehensions

불필요한 comprehension을 단순화합니다.

```python
# 수정 전 (C400: list() 대신 list comprehension 불필요)
result = list([x for x in range(10)])

# 수정 후
result = [x for x in range(10)]
```

```python
# 수정 전 (C416: 불필요한 comprehension)
result = [x for x in some_list]

# 수정 후
result = list(some_list)
```

#### `SIM` — flake8-simplify

코드를 더 간결하게 단순화합니다.

```python
# 수정 전 (SIM108: 삼항 연산자 사용 가능)
if condition:
    x = True
else:
    x = False

# 수정 후
x = True if condition else False
```

```python
# 수정 전 (SIM102: 중첩 if 단순화)
if a:
    if b:
        pass

# 수정 후
if a and b:
    pass
```

#### `RUF` — Ruff-specific

Ruff 자체 규칙입니다.

```python
# 수정 전 (RUF013: Optional 타입 힌트에 암묵적 None 허용 금지)
def foo(x: str = None):
    pass

# 수정 후
def foo(x: str | None = None):
    pass
```

---

### isort 설정

```toml
[lint.isort]
known-first-party = ["src"]
```

- `known-first-party`: 프로젝트 내부 모듈로 인식할 패키지 목록
- import 순서: 표준 라이브러리 → 서드파티 → 내부 모듈

---

### format 설정

| 옵션 | 값 | 설명 |
|------|----|------|
| `quote-style` | `"double"` | 문자열 따옴표를 큰따옴표(`"`)로 통일 |
| `indent-style` | `"space"` | 들여쓰기를 스페이스로 통일 |
| `line-ending` | `"auto"` | OS에 맞는 줄바꿈 문자 자동 설정 |
| `line-length` | `120` | formatter 기준 줄 길이 |
| `skip-magic-trailing-comma` | `true` | trailing comma가 있어도 강제 줄바꿈 하지 않음 |

#### format 수정 예시

**`quote-style = "double"`**

```python
# 수정 전
name = 'hello'
message = f'Hi, {name}'

# 수정 후
name = "hello"
message = f"Hi, {name}"
```

**`indent-style = "space"`**

```python
# 수정 전 (탭 사용)
def foo():
	return 1

# 수정 후 (4 스페이스)
def foo():
    return 1
```

**`skip-magic-trailing-comma = true`**

```python
# trailing comma가 있어도 한 줄로 유지 (강제 줄바꿈 안 함)
# 수정 전
items = [
    1,
    2,
    3,
]

# skip-magic-trailing-comma = true 이면 formatter가 아래처럼 변경하지 않음
# (trailing comma 존재를 "이 형태를 유지하겠다"는 의도로 간주하지 않음)
items = [1, 2, 3]
```

---

## 사용법

### 린트 검사

```bash
# 전체 검사
ruff check .

# 특정 파일 검사
ruff check main.py

# 자동 수정 가능한 오류 수정
ruff check --fix .
```

### 포맷

```bash
# 전체 포맷
ruff format .

# 특정 파일 포맷
ruff format main.py

# 변경 사항 미리보기 (실제 수정 없음)
ruff format --diff .
```

### 동시 실행

```bash
ruff check --fix . && ruff format .
```

---

## 규칙 관리

### 특정 줄 무시

```python
x = 1  # noqa: E741
```

### 특정 파일 전체 무시

`.ruff.toml`에서 `exclude` 설정:

```toml
exclude = [
    "migrations/",
    "*.pyi",
]
```

### 인라인으로 파일 전체 무시

```python
# ruff: noqa
```

---

## 참고 자료

- [Ruff 공식 문서](https://docs.astral.sh/ruff/)
- [규칙 전체 목록](https://docs.astral.sh/ruff/rules/)
- [설정 옵션 전체 목록](https://docs.astral.sh/ruff/settings/)
