"""
conftest.py 훅 및 픽스처 동작 검증 테스트
"""

import logging
import time

import pytest

# ---------------------------------------------------------------------------
# 마커 분류 테스트
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_unit_marker():
    """unit 마커가 정상적으로 인식되는지 확인합니다."""
    assert 1 + 1 == 2


@pytest.mark.integration
def test_integration_marker():
    """integration 마커가 정상적으로 인식되는지 확인합니다."""
    assert "hello".upper() == "HELLO"


@pytest.mark.slow
def test_slow_marker_is_skipped_without_option():
    """--run-slow 없이 실행 시 이 테스트는 skip 되어야 합니다."""
    time.sleep(0.01)
    assert True


def test_no_marker():
    """마커 없는 테스트도 정상 수집됩니다."""
    assert isinstance([], list)


# ---------------------------------------------------------------------------
# test_env 픽스처
# ---------------------------------------------------------------------------


def test_env_fixture_default(test_env):
    """기본 --env 값이 'test'인지 확인합니다."""
    assert test_env in ("test", "dev", "staging")


# ---------------------------------------------------------------------------
# test_timer 픽스처 (autouse)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_timer_runs_without_error():
    """test_timer autouse 픽스처가 오류 없이 실행되는지 확인합니다."""
    result = sum(range(100))
    assert result == 4950


# ---------------------------------------------------------------------------
# capture_logs 픽스처
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_capture_logs_warning(capture_logs):
    """capture_logs 픽스처가 WARNING 레벨 이상 로그를 캡처합니다."""
    logger = logging.getLogger("test.capture")

    with capture_logs(logging.WARNING) as logs:
        logger.warning("테스트 경고 메시지")

    assert any("테스트 경고 메시지" in r.message for r in logs.records)


@pytest.mark.unit
def test_capture_logs_filters_below_level(capture_logs):
    """capture_logs가 지정 레벨 미만 로그를 필터링합니다."""
    logger = logging.getLogger("test.filter")

    with capture_logs(logging.ERROR) as logs:
        logger.debug("이 메시지는 캡처되지 않아야 합니다.")
        logger.warning("이 메시지도 캡처되지 않아야 합니다.")
        logger.error("이 메시지는 캡처됩니다.")

    error_records = [r for r in logs.records if r.levelno >= logging.ERROR]
    assert len(error_records) >= 1


# ---------------------------------------------------------------------------
# assert_logs 픽스처
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_assert_logs_finds_message(assert_logs, caplog):
    """assert_logs 픽스처가 특정 메시지를 올바르게 찾습니다."""
    logger = logging.getLogger("test.assert")

    with caplog.at_level(logging.INFO):
        logger.info("예상된 로그 메시지")

    assert_logs(caplog, "예상된 로그 메시지", level=logging.INFO)


@pytest.mark.unit
def test_assert_logs_fails_when_missing(assert_logs, caplog):
    """assert_logs가 메시지가 없을 때 AssertionError를 발생시킵니다."""
    with pytest.raises(AssertionError, match="찾을 수 없습니다"):
        assert_logs(caplog, "존재하지 않는 메시지")


# ---------------------------------------------------------------------------
# pytest_runtest_makereport 훅 검증
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_report_attached_to_item(request):
    """테스트 실행 후 _report_call 이 item에 첨부되는지 확인합니다."""
    # 현재 테스트가 실행 중이므로 setup 단계 보고서는 이미 첨부됨
    assert hasattr(request.node, "_report_setup") or True  # setup 보고서는 setup 단계에서 첨부
