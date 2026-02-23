# 커밋 메시지 작성 가이드

## 기본 구조

```
<타입>: <제목>          ← Header (필수)

<본문>                  ← Body (선택)

<꼬리말>               ← Footer (선택)
```

---

## Header (헤더)

한 줄로 변경 사항을 요약합니다. **50자 이내**로 작성합니다.

```
<타입>: <제목>
```

### 타입 목록

| 타입 | 설명 |
|------|------|
| `feat` | 새로운 기능 추가 |
| `fix` | 버그 수정 |
| `docs` | 문서 수정 |
| `style` | 코드 포맷팅, 세미콜론 누락 등 (로직 변경 없음) |
| `refactor` | 코드 리팩토링 (기능 변경 없음) |
| `test` | 테스트 코드 추가 또는 수정 |
| `chore` | 빌드 설정, 패키지 관리 등 기타 변경 |
| `perf` | 성능 개선 |
| `ci` | CI/CD 설정 변경 |
| `revert` | 이전 커밋 되돌리기 |

### 제목 작성 규칙

- 마침표(`.`) 없이 작성
- 명령문 형태로 작성 (예: "기능 추가", "버그 수정")
- 첫 글자는 소문자(영문) 또는 명사(한글)로 시작

---

## Body (본문)

**무엇을**, **왜** 변경했는지 설명합니다. **한 줄에 72자 이내**로 작성합니다.

- 헤더와 한 줄 빈 줄로 구분
- 여러 항목은 `-` bullet point로 나열
- "어떻게"보다 "왜"에 집중하여 작성

---

## Footer (꼬리말)

이슈 연결, Breaking Change 등을 명시합니다.

### 이슈 참조

```
Closes #이슈번호      ← 이슈 자동 종료
Fixes #이슈번호       ← 버그 수정으로 이슈 종료
Refs #이슈번호        ← 이슈 참조만 (종료 안 함)
```

### Breaking Change

하위 호환성이 깨지는 변경사항은 반드시 명시합니다.

```
BREAKING CHANGE: <변경 내용 설명>
```

---

## 작성 예시

### 기능 추가

```
feat: 사용자 로그인 기능 추가

- JWT 기반 인증 구현
- 로그인 실패 시 에러 메시지 반환
- 토큰 만료 시간 1시간으로 설정

Closes #12
```

### 버그 수정

```
fix: 비밀번호 공백 입력 시 서버 오류 수정

공백 문자열이 유효성 검사를 통과하는 문제 수정.
입력값 trim() 처리 후 길이 검증 로직 추가.

Fixes #34
```

### 리팩토링

```
refactor: 사용자 조회 로직 서비스 레이어로 분리

컨트롤러에 집중된 DB 접근 코드를 UserService로 이동.
단일 책임 원칙(SRP) 준수를 위한 구조 개선.
```

### Breaking Change 포함

```
feat: API 응답 형식 변경

모든 API 응답을 { data, status, message } 구조로 통일.

BREAKING CHANGE: 기존 응답 필드명 result → data로 변경됨.
클라이언트 코드 수정 필요.

Closes #56
```

---

## 나쁜 예시

```
# 너무 모호함
fix: 버그 수정

# 타입 없음
로그인 기능 추가

# 너무 장황한 헤더
feat: 사용자가 이메일과 비밀번호를 입력하여 로그인할 수 있는 기능을 JWT 토큰 방식으로 추가
```

---

## 참고 자료

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Angular Commit Message Guidelines](https://github.com/angular/angular/blob/main/CONTRIBUTING.md#commit)