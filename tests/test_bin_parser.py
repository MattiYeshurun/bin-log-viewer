import sys
import os
from unittest.mock import MagicMock, patch
import pytest

# Ensure the 'src' directory is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from bin_parser.log_parser import LogParser


def test_extract_gps_coordinates_file_open_error():
    """Test when opening the connection raises an exception."""
    print("\n[TEST] Running file open error handling test...")
    with patch("bin_parser.log_parser.mavutil.mavlink_connection") as mock_conn:
        mock_conn.side_effect = Exception("Failed to open file")
        
        coordinates = LogParser.extract_gps_coordinates("dummy_path.bin")
        
        assert coordinates == []
        mock_conn.assert_called_once_with("dummy_path.bin")
        print("[TEST] Verified that parser safely returned empty list on file open error.")


def test_extract_gps_coordinates_no_messages():
    """Test when the file opens but contains no GPS messages (returns None on first recv_match)."""
    print("\n[TEST] Running empty log test (no GPS messages)...")
    with patch("bin_parser.log_parser.mavutil.mavlink_connection") as mock_conn:
        mock_log = MagicMock()
        mock_log.recv_match.return_value = None
        mock_conn.return_value = mock_log
        
        coordinates = LogParser.extract_gps_coordinates("dummy_path.bin")
        
        assert coordinates == []
        mock_log.recv_match.assert_called_once_with(type="GPS", blocking=False)
        print("[TEST] Verified that parser safely returned empty list for empty logs.")


def test_extract_gps_coordinates_valid_and_invalid_messages():
    """Test extraction of mixed valid and invalid GPS messages."""
    print("\n[TEST] Running mixed valid/invalid GPS message extraction test...")
    with patch("bin_parser.log_parser.mavutil.mavlink_connection") as mock_conn:
        mock_log = MagicMock()
        
        # Define mock GPS messages
        # Message 1: Valid
        msg_valid_1 = MagicMock()
        msg_valid_1.U = 1
        msg_valid_1.Lat = 32.1234567
        msg_valid_1.Lng = 34.7654321
        
        # Message 2: Invalid (U is not 1)
        msg_invalid_u = MagicMock()
        msg_invalid_u.U = 0
        msg_invalid_u.Lat = 32.111111
        msg_invalid_u.Lng = 34.111111
        
        # Message 3: Invalid (Lat is 0)
        msg_invalid_lat_zero = MagicMock()
        msg_invalid_lat_zero.U = 1
        msg_invalid_lat_zero.Lat = 0.0
        msg_invalid_lat_zero.Lng = 34.222222
        
        # Message 4: Invalid (Lng is None)
        msg_invalid_lng_none = MagicMock()
        msg_invalid_lng_none.U = 1
        msg_invalid_lng_none.Lat = 32.333333
        msg_invalid_lng_none.Lng = None
        
        # Message 5: Valid (needs rounding check)
        msg_valid_2 = MagicMock()
        msg_valid_2.U = 1
        msg_valid_2.Lat = 32.44444444
        msg_valid_2.Lng = 34.55555555
        
        # Mock recv_match to return these messages in order, then None to exit loop
        mock_log.recv_match.side_effect = [
            msg_valid_1,
            msg_invalid_u,
            msg_invalid_lat_zero,
            msg_invalid_lng_none,
            msg_valid_2,
            None
        ]
        mock_conn.return_value = mock_log
        
        coordinates = LogParser.extract_gps_coordinates("dummy_path.bin")
        
        # Should only contain the 2 valid coordinates, rounded to 6 decimal places
        assert coordinates == [
            (32.123457, 34.765432),
            (32.444444, 34.555556)
        ]
        print(f"[TEST] Verified coordinates parsed: {coordinates}")


def test_extract_gps_coordinates_exception_during_message_parsing():
    """Test resilience when accessing a message raises an exception."""
    print("\n[TEST] Running parser resilience test (corrupted message)...")
    with patch("bin_parser.log_parser.mavutil.mavlink_connection") as mock_conn:
        mock_log = MagicMock()
        
        # Message 1: Valid
        msg_valid = MagicMock()
        msg_valid.U = 1
        msg_valid.Lat = 32.123456
        msg_valid.Lng = 34.765432
        
        # Message 2: Corrupted (raises exception when Lat is accessed)
        class CorruptedMessage:
            U = 1
            @property
            def Lat(self):
                raise ValueError("Corrupt Lat")
            @property
            def Lng(self):
                return 34.0
                
        msg_corrupted = CorruptedMessage()
        
        # Message 3: Valid
        msg_valid_2 = MagicMock()
        msg_valid_2.U = 1
        msg_valid_2.Lat = 32.999999
        msg_valid_2.Lng = 34.999999
        
        mock_log.recv_match.side_effect = [
            msg_valid,
            msg_corrupted,
            msg_valid_2,
            None
        ]
        mock_conn.return_value = mock_log
        
        coordinates = LogParser.extract_gps_coordinates("dummy_path.bin")
        
        # The corrupted message should be skipped, but msg_valid and msg_valid_2 should succeed
        assert coordinates == [
            (32.123456, 34.765432),
            (32.999999, 34.999999)
        ]
        print(f"[TEST] Verified that corrupted message was skipped, and valid coordinates were parsed: {coordinates}")


def test_extract_gps_coordinates_edge_cases():
    """Test extreme edge cases, non-numeric values, and missing attributes."""
    print("\n[TEST] Running extreme edge cases, non-numeric values, and missing attributes tests...")
    with patch("bin_parser.log_parser.mavutil.mavlink_connection") as mock_conn:
        mock_log = MagicMock()

        # 1. Latitude is strictly 0
        msg_lat_zero = MagicMock()
        msg_lat_zero.U = 1
        msg_lat_zero.Lat = 0.0
        msg_lat_zero.Lng = 34.123456

        # 2. Longitude is strictly 0
        msg_lng_zero = MagicMock()
        msg_lng_zero.U = 1
        msg_lng_zero.Lat = 32.123456
        msg_lng_zero.Lng = 0.0

        # 3. Missing 'Lat' attribute
        class MissingLatMessage:
            U = 1
            Lng = 34.123456
        msg_missing_lat = MissingLatMessage()

        # 4. Missing 'Lng' attribute
        class MissingLngMessage:
            U = 1
            Lat = 32.123456
        msg_missing_lng = MissingLngMessage()

        # 5. Non-numeric 'Lat' value (round will throw TypeError)
        msg_non_numeric = MagicMock()
        msg_non_numeric.U = 1
        msg_non_numeric.Lat = "invalid_string"
        msg_non_numeric.Lng = 34.123456

        # 6. Rounding of boundary and negative values
        msg_rounding = MagicMock()
        msg_rounding.U = 1
        msg_rounding.Lat = -32.1234564
        msg_rounding.Lng = -34.1234566

        # 7. U is a string "1" (should be ignored since "1" != 1)
        msg_u_string = MagicMock()
        msg_u_string.U = "1"
        msg_u_string.Lat = 32.123456
        msg_u_string.Lng = 34.123456

        # 8. U is a float 1.0 (should be processed since 1.0 == 1)
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
            None
        ]
        mock_conn.return_value = mock_log

        coordinates = LogParser.extract_gps_coordinates("dummy_path.bin")

        # Only the rounding message and the float-U message should be extracted successfully
        assert coordinates == [
            (-32.123456, -34.123457),
            (32.123456, 34.123456)
        ]
        print(f"[TEST] Verified all boundary/type/missing edge cases. Correctly parsed: {coordinates}")



test_extract_gps_coordinates_file_open_error()
test_extract_gps_coordinates_no_messages()
test_extract_gps_coordinates_valid_and_invalid_messages()
test_extract_gps_coordinates_exception_during_message_parsing()
test_extract_gps_coordinates_edge_cases()   

