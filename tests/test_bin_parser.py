import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from buisness_logic.bin_parser.log_parser import LogParser


def _make_gps_message(u, lat, lng):
    """Helper: create a mock GPS message whose to_dict() returns the given fields."""
    msg = MagicMock()
    msg.to_dict.return_value = {"U": u, "Lat": lat, "Lng": lng}
    return msg


def test_extract_gps_coordinates_empty_file(tmp_path):
    """Parser raises ValueError when the file is empty (0 bytes)."""
    print("\n[TEST] Running empty file validation test...")
    empty_file = tmp_path / "empty.bin"
    empty_file.write_bytes(b"")

    with pytest.raises(ValueError, match="is empty"):
        LogParser.extract_gps_coordinates(str(empty_file))

    print("[TEST] Verified that parser raises ValueError for empty files.")
    print("[RESULT] test_extract_gps_coordinates_empty_file - PASSED")


@patch("buisness_logic.bin_parser.log_parser.os.path.getsize", return_value=1024)
def test_extract_gps_coordinates_file_open_error(mock_getsize):
    """Parser returns an empty list when the log file cannot be opened."""
    print("\n[TEST] Running file open error handling test...")
    with patch("buisness_logic.bin_parser.log_parser.mavutil.mavlink_connection") as mock_conn:
        mock_conn.side_effect = Exception("Failed to open file")

        coordinates = LogParser.extract_gps_coordinates("dummy_path.bin")

        assert coordinates == []
        mock_conn.assert_called_once_with("dummy_path.bin")
        print("[TEST] Verified that parser safely returned empty list on file open error.")
        print("[RESULT] test_extract_gps_coordinates_file_open_error - PASSED")


@patch("buisness_logic.bin_parser.log_parser.os.path.getsize", return_value=1024)
def test_extract_gps_coordinates_no_messages(mock_getsize):
    """Parser returns an empty list when the log contains no GPS messages."""
    print("\n[TEST] Running empty log test (no GPS messages)...")
    with patch("buisness_logic.bin_parser.log_parser.mavutil.mavlink_connection") as mock_conn:
        mock_log = MagicMock()
        mock_log.recv_match.return_value = None
        mock_conn.return_value = mock_log

        coordinates = LogParser.extract_gps_coordinates("dummy_path.bin")

        assert coordinates == []
        mock_log.recv_match.assert_called_once_with(type="GPS", blocking=False)
        mock_log.close.assert_called_once()
        print("[TEST] Verified that parser safely returned empty list for empty logs.")
        print("[RESULT] test_extract_gps_coordinates_no_messages - PASSED")


@patch("buisness_logic.bin_parser.log_parser.os.path.getsize", return_value=1024)
def test_extract_gps_coordinates_valid_and_invalid_messages(mock_getsize):
    """Parser extracts only valid GPS messages and ignores invalid records."""
    print("\n[TEST] Running mixed valid/invalid GPS message extraction test...")
    with patch("buisness_logic.bin_parser.log_parser.mavutil.mavlink_connection") as mock_conn:
        mock_log = MagicMock()

        msg_valid_1 = _make_gps_message(u=1, lat=32.1234567, lng=34.7654321)
        msg_invalid_u = _make_gps_message(u=0, lat=32.111111, lng=34.111111)
        msg_invalid_lat_zero = _make_gps_message(u=1, lat=0.0, lng=34.222222)
        msg_invalid_lng_none = _make_gps_message(u=1, lat=32.333333, lng=None)
        msg_valid_2 = _make_gps_message(u=1, lat=32.44444444, lng=34.55555555)

        mock_log.recv_match.side_effect = [
            msg_valid_1,
            msg_invalid_u,
            msg_invalid_lat_zero,
            msg_invalid_lng_none,
            msg_valid_2,
            None,
        ]
        mock_conn.return_value = mock_log

        coordinates = LogParser.extract_gps_coordinates("dummy_path.bin")

        assert coordinates == [
            (32.123457, 34.765432),
            (32.444444, 34.555556),
        ]
        mock_log.close.assert_called_once()
        print(f"[TEST] Verified coordinates parsed: {coordinates}")
        print("[RESULT] test_extract_gps_coordinates_valid_and_invalid_messages - PASSED")


