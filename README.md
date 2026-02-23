# PythonBaseProject

Python 프로젝트를 시작하기 위한 베이스 템플릿입니다.
코드 품질 도구, 보안 분석, 테스트 환경이 미리 구성되어 있습니다.

---

## 기술 스택

| 역할 | 도구 |
|------|------|
| 패키지 관리 | [uv](https://docs.astral.sh/uv/) |
| Lint / Format | [Ruff](https://docs.astral.sh/ruff/) |
| 보안 분석 | [Bandit](https://bandit.readthedocs.io/) |
| 테스트 | [pytest](https://docs.pytest.org/) + [pytest-cov](https://pytest-cov.readthedocs.io/) |
| Git 훅 | [pre-commit](https://pre-commit.com/) |
| AI 코드 리뷰 | [Claude Code Action](https://github.com/anthropics/claude-code-action) |

---

## 프로젝트 구조

```
.
├── .github/
│   ├── ISSUE_TEMPLATE/         # 이슈 템플릿
│   │   ├── bug_report.md
│   │   ├── fix.md
│   │   ├── refactor.md
│   │   └── common_feature.md
│   └── workflows/
│       ├── claude.yml
│       └── claude-pr-review.yml
├── src/                        # 소스 코드
│   └── main.py
├── tests/                      # 테스트 코드
│   ├── conftest.py             # 공통 훅 및 픽스처
│   └── test_*.py
├── docs/
│   ├── configs/                # 도구 설정 가이드
│   │   ├── BANDIT.md
│   │   ├── PYTEST.md
│   │   └── RUFF.md
│   └── guides/                 # 개발 규칙 가이드
│       ├── CODING_CONVENTION.md
│       └── COMMIT_MESSAGE.md
├── .pre-commit-config.yaml
├── .ruff.toml
├── bandit.yaml
├── pytest.ini
└── pyproject.toml
```

---

## 시작하기

### 요구 사항

- Python 3.10+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

### 설치

```bash
# 의존성 설치 (dev 포함)
uv sync --dev

# pre-commit 훅 등록
uv run pre-commit install
```

---

## 개발 워크플로우

### 실행

```bash
uv run python src/main.py
```

### Lint / Format

```bash
# lint 자동 수정 + 포맷
uv run ruff check --fix . && uv run ruff format .

# lint 확인만
uv run ruff check .
```

### 테스트

```bash
# 전체 테스트 (커버리지 포함)
uv run pytest

# 커버리지 없이 빠르게
uv run pytest --no-cov

# slow 마커 테스트 포함
uv run pytest --run-slow

# 마커로 필터링
uv run pytest -m unit
uv run pytest -m "not slow"
```

### 보안 분석

```bash
uv run bandit -c bandit.yaml -r src/
```

---

## pre-commit 훅

`git commit` 시 아래 순서로 자동 실행됩니다.

| 순서 | 훅 | 역할 |
|------|----|------|
| 1 | `ruff` | Lint 검사 및 자동 수정 |
| 2 | `ruff-format` | 코드 포맷 적용 |
| 3 | `bandit` | 보안 취약점 정적 분석 |
| 4 | `pytest` | 테스트 실행 (커버리지 제외) |

훅이 파일을 수정한 경우, 변경 사항을 다시 스테이징한 뒤 커밋합니다.

```bash
# 전체 파일 대상으로 수동 실행
uv run pre-commit run --all-files
```

---

## GitHub Actions 워크플로우

| 워크플로우 | 트리거 | 역할 |
|-----------|--------|------|
| `claude.yml` | Issue 생성/할당, PR 리뷰 코멘트 | `@claude` 멘션 시 Claude가 작업 수행 |
| `claude-pr-review.yml` | PR 오픈/업데이트 | Claude가 자동으로 PR 코드 리뷰 |

## 이슈 템플릿

| 템플릿 | 접두사 | 용도 |
|--------|--------|------|
| `bug_report` | `[BUG]` | 버그 발견 기록 |
| `fix` | `[FIX]` | 오류 수정 계획 |
| `refactor` | `[REFACTOR]` | 코드 구조 개선 |
| `common_feature` | `[COMMON]` | 공통 기능 추가 |

### CLAUDE_CODE_OAUTH_TOKEN 설정

Claude 워크플로우(`claude.yml`, `claude-pr-review.yml`) 실행을 위해 저장소 Secret에 토큰을 등록해야 합니다.

**1단계: 토큰 생성**

```bash
claude setup-token
```

출력된 토큰 값을 복사합니다.

**2단계: GitHub 저장소 Secret 등록**

저장소 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| 항목 | 값 |
|------|-----|
| Name | `CLAUDE_CODE_OAUTH_TOKEN` |
| Secret | 1단계에서 복사한 토큰 |


---

## 문서

### 도구 설정

| 문서 | 내용 |
|------|------|
| [docs/configs/BANDIT.md](docs/configs/BANDIT.md) | Bandit 보안 분석 설정 및 사용법 |
| [docs/configs/PYTEST.md](docs/configs/PYTEST.md) | pytest 설정 및 테스트 작성 가이드 |
| [docs/configs/RUFF.md](docs/configs/RUFF.md) | Ruff lint 규칙 설명 |

### 개발 규칙

| 문서 | 내용 |
|------|------|
| [docs/guides/CODING_GUIDE.md](docs/guides/CODING_GUIDE.md) | TDD, 커밋 가이드 |
| [docs/guides/CODING_CONVENTION.md](docs/guides/CODING_CONVENTION.md) | 코드 스타일 및 네이밍 규칙 |
| [docs/guides/COMMIT_MESSAGE.md](docs/guides/COMMIT_MESSAGE.md) | 커밋 메시지 작성 가이드 |
