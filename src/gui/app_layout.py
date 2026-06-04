import asyncio
import logging
import os
from typing import List, Tuple

import flet as ft
import flet_map as ftm

from buisness_logic.bin_parser.log_parser import LogParser

logger = logging.getLogger(__name__)

TILE_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}.png"


class BinLogViewerApp:

    def __init__(self, page: ft.Page) -> None:
        logger.info("Initializing BinLogViewerApp")
        self.page = page
        self.extracted_points: List[Tuple[float, float]] = []

        self.page.title = "Bin Log Viewer & Map"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 10

        self.status_text = ft.Text(value="Please select a Bin file to process...", size=14, italic=True)
        self.progress_bar = ft.ProgressBar(width=200, visible=False)
        self.file_picker = ft.FilePicker()
        self.upload_btn = ft.Button(
            content=ft.Text("Select BIN File"), icon="folder", on_click=self.on_select_file_click
        )
        self.map_control = ftm.Map(
            expand=True,
            initial_center=ftm.MapLatitudeLongitude(latitude=31.7683, longitude=35.2137),
            initial_zoom=9,
            layers=[ftm.TileLayer(url_template=TILE_URL)],
        )

        sidebar = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Bin Log Viewer", size=20, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    self.upload_btn,
                    ft.Divider(height=10, thickness=0, color="transparent"),
                    self.status_text,
                    self.progress_bar,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
            ),
            width=260,
            bgcolor="surfacevariant",
            padding=20,
            border_radius=10,
        )
        self.page.add(ft.Row(controls=[sidebar, ft.Container(content=self.map_control, expand=True)], expand=True))
        self.page.on_disconnect = self.on_disconnect
        logger.info("App layout built successfully")

    def on_disconnect(self, e: ft.ControlEvent) -> None:
        self.extracted_points.clear()

    def set_state(self, status: str, loading: bool = False, btn_disabled: bool = False) -> None:
        self.status_text.value = status
        self.progress_bar.value = None if loading else 0
        self.progress_bar.visible = loading
        self.upload_btn.disabled = btn_disabled
        self.page.update()

    def on_select_file_click(self, e: ft.ControlEvent) -> None:
        logger.info("Opening file selection dialog")
        self.page.run_task(self.pick_and_process_file)

    async def pick_and_process_file(self) -> None:
        files = await self.file_picker.pick_files(
            dialog_title="Select BIN Log File",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["bin"],
            allow_multiple=False,
        )
        if files:
            file_path = files[0].path
            logger.info("File selected: %s", os.path.basename(file_path))
            self.set_state(f'Loading "{os.path.basename(file_path)}", please wait...', loading=True, btn_disabled=True)
            await self.process_file(file_path)
        else:
            logger.info("File selection cancelled by user")
            self.set_state("No file selected.")

    async def process_file(self, file_path: str) -> None:
        logger.info("Starting file processing: %s", file_path)
        try:
            self.extracted_points = await asyncio.to_thread(LogParser.extract_gps_coordinates, file_path)
            logger.info("File parsed successfully, %d points extracted", len(self.extracted_points))
            self.update_map()

        except Exception as ex:
            logger.error("Error processing file %s: %s", file_path, ex)
            self.set_state(f"Error: {ex}")

        finally:
            logger.info("Cleaning up after processing task.")
            self.progress_bar.visible = False
            self.upload_btn.disabled = False
            self.page.update()

    def make_marker(self, lat: float, lng: float, color: str) -> ftm.Marker:
        return ftm.Marker(
            coordinates=ftm.MapLatitudeLongitude(latitude=lat, longitude=lng),
            content=ft.Container(
                width=12, height=12, bgcolor=color, shape=ft.BoxShape.CIRCLE, border=ft.Border.all(1, "white")
            ),
        )

    def update_map(self) -> None:
        logger.info("Updating map display")
        if not self.extracted_points:
            logger.warning("No valid GPS points found in log")
            self.set_state("No valid GPS points found in log.")
            return

        sampled_points = self.extracted_points[::10]

        coords = [ftm.MapLatitudeLongitude(latitude=lat, longitude=lng) for lat, lng in sampled_points]

        self.map_control.layers = [
            self.map_control.layers[0],
            ftm.PolylineLayer(polylines=[ftm.PolylineMarker(coordinates=coords, color="red", stroke_width=4)]),
            ftm.MarkerLayer(
                markers=[
                    self.make_marker(*self.extracted_points[0], "green"),
                    self.make_marker(*self.extracted_points[-1], "blue"),
                ]
            ),
        ]

        start = self.extracted_points[0]
        self.page.run_task(self.move_to_start, start)

        self.set_state(
            f"Loaded {len(self.extracted_points)} points. "
            f"Displayed {len(sampled_points)} points (1:10 downsampling)."
        )
        self.map_control.update()
        logger.info("Map updated with %d downsampled coordinates", len(sampled_points))

    async def move_to_start(self, start: Tuple[float, float]) -> None:
        await self.map_control.move_to(
            destination=ftm.MapLatitudeLongitude(latitude=start[0], longitude=start[1]), zoom=12
        )


def main(page: ft.Page) -> None:
    BinLogViewerApp(page)


if __name__ == "__main__":
    ft.run(main)
