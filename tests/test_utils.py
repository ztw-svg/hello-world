from transcriber_tool.utils import format_timestamp


def test_format_timestamp_mm_ss() -> None:
    assert format_timestamp(65, "mm:ss") == "[01:05]"


def test_format_timestamp_hh_mm_ss() -> None:
    assert format_timestamp(3661, "hh:mm:ss") == "[01:01:01]"