@patch("buisness_logic.bin_parser.log_parser.os.path.getsize", return_value=1024)
def test_extract_gps_coordinates_exception_during_message_parsing(mock_getsize):
    """Parser continues parsing after a message raises an exception."""
    print("\n[TEST] Running parser resilience test (corrupted message)...")
    with patch("buisness_logic.bin_parser.log_parser.mavutil.mavlink_connection") as mock_conn:
        mock_log = MagicMock()

        msg_valid_1 = _make_gps_message(u=1, lat=32.123456, lng=34.765432)

        msg_corrupted = MagicMock()
        msg_corrupted.to_dict.return_value = {"U": 1, "Lat": None, "Lng": None}
        # Override to_dict to return a dict where get("Lat") triggers an error
        corrupt_data = {"U": 1}

        class CorruptDict(dict):
            def get(self, key, default=None):
                if key == "Lat":
                    raise ValueError("Corrupt Lat")
                return super().get(key, default)

        msg_corrupted.to_dict.return_value = CorruptDict(corrupt_data)

        msg_valid_2 = _make_gps_message(u=1, lat=32.999999, lng=34.999999)

        mock_log.recv_match.side_effect = [
            msg_valid_1,
            msg_corrupted,
            msg_valid_2,
            None,
        ]
        mock_conn.return_value = mock_log

        coordinates = LogParser.extract_gps_coordinates("dummy_path.bin")

        assert coordinates == [
            (32.123456, 34.765432),
            (32.999999, 34.999999),
        ]
        mock_log.close.assert_called_once()
        print(
            f"[TEST] Verified that corrupted message was skipped, and valid coordinates were parsed: {coordinates}"
        )
        print("[RESULT] test_extract_gps_coordinates_exception_during_message_parsing - PASSED")


@patch("buisness_logic.bin_parser.log_parser.os.path.getsize", return_value=1024)
def test_extract_gps_coordinates_edge_cases(mock_getsize):
    """Parser handles edge cases such as missing attributes and type variations."""
    print(
        "\n[TEST] Running extreme edge cases, non-numeric values, and missing attributes tests..."
    )
    with patch("buisness_logic.bin_parser.log_parser.mavutil.mavlink_connection") as mock_conn:
        mock_log = MagicMock()

        msg_lat_zero = _make_gps_message(u=1, lat=0.0, lng=34.123456)
        msg_lng_zero = _make_gps_message(u=1, lat=32.123456, lng=0.0)

        # Missing Lat key in dict
        msg_missing_lat = MagicMock()
        msg_missing_lat.to_dict.return_value = {"U": 1, "Lng": 34.123456}

        # Missing Lng key in dict
        msg_missing_lng = MagicMock()
        msg_missing_lng.to_dict.return_value = {"U": 1, "Lat": 32.123456}

        msg_non_numeric = _make_gps_message(u=1, lat="invalid_string", lng=34.123456)
        msg_rounding = _make_gps_message(u=1, lat=-32.1234564, lng=-34.1234566)

        # U as string "1" should not match == 1
        msg_u_string = _make_gps_message(u="1", lat=32.123456, lng=34.123456)

        # U as float 1.0 should match == 1
        msg_u_float = _make_gps_message(u=1.0, lat=32.123456, lng=34.123456)

        mock_log.recv_match.side_effect = [
            msg_lat_zero,
            msg_lng_zero,
            msg_missing_lat,
            msg_missing_lng,
            msg_non_numeric,
            msg_rounding,
            msg_u_string,
            msg_u_float,
            None,
        ]
        mock_conn.return_value = mock_log

        coordinates = LogParser.extract_gps_coordinates("dummy_path.bin")

        assert coordinates == [
            (-32.123456, -34.123457),
            (32.123456, 34.123456),
        ]
        mock_log.close.assert_called_once()
        print(
            f"[TEST] Verified all boundary/type/missing edge cases. Correctly parsed: {coordinates}"
        )
        print("[RESULT] test_extract_gps_coordinates_edge_cases - PASSED")


@patch("buisness_logic.bin_parser.log_parser.os.path.getsize", return_value=1024)
def test_close_called_on_exception(mock_getsize):
    """Parser always calls log.close() even when an unexpected exception occurs."""
    print("\n[TEST] Running finally/close guarantee test...")
    with patch("buisness_logic.bin_parser.log_parser.mavutil.mavlink_connection") as mock_conn:
        mock_log = MagicMock()
        mock_log.recv_match.side_effect = RuntimeError("Unexpected crash")
        mock_conn.return_value = mock_log

        with pytest.raises(RuntimeError, match="Unexpected crash"):
            LogParser.extract_gps_coordinates("dummy_path.bin")

        mock_log.close.assert_called_once()
        print("[TEST] Verified that log.close() is called even after an exception.")
        print("[RESULT] test_close_called_on_exception - PASSED")


if __name__ == "__main__":
    import traceback

    tests = [
        test_extract_gps_coordinates_empty_file,
        test_extract_gps_coordinates_file_open_error,
        test_extract_gps_coordinates_no_messages,
        test_extract_gps_coordinates_valid_and_invalid_messages,
        test_extract_gps_coordinates_exception_during_message_parsing,
        test_extract_gps_coordinates_edge_cases,
        test_close_called_on_exception,
    ]

    print("Running parser tests from test_bin_parser.py")
    passed = 0
    failed = 0

    for test in tests:
        test_name = test.__name__
        try:
            test()
        except Exception:
            failed += 1
            print(f"[RESULT] {test_name} - FAILED")
            traceback.print_exc()
        else:
            passed += 1
            print(f"[RESULT] {test_name} - PASSED")
        print("---")

    print(f"Finished: {passed} passed, {failed} failed")
