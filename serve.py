import uvicorn
import sys
import os

if __name__ == "__main__":
    print("Starting SupportIQ Backend server on http://127.0.0.1:8000 ...")
    uvicorn.run(
        "backend.app.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
        access_log=True,
    )
