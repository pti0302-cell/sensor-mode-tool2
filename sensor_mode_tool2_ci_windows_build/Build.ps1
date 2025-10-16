
# Build.ps1 - Local Windows build helper
param(
    [string]$PythonVersion = "3.10"
)
Write-Host "Creating venv..."
python -m venv .venv
.\.venv\Scripts\pip install --upgrade pip
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\pip install pyinstaller
Write-Host "Building..."
.\.venv\Scripts\pyinstaller --clean --onefile --windowed sensor_mode_tool2.py
Write-Host "Done. Check dist\sensor_mode_tool2.exe"
