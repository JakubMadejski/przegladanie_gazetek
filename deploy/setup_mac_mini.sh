#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
UVICORN_BIN="$PROJECT_DIR/.venv/bin/uvicorn"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

mkdir -p "$LAUNCH_AGENTS_DIR"

echo "=== Konfiguracja usług GazetkoAgent na macOS (Mac mini M2) ==="
echo "Katalog projektu: $PROJECT_DIR"

# 1. Usługa API (FastAPI na porcie 8000)
API_PLIST="$LAUNCH_AGENTS_DIR/com.gazetkoagent.api.plist"
cat <<EOF > "$API_PLIST"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.gazetkoagent.api</string>
    <key>ProgramArguments</key>
    <array>
        <string>$UVICORN_BIN</string>
        <string>api.app:app</string>
        <string>--host</string>
        <string>0.0.0.0</string>
        <string>--port</string>
        <string>8000</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/logs/api_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/logs/api_stderr.log</string>
</dict>
</plist>
EOF

# 2. Usługa Scheduler (Synchronizacja o 6:00 rano)
SCHEDULER_PLIST="$LAUNCH_AGENTS_DIR/com.gazetkoagent.scheduler.plist"
cat <<EOF > "$SCHEDULER_PLIST"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.gazetkoagent.scheduler</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_BIN</string>
        <string>scheduler.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/logs/scheduler_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/logs/scheduler_stderr.log</string>
</dict>
</plist>
EOF

mkdir -p "$PROJECT_DIR/logs"

echo "Usługi launchd zostały utworzone:"
echo "1. $API_PLIST"
echo "2. $SCHEDULER_PLIST"
echo ""
echo "Aby je aktywować, wykonaj w terminalu:"
echo "  launchctl load $API_PLIST"
echo "  launchctl load $SCHEDULER_PLIST"
echo ""
echo "API będzie dostępne pod adresem: http://localhost:8000"
echo "=== Gotowe! ==="
