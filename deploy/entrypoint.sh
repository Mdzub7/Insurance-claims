
#!/bin/sh
set -euo pipefail

# Start backend using uvicorn
nohup uvicorn app.backend.main:app --host 0.0.0.0 --port 8001 &
# Start frontend server
cd frontend
python3 -m http.server 8000
