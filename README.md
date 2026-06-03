# Bin Log Viewer & GPS Track Extractor

Python application for extracting GPS coordinates from MAVLink `.bin` telemetry logs and visualizing the resulting flight path on an interactive map.

The project is designed for developers and operators who need a lightweight desktop viewer for GPS tracks inside MAVLink binary logs, with an easy file picker and a simple `flet` map UI.

---

## 📁 Current Project Structure

```text
bin-log-viewer_24.05.26/
├── data/                                   # Optional sample logs or test data
├── src/                                    # Application source code
│   ├── buisness_logic/
│   │   ├── bin_parser/
│   │   │   ├── __init__.py
│   │   │   └── log_parser.py               # GPS extraction logic from MAVLink logs
│   │   └── gui/
│   │       ├── __init__.py
│   │       └── app_layout.py                # Flet GUI and map layout
│   └── main.py                             # App entrypoint
├── tests/
│   └── test_bin_parser.py                  # Unit tests for parser behavior
├── pytest.ini                              # Pytest configuration
├── requirements.txt                        # Python dependencies
└── README.md                               # Project documentation
```

---

## 🚀 What This App Does

This application performs three main steps:

1. `LogParser.extract_gps_coordinates()` opens a MAVLink `.bin` log using `pymavlink`
2. It scans all incoming `GPS` messages and keeps only valid coordinates
3. It displays the GPS track on a `flet_map` interactive map inside a desktop UI

### What is considered a valid GPS point?

- `message.U == 1`
- `message.Lat` is not `None` and not `0.0`
- `message.Lng` is not `None` and not `0.0`
- Latitude and longitude are rounded to 6 decimal places

### User-facing behavior

- A native file dialog appears when clicking **Select BIN File**
- The app parses the selected `.bin` log in a background task
- The map displays a red polyline representing the track
- The first point is shown with a green marker, the last point with a blue marker
- If the log contains no valid GPS points, the app shows a friendly status message

---

## 🧩 Architecture Overview

### `src/main.py`

- Sets up logging configuration
- Launches the `flet` runtime
- Calls `gui_main()` from `app_layout.py`

### `src/buisness_logic/gui/app_layout.py`

- Builds the `flet` page layout with sidebar, status text, progress bar, and map
- Uses `Tkinter` to open a native file picker on Windows
- Processes the selected file asynchronously with `asyncio.to_thread`
- Updates the map using `flet_map` layers:
  - `TileLayer` for the base map
  - `PolylineLayer` for the GPS path
  - `MarkerLayer` for start/end markers

### `src/buisness_logic/bin_parser/log_parser.py`

- Opens the `.bin` log using `pymavlink.mavutil.mavlink_connection()`
- Reads messages using `recv_match(type="GPS", blocking=False)` in a loop
- Validates and rounds coordinates
- Logs errors and continues parsing even when a single message is corrupt

### `tests/test_bin_parser.py`

- Mocks `pymavlink` connection behavior to avoid real file dependencies
- Verifies:
  - file open failures are handled safely
  - empty logs return an empty list
  - invalid GPS messages are skipped
  - corrupted messages do not stop parsing
  - rounding, missing values, and type edge cases are handled correctly

---

## ⚙️ Installation

1. Open the repository root in a terminal.
2. Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
```

### Recommended tooling

The repository also includes developer tools in `requirements.txt` for formatting and static analysis:

- `black`
- `isort`
- `mypy`
- `pylint`
- `folium`

These packages are optional for running the app, but useful when improving or maintaining the code.

---

## ▶️ Run the App

Launch the GUI with:

```powershell
.venv\Scripts\python src/main.py
```

Once open:

- Click **Select BIN File**
- Choose a `.bin` MAVLink log
- Wait for the parser to finish
- View the extracted route on the map

---

## 🧪 Run Tests

Run the parser unit tests with:

```powershell
.venv\Scripts\python -m pytest
```

If you want to run only the parser tests:

```powershell
.venv\Scripts\python -m pytest tests/test_bin_parser.py
```

---

## 🛠️ Notes and Limitations

- The current parser only checks `GPS` message objects and a single flag `U == 1`.
- Invalid coordinates such as `0.0`, `None`, or missing attributes are skipped.
- The GUI down-samples the track to every 10th extracted point for display performance.
- The tile server is configured to use the ArcGIS world street map template.
- The app assumes a desktop environment with a native file dialog.

---

## 💡 How to Extend

Suggested improvements:

- Add duplicate coordinate filtering to remove consecutive identical points
- Support additional MAVLink GPS message types or fields
- Add an export feature for parsed GPS points to CSV or GeoJSON
- Add zoom controls, map layer selection, or track info display
- Add a command-line mode for batch processing without the GUI
