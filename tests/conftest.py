"""
conftest.py - pytest 전역 훅 및 픽스처 모음

이 파일은 프로젝트 루트에 위치하여 모든 테스트에 공통 적용됩니다.
"""

import logging
import sys
import time
import warnings
from collections import defaultdict

import pytest

# Windows 터미널 UTF-8 출력 보장
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")


# ---------------------------------------------------------------------------
# 커스텀 CLI 옵션
# ---------------------------------------------------------------------------


def pytest_addoption(parser):
    """커스텀 커맨드라인 옵션을 추가합니다."""
    parser.addoption(
        "--run-slow", action="store_true", default=False, help="@pytest.mark.slow 마커가 붙은 테스트도 실행합니다."
    )
    parser.addoption(
        "--env",
        action="store",
        default="test",
        choices=["test", "dev", "staging"],
        help="테스트 실행 환경을 지정합니다. (기본값: test)",
    )


# ---------------------------------------------------------------------------
# 세션 훅
# ---------------------------------------------------------------------------


def pytest_sessionstart(session):
    """테스트 세션이 시작될 때 헤더를 출력합니다."""
    print("\n" + "=" * 60)
    print("  테스트 세션 시작")
    print("=" * 60)


def pytest_sessionfinish(session, exitstatus):
    """테스트 세션이 종료될 때 호출됩니다."""
    print("\n" + "=" * 60)
    exit_labels = {
        0: "성공 (모든 테스트 통과)",
        1: "실패 (일부 테스트 실패)",
        2: "사용자에 의해 중단",
        3: "내부 오류 발생",
        4: "커맨드라인 옵션 오류",
        5: "수집된 테스트 없음",
    }
    label = exit_labels.get(int(exitstatus), f"알 수 없는 종료 코드: {exitstatus}")
    print(f"  테스트 세션 종료: {label}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# 수집 훅
# ---------------------------------------------------------------------------


def pytest_collection_modifyitems(config, items):
    """
    수집된 테스트 항목을 수정합니다.
    - --run-slow 옵션이 없으면 slow 마커 테스트를 건너뜁니다.
    - slow 마커 테스트를 목록 맨 뒤로 재정렬합니다.
    """
    skip_slow = pytest.mark.skip(reason="--run-slow 옵션 없이는 실행되지 않습니다.")

    slow_items = []
    normal_items = []

    for item in items:
        if item.get_closest_marker("slow"):
            if not config.getoption("--run-slow"):
                item.add_marker(skip_slow)
            slow_items.append(item)
        else:
            normal_items.append(item)

    # slow 테스트를 뒤로 배치
    items[:] = normal_items + slow_items


def pytest_collection_finish(session):
    """테스트 수집이 끝난 후 수집 통계를 출력합니다."""
    counts = defaultdict(int)
    for item in session.items:
        for marker in ("unit", "integration", "slow"):
            if item.get_closest_marker(marker):
                counts[marker] += 1
                break
        else:
            counts["unmarked"] += 1

    if session.items:
        print(f"\n수집된 테스트: {len(session.items)}개", end="")
        parts = []
        for label in ("unit", "integration", "slow", "unmarked"):
            if counts[label]:
                parts.append(f"{label}={counts[label]}")
        if parts:
            print(f"  ({', '.join(parts)})", end="")
        print()


# ---------------------------------------------------------------------------
# 실행 훅
# ---------------------------------------------------------------------------


def pytest_runtest_setup(item):
    """각 테스트 setup 단계에서 환경 정보를 로깅합니다."""
    env = item.config.getoption("--env", default="test")
    item._test_env = env  # 이후 훅에서 참조 가능


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    테스트 결과 보고서를 생성하는 훅입니다.
    - 실패한 테스트에 대해 item에 결과를 저장해 픽스처에서 활용 가능하게 합니다.
    """
    outcome = yield
    report = outcome.get_result()

    # request 픽스처에서 접근할 수 있도록 결과를 item에 첨부
    setattr(item, f"_report_{report.when}", report)

    # 실패 시 추가 컨텍스트 출력
    if report.when == "call" and report.failed:
        markers = [m.name for m in item.iter_markers()]
        if markers:
            print(f"\n  [마커] {', '.join(markers)}")
        env = getattr(item, "_test_env", "test")
        print(f"  [환경] {env}")


# ---------------------------------------------------------------------------
# 터미널 요약 훅
# ---------------------------------------------------------------------------


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """테스트 완료 후 커스텀 요약을 터미널에 출력합니다."""
    passed = len(terminalreporter.stats.get("passed", []))
    failed = len(terminalreporter.stats.get("failed", []))
    skipped = len(terminalreporter.stats.get("skipped", []))
    errors = len(terminalreporter.stats.get("error", []))

    terminalreporter.write_sep("-", "커스텀 테스트 요약")
    terminalreporter.write_line(f"  통과: {passed}  실패: {failed}  건너뜀: {skipped}  오류: {errors}")

    if failed:
        terminalreporter.write_line("\n  실패한 테스트 목록:")
        for report in terminalreporter.stats.get("failed", []):
            terminalreporter.write_line(f"    - {report.nodeid}")


# ---------------------------------------------------------------------------
# 픽스처
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def test_env(request):
    """--env 옵션으로 지정된 테스트 환경 이름을 반환합니다."""
    return request.config.getoption("--env")


@pytest.fixture(autouse=True)
def test_timer(request):
    """모든 테스트의 실행 시간을 측정하고 느린 테스트(1초 초과)를 경고합니다."""
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start

    threshold = 1.0
    if elapsed > threshold:
        warnings.warn(f"느린 테스트: {request.node.name} ({elapsed:.2f}s > {threshold}s)", UserWarning, stacklevel=2)
        print(f"\n  [경고] 느린 테스트: {request.node.name} ({elapsed:.2f}s > {threshold}s)")


@pytest.fixture
def capture_logs(caplog):
    """
    지정한 레벨 이상의 로그를 캡처하는 픽스처입니다.

    사용 예:
        def test_something(capture_logs):
            with capture_logs(logging.WARNING) as logs:
                do_something()
            assert "expected message" in logs.text
    """
    import contextlib

    @contextlib.contextmanager
    def _capture(level=logging.DEBUG):
        with caplog.at_level(level):
            yield caplog

    return _capture


@pytest.fixture
def assert_logs():
    """
    특정 로그 메시지가 발생했는지 검증하는 픽스처입니다.

    사용 예:
        def test_something(assert_logs, caplog):
            do_something()
            assert_logs(caplog, "expected message", level=logging.WARNING)
    """

    def _assert(caplog, message, level=logging.DEBUG):
        level_name = logging.getLevelName(level)
        matching = [r for r in caplog.records if r.levelno >= level and message in r.message]
        assert matching, (
            f"로그에서 '{message}' (레벨: {level_name} 이상)를 찾을 수 없습니다.\n"
            f"캡처된 로그:\n" + "\n".join(f"  [{r.levelname}] {r.message}" for r in caplog.records)
        )

    return _assert
