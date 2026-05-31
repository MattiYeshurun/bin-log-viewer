# MAVLink Binary Log GPS Parser & Map Viewer

A highly optimized Python application designed to extract, filter, and visualize GPS coordinate paths from MAVLink binary (`.bin`) flight logs. It features a fast binary log parser and a beautiful interactive map viewer.

---

## 📂 Project Structure

The project is structured according to professional Python packaging best practices:

```text
Overlap_task_01_20.05.26/
├── data/
│   └── log_file_test_01.bin      # MAVLink binary flight logs
├── src/                          # Application source code
│   ├── bin_parser/
│   │   ├── __init__.py           # Package marker
│   │   └── log_parser.py         # MAVLink binary file parser
│   ├── gui/
│   │   ├── __init__.py           # Package marker
│   │   └── app_layout.py         # Interactive Flet map layout
│   └── main.py                   # Main application entrypoint
├── tests/
│   └── test_bin_parser.py        # Robust unit & edge-case test suite
├── pytest.ini                    # Pytest configuration (verbose output)
├── requirements.txt              # Project dependencies
└── README.md                     # Project documentation
```

---

## ⚡ Key Features & Optimizations

- **High Performance Scanning**: Optimized file scanner parses large binary files (e.g., **300 MB logs**) and processes over **64,000 GPS messages in less than 5 seconds** (down from 20s by eliminating console I/O bottlenecks).
- **Fault-Tolerant Parsing**: Parser is resilient against packet corruption. Any isolated message error is logged, and the scanning safely continues parsing the remaining data.
- **Smart GPS Filtering**: Removes consecutive duplicate coordinates automatically (reducing redundant logs by over 5% when stationary or hovering).
- **Interactive Map Visualizer**: Renders the complete flight path trajectory on a map using a Flet desktop wrapper.

---

## 🛠️ Installation & Setup

1. **Clone or Open the Workspace**  
   Open the project folder in your terminal:
   ```bash
   cd Overlap_task_01_20.05.26
   ```

2. **Set Up a Virtual Environment**  
   Create and activate a local Python virtual environment:
   ```powershell
   # Create virtual environment
   python -m venv .venv

   # Activate virtual environment (Windows PowerShell)
   .venv\Scripts\Activate.ps1
   ```

3. **Install Dependencies**  
   Install all required libraries including `pymavlink` and `flet`:
   ```powershell
   pip install -r requirements.txt
   ```

---

## 🚀 Running the Application

To start the **Bin Log Viewer & Map GUI**, simply execute the main file:

```powershell
.venv\Scripts\python src/main.py
```

### GUI Features:
- Click **"Select BIN File"** to open a file dialogue.
- Load any MAVLink `.bin` file.
- The map automatically centers, zooms, and highlights the **Start point (Green)**, **End point (Blue)**, and the **Flight Route (Red line)**.

---

## 🧪 Running Unit Tests

We have implemented a robust, comprehensive unit test suite covering extreme edge cases, parsing failures, and corrupted packets.

To run the tests with detailed verbose outputs showing all validation print messages:

```powershell
.venv\Scripts\python -m pytest
```

### Edge Cases Covered:
- **File Access Failure**: Gracefully returns empty list if log cannot be loaded.
- **Empty Logs**: Safely handles logs lacking GPS coordinates.
- **Mixed Validation**: Rejects invalid states (`U != 1`), `0.0` zero coordinates, or `None` values.
- **Robust Failure Resilience**: Correctly skips corrupt packets and parses surrounding messages.
- **Boundary & Rounding**: Checks coordinate rounding behavior, negative values, and type variance (e.g., float vs string for status).
