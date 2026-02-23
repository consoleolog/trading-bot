# 개발 가이드

> 이 문서는 개발 원칙과 방식을 정의합니다.
> 코드 스타일 규칙은 [CODING_CONVENTION.md](CODING_CONVENTION.md),
> 커밋 메시지 형식은 [COMMIT_MESSAGE.md](COMMIT_MESSAGE.md)를 참고하세요.

## 1. TDD (테스트 주도 개발)

기능을 구현할 때 테스트 코드를 함께 작성합니다.
구현 후에 테스트를 추가하는 것이 아니라, **테스트와 구현을 함께 커밋**하는 것을 원칙으로 합니다.

### 기본 원칙

- 모든 함수/메서드에는 대응하는 테스트가 존재해야 합니다.
- 엣지 케이스(null, 빈 값, 잘못된 입력 등)를 반드시 테스트합니다.

### 테스트 파일 구조

```
tests/
├── conftest.py          # 공통 fixture
├── test_post.py         # 게시글 관련 단위 테스트
└── integration/
    └── test_api.py      # 통합 테스트
```

### 테스트 작성 절차

```
1. 구현할 함수의 입력 / 출력 명세 정의
2. 정상 케이스 테스트 작성
3. 엣지 케이스 테스트 작성
4. 함수 구현
5. 테스트 통과 확인
6. 기능 코드 + 테스트 코드 함께 커밋
```

### 예시

```python
# tests/test_post.py
import pytest
from src.post import parse_post_request, save_post


@pytest.mark.unit
class TestParsePostRequest:
    def test_returns_title_and_content(self, mock_request):
        title, content = parse_post_request(mock_request)
        assert title == "제목입니다"
        assert content == "본문입니다"

    def test_raises_when_title_is_missing(self):
        with pytest.raises(ValueError):
            parse_post_request({"content": "본문만 있음"})

    def test_raises_when_title_is_empty_string(self):
        with pytest.raises(ValueError):
            parse_post_request({"title": "", "content": "본문"})

    def test_raises_when_content_is_missing(self):
        with pytest.raises(ValueError):
            parse_post_request({"title": "제목만 있음"})


@pytest.mark.unit
class TestSavePost:
    def test_returns_saved_post_with_id(self):
        post = save_post("제목", "본문")
        assert post["id"] is not None
        assert post["title"] == "제목"

    def test_raises_when_title_exceeds_max_length(self):
        with pytest.raises(ValueError):
            save_post("가" * 101, "본문")
```

---

## 2. 레이어 기반 최소화 설계

> **작은 기능, 작은 변경, 작은 책임.**

하나의 함수는 하나의 역할만 수행합니다.
기능을 레이어(입력 처리 → 비즈니스 로직 → 응답 생성)로 분리하여 각 레이어를 독립적으로 테스트할 수 있도록 합니다.

### 레이어 구분 원칙

| 레이어 | 역할 | 예시 |
|--------|------|------|
| 입력 처리 | 요청에서 값 추출, 유효성 검증 | `parse_post_request()` |
| 비즈니스 로직 | 실제 동작 수행, DB 저장 | `save_post()` |
| 응답 생성 | 결과를 반환 형식으로 변환 | `build_post_response()` |

### 레이어 분리 예시

```python
# 금지: 하나의 함수에 모든 로직이 뒤섞임
def create_post(request, response):
    title = request["title"]
    content = request["content"]
    post_id = db.insert("INSERT INTO posts VALUES (?, ?)", title, content)
    response.write(f'{{"id": {post_id}, "title": "{title}"}}')


# 권장: 각 역할을 독립 함수로 분리
def parse_post_request(request: dict) -> tuple[str, str]:
    """요청에서 title, content를 추출하고 기본 유효성 검증."""
    title = request.get("title")
    content = request.get("content")
    if not title or not content:
        raise ValueError("title과 content는 필수입니다.")
    if len(title) > 100:
        raise ValueError("title은 100자를 초과할 수 없습니다.")
    return title, content


def save_post(title: str, content: str) -> dict:
    """게시글을 저장하고 저장된 게시글 정보를 반환."""
    ...


def build_post_response(post: dict) -> dict:
    """저장된 게시글을 API 응답 형식으로 변환."""
    ...
```

---

## 3. 개발 예제 — 기능 단계 분리

새 기능을 개발하기 전, 아래 단계를 순서대로 진행합니다.

### Step 1. 단계 구분

기능을 독립적인 처리 단계로 나눕니다.

```
게시글 작성 기능
├── 입력 값 추출     : parse_post_request(request) → (title, content)
├── 게시글 저장      : save_post(title, content) → dict
└── 응답 생성        : build_post_response(post) → dict
```

### Step 2. 입출력 명세 정의

각 단계의 입력과 출력을 타입 힌트로 명확히 정의합니다.

```python
def parse_post_request(request: dict) -> tuple[str, str]: ...
def save_post(title: str, content: str) -> dict: ...
def build_post_response(post: dict) -> dict: ...
```

### Step 3. 테스트 케이스 정의

각 단계별로 테스트할 시나리오를 먼저 목록화합니다.

| 함수 | 테스트 케이스 |
|------|--------------|
| `parse_post_request` | title 누락 / content 누락 / title 100자 초과 / 정상 입력 |
| `save_post` | 정상 저장 후 id 반환 / DB 오류 시 예외 발생 |
| `build_post_response` | 저장된 post를 응답 형식으로 변환 |

### Step 4. 구현 및 커밋

테스트와 구현을 짝으로 커밋합니다. 한 번에 전체를 커밋하지 않습니다.

```
1st commit: parse_post_request 구현 + 테스트
2nd commit: save_post 구현 + 테스트
3rd commit: build_post_response 구현 + 테스트
```

---

## 4. 커밋 방법

> **꼭 필요한 최소한의 단위로, 충분한 설명과 함께.**

### 커밋 원칙

- **최소 단위**: 하나의 커밋은 하나의 논리적 변경만 담습니다.
- **테스트 포함**: 기능 구현 커밋에는 반드시 테스트가 함께 포함되어야 합니다.

### 커밋 메시지 형식

상세 규칙은 [COMMIT_MESSAGE.md](COMMIT_MESSAGE.md)를 참고합니다.

```
<타입>: <제목 — 50자 이내>

<변경 내용, 이유, 주의사항 — 72자 이내>
```

**예시**

```
feat: 게시글 입력 값 파싱 함수 추가

- 요청에서 title, content를 추출하는 parse_post_request 구현
- title 또는 content 누락 시 ValueError 발생
- title 최대 길이(100자) 초과 시 ValueError 발생
```

---

## 참고 자료

- [CODING_CONVENTION.md](CODING_CONVENTION.md) — 코드 스타일 및 네이밍 규칙
- [COMMIT_MESSAGE.md](COMMIT_MESSAGE.md) — 커밋 메시지 형식
- [docs/configs/PYTEST.md](../configs/PYTEST.md) — 테스트 설정 및 작성 가이드
- [pytest 공식 문서](https://docs.pytest.org/)
- [PEP 8 — Python 스타일 가이드](https://peps.python.org/pep-0008/)