from typing import List, Tuple

from pymavlink import mavutil


class LogParser:

    @staticmethod
    def extract_gps_coordinates(file_path: str) -> List[Tuple[float, float]]:
        synced_data: list[tuple[float, float]] = []
        try:
            log = mavutil.mavlink_connection(file_path)
        except Exception as e:
            print(f"Error opening file {file_path}: {e}")
            return synced_data

        print(f"[PARSER] Starting log file scanning: {file_path}")

        while True:
            message = log.recv_match(type="GPS", blocking=False)

            if message is None:
                break

            if getattr(message, "U", None) == 1:
                try:
                    lat = getattr(message, "Lat", None)
                    lng = getattr(message, "Lng", None)

                    if lat == 0 or lng == 0 or lat is None or lng is None:
                        continue

                    synced_data.append((round(lat, 6), round(lng, 6)))

                except Exception as e:
                    print(f"[PARSER] Unexpected error parsing message: {e}")
                    continue

        print(f"[PARSER] Scanning finished. {len(synced_data)} points extracted.")
        return synced_data
