import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from buisness_logic.bin_parser.log_parser import LogParser


def test_extract_gps_coordinates_file_open_error():
    """Parser returns an empty list when the log file cannot be opened."""
    print("\n[TEST] Running file open error handling test...")
    with patch("buisness_logic.bin_parser.log_parser.mavutil.mavlink_connection") as mock_conn:
        mock_conn.side_effect = Exception("Failed to open file")

        coordinates = LogParser.extract_gps_coordinates("dummy_path.bin")

        assert coordinates == []
        mock_conn.assert_called_once_with("dummy_path.bin")
        print("[TEST] Verified that parser safely returned empty list on file open error.")
        print("[RESULT] test_extract_gps_coordinates_file_open_error - PASSED")


def test_extract_gps_coordinates_no_messages():
    """Parser returns an empty list when the log contains no GPS messages."""
    print("\n[TEST] Running empty log test (no GPS messages)...")
    with patch("buisness_logic.bin_parser.log_parser.mavutil.mavlink_connection") as mock_conn:
        mock_log = MagicMock()
        mock_log.recv_match.return_value = None
        mock_conn.return_value = mock_log

        coordinates = LogParser.extract_gps_coordinates("dummy_path.bin")

        assert coordinates == []
        mock_log.recv_match.assert_called_once_with(type="GPS", blocking=False)
        print("[TEST] Verified that parser safely returned empty list for empty logs.")
        print("[RESULT] test_extract_gps_coordinates_no_messages - PASSED")


def test_extract_gps_coordinates_valid_and_invalid_messages():
    """Parser extracts only valid GPS messages and ignores invalid records."""
    print("\n[TEST] Running mixed valid/invalid GPS message extraction test...")
    with patch("buisness_logic.bin_parser.log_parser.mavutil.mavlink_connection") as mock_conn:
        mock_log = MagicMock()

        msg_valid_1 = MagicMock()
        msg_valid_1.U = 1
        msg_valid_1.Lat = 32.1234567
        msg_valid_1.Lng = 34.7654321

        msg_invalid_u = MagicMock()
        msg_invalid_u.U = 0
        msg_invalid_u.Lat = 32.111111
        msg_invalid_u.Lng = 34.111111

        msg_invalid_lat_zero = MagicMock()
        msg_invalid_lat_zero.U = 1
        msg_invalid_lat_zero.Lat = 0.0
        msg_invalid_lat_zero.Lng = 34.222222

        msg_invalid_lng_none = MagicMock()
        msg_invalid_lng_none.U = 1
        msg_invalid_lng_none.Lat = 32.333333
        msg_invalid_lng_none.Lng = None

        msg_valid_2 = MagicMock()
        msg_valid_2.U = 1
        msg_valid_2.Lat = 32.44444444
        msg_valid_2.Lng = 34.55555555

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
        print(f"[TEST] Verified coordinates parsed: {coordinates}")
        print("[RESULT] test_extract_gps_coordinates_valid_and_invalid_messages - PASSED")


def test_extract_gps_coordinates_exception_during_message_parsing():
    """Parser continues parsing after a message raises an exception."""
    print("\n[TEST] Running parser resilience test (corrupted message)...")
    with patch("buisness_logic.bin_parser.log_parser.mavutil.mavlink_connection") as mock_conn:
        mock_log = MagicMock()

        msg_valid_1 = MagicMock()
        msg_valid_1.U = 1
        msg_valid_1.Lat = 32.123456
        msg_valid_1.Lng = 34.765432

        class CorruptedMessage:
            U = 1

            @property
            def Lat(self):
                raise ValueError("Corrupt Lat")

            @property
            def Lng(self):
                return 34.0

        msg_corrupted = CorruptedMessage()

        msg_valid_2 = MagicMock()
        msg_valid_2.U = 1
        msg_valid_2.Lat = 32.999999
        msg_valid_2.Lng = 34.999999

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
        print(
            f"[TEST] Verified that corrupted message was skipped, and valid coordinates were parsed: {coordinates}"
        )
        print("[RESULT] test_extract_gps_coordinates_exception_during_message_parsing - PASSED")


def test_extract_gps_coordinates_edge_cases():
    """Parser handles edge cases such as missing attributes and type variations."""
    print(
        "\n[TEST] Running extreme edge cases, non-numeric values, and missing attributes tests..."
    )
    with patch("buisness_logic.bin_parser.log_parser.mavutil.mavlink_connection") as mock_conn:
        mock_log = MagicMock()

        msg_lat_zero = MagicMock()
        msg_lat_zero.U = 1
        msg_lat_zero.Lat = 0.0
        msg_lat_zero.Lng = 34.123456

        msg_lng_zero = MagicMock()
        msg_lng_zero.U = 1
        msg_lng_zero.Lat = 32.123456
        msg_lng_zero.Lng = 0.0

        class MissingLatMessage:
            U = 1
            Lng = 34.123456

        msg_missing_lat = MissingLatMessage()

        class MissingLngMessage:
            U = 1
            Lat = 32.123456

        msg_missing_lng = MissingLngMessage()

        msg_non_numeric = MagicMock()
        msg_non_numeric.U = 1
        msg_non_numeric.Lat = "invalid_string"
        msg_non_numeric.Lng = 34.123456

        msg_rounding = MagicMock()
        msg_rounding.U = 1
        msg_rounding.Lat = -32.1234564
        msg_rounding.Lng = -34.1234566

        msg_u_string = MagicMock()
        msg_u_string.U = "1"
        msg_u_string.Lat = 32.123456
        msg_u_string.Lng = 34.123456

        msg_u_float = MagicMock()
        msg_u_float.U = 1.0
        msg_u_float.Lat = 32.123456
        msg_u_float.Lng = 34.123456

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
        print(
            f"[TEST] Verified all boundary/type/missing edge cases. Correctly parsed: {coordinates}"
        )
        print("[RESULT] test_extract_gps_coordinates_edge_cases - PASSED")


if __name__ == "__main__":
    import traceback

    tests = [
        test_extract_gps_coordinates_file_open_error,
        test_extract_gps_coordinates_no_messages,
        test_extract_gps_coordinates_valid_and_invalid_messages,
        test_extract_gps_coordinates_exception_during_message_parsing,
        test_extract_gps_coordinates_edge_cases,
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

