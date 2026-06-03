import logging
from typing import List, Tuple

from pymavlink import mavutil

logger = logging.getLogger(__name__)


class LogParser:

    @staticmethod
    def extract_gps_coordinates(file_path: str) -> List[Tuple[float, float]]:
        synced_data: list[tuple[float, float]] = []
        try:
            log = mavutil.mavlink_connection(file_path)
        except Exception as e:
            logger.error("Error opening file %s: %s", file_path, e)
            return synced_data

        logger.info("Starting log file scanning: %s", file_path)

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
                    logger.error("Unexpected error parsing message: %s", e)
            log.close()

        logger.info("Scanning finished. %d points extracted.", len(synced_data))
        return synced_data
