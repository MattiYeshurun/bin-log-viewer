from tkinter import Tk, filedialog
from typing import List, Tuple

import flet as ft
import flet_map as ftm

from bin_parser.log_parser import LogParser


def main(page: ft.Page) -> None:
    page.title = "Bin Log Viewer & Map"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 10

    extracted_points: List[Tuple[float, float]] = []
    map_control = ftm.Map(
        expand=True,
        initial_center=ftm.MapLatitudeLongitude(latitude=31.7683, longitude=35.2137),
        initial_zoom=9,
        layers=[
            ftm.TileLayer(
                url_template="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}.png",
            ),
        ],
    )

    status_text = ft.Text(value="Please select a Bin file to process...", size=14, italic=True)
    progress_bar = ft.ProgressBar(width=200, visible=False)

    def update_map() -> None:
        if not extracted_points:
            status_text.value = "No valid GPS points found in log."
            progress_bar.visible = False
            page.update()
            return

        route_coordinates = []
        lats = []
        lngs = []
        for lat, lng in extracted_points:
            route_coordinates.append(ftm.MapLatitudeLongitude(latitude=lat, longitude=lng))
            lats.append(lat)
            lngs.append(lng)

        if len(map_control.layers) > 1:
            map_control.layers = [map_control.layers[0]]

        route_line = ftm.PolylineLayer(
            polylines=[
                ftm.PolylineMarker(
                    coordinates=route_coordinates,
                    color="red",
                    stroke_width=4,
                )
            ]
        )
        map_control.layers.append(route_line)

        start_pt = extracted_points[0]
        end_pt = extracted_points[-1]

        markers_layer = ftm.MarkerLayer(
            markers=[
                ftm.Marker(
                    coordinates=ftm.MapLatitudeLongitude(latitude=start_pt[0], longitude=start_pt[1]),
                    content=ft.Container(
                        width=12, height=12, bgcolor="green", shape=ft.BoxShape.CIRCLE, border=ft.Border.all(1, "white")
                    ),
                ),
                ftm.Marker(
                    coordinates=ftm.MapLatitudeLongitude(latitude=end_pt[0], longitude=end_pt[1]),
                    content=ft.Container(
                        width=12, height=12, bgcolor="blue", shape=ft.BoxShape.CIRCLE, border=ft.Border.all(1, "white")
                    ),
                ),
            ]
        )
        map_control.layers.append(markers_layer)

        avg_lat = sum(lats) / len(lats)
        avg_lng = sum(lngs) / len(lngs)

        target_center = ftm.MapLatitudeLongitude(latitude=avg_lat, longitude=avg_lng)
        page.run_task(map_control.move_to, target_center, 12)

        progress_bar.visible = False
        status_text.value = f"Extracted {len(extracted_points)} valid coordinates. Whole route displayed."
        map_control.update()
        page.update()

    def process_file(file_path: str) -> None:
        nonlocal extracted_points
        progress_bar.visible = True
        status_text.value = "Processing file, please wait..."
        page.update()

        try:
            extracted_points = LogParser.extract_gps_coordinates(file_path)
            update_map()
        except Exception as ex:
            progress_bar.visible = False
            status_text.value = f"Error: {str(ex)}"
            page.update()

    def select_file_click(e) -> None:
        root = Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        file_path = filedialog.askopenfilename(
            title="Select BIN Log File", filetypes=[("BIN files", "*.bin"), ("All files", "*.*")]
        )
        root.destroy()

        if file_path:
            process_file(file_path)
        else:
            status_text.value = "No file selected."
            page.update()

    upload_btn = ft.Button(content=ft.Text("Select BIN File"), icon="folder", on_click=select_file_click)

    sidebar = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Bin Log Viewer", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                upload_btn,
                ft.Divider(height=10, thickness=0, color="transparent"),
                status_text,
                progress_bar,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
        ),
        width=260,
        bgcolor="surfacevariant",
        padding=20,
        border_radius=10,
    )

    page.add(ft.Row(controls=[sidebar, ft.Container(content=map_control, expand=True)], expand=True))


if __name__ == "__main__":
    ft.run(main)
