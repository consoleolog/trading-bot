# Bandit 보안 정적 분석 가이드

[Bandit](https://bandit.readthedocs.io/)은 Python 코드의 보안 취약점을 정적으로 분석하는 도구입니다.
AST(Abstract Syntax Tree)를 순회하며 잠재적 보안 이슈를 탐지합니다.

---

## 설치

```bash
uv sync --dev
```

---

## 실행

### 기본 실행 (설정 파일 사용)

```bash
uv run bandit -c bandit.yaml -r src/
```

### 심각도·신뢰도 필터링

```bash
# MEDIUM 이상 심각도만 보고
uv run bandit -c bandit.yaml -r src/ -l

# HIGH 심각도만 보고
uv run bandit -c bandit.yaml -r src/ -ll
```

> `-l` 옵션을 추가할수록 최소 심각도가 높아집니다.
> `-l` = MEDIUM 이상, `-ll` = HIGH만

### 출력 포맷

```bash
# JSON 출력 (CI 파이프라인 연동용)
uv run bandit -c bandit.yaml -r src/ -f json -o bandit-report.json

# 화면 출력 (기본)
uv run bandit -c bandit.yaml -r src/ -f screen
```

---

## 설정 파일 (`bandit.yaml`)

```yaml
targets:
  - src                 # 분석 대상 디렉토리

exclude_dirs:
  - .venv
  - tests
  - htmlcov
  - .git

level: LOW              # 최소 심각도 (LOW | MEDIUM | HIGH)
confidence: LOW         # 최소 신뢰도 (LOW | MEDIUM | HIGH)

skips:
  - B101                # assert_used: 테스트 외 코드에서도 assert 허용
```

---

## 심각도 · 신뢰도 레벨

| 레벨 | 설명 |
|------|------|
| LOW | 잠재적 위험. 맥락에 따라 무해할 수 있음 |
| MEDIUM | 주의 필요. 코드 검토 권장 |
| HIGH | 즉시 수정 필요한 명확한 취약점 |

---

## pre-commit 통합

`.pre-commit-config.yaml`에 등록되어 있어 `git commit` 시 자동 실행됩니다.

```yaml
- id: bandit
  name: bandit
  entry: uv run bandit
  language: system
  args: [-c, bandit.yaml, -r]
  types: [python]
```

변경된 Python 파일에 대해서만 실행되며, 이슈가 발견되면 커밋이 중단됩니다.

### 수동으로 pre-commit 실행

```bash
# 변경된 파일만 검사
uv run pre-commit run bandit

# 전체 파일 검사
uv run pre-commit run bandit --all-files
```

---

## 이슈 억제 (`# nosec`)

불가피하게 특정 이슈를 무시해야 할 경우 인라인 주석으로 억제합니다.

```python
# 특정 테스트 ID 억제
subprocess.call(cmd, shell=True)  # nosec B602

# 해당 라인의 모든 이슈 억제 (지양)
subprocess.call(cmd, shell=True)  # nosec
```

> `# nosec`은 꼭 필요한 경우에만 사용하고, 이유를 함께 주석으로 남기세요.

---

## 주요 테스트 ID

| ID | 설명 |
|----|------|
| B101 | `assert` 문 사용 |
| B102 | `exec` 사용 |
| B103 | 파일 권한 설정 (`chmod`) |
| B104 | 모든 인터페이스 바인딩 (`0.0.0.0`) |
| B105–B107 | 하드코딩된 패스워드 |
| B201 | Flask 앱 디버그 모드 활성화 |
| B301–B303 | 안전하지 않은 역직렬화 (`pickle`, `marshal`) |
| B311 | 암호화 목적의 `random` 모듈 사용 |
| B324 | MD5·SHA1 등 취약한 해시 알고리즘 |
| B501–B502 | SSL/TLS 검증 비활성화 |
| B601–B602 | Shell injection 위험 (`subprocess`, `os.system`) |
| B608 | SQL injection 가능성 (문자열 포맷 쿼리) |

전체 목록: https://bandit.readthedocs.io/en/latest/plugins/index.html

---

## skips 추가 기준

`bandit.yaml`의 `skips`에 ID를 추가하기 전에 아래를 검토하세요.

1. 해당 이슈가 프로젝트 전반에서 의도적으로 사용되는가?
2. 개별 `# nosec`으로 처리할 수 없는 이유가 있는가?
3. 팀 전체가 해당 억제에 동의하는가?

전역 skip보다 **인라인 `# nosec`을 우선** 사용하세요.
