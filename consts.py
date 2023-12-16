MAX_FILE_SIZE = 32 * 1024 * 1024  # 32mb
CDN_ROUTE = "/cdn"
ORIGINS = [
    "http://localhost:8000",  # This server
    "http://localhost:5173",  # Relay server
]
MAX_SESSIONS = 5
