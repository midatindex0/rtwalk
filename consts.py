MAX_FILE_SIZE = 32 * 1024 * 1024  # 32mb
CDN_ROUTE = "/cdn"
ORIGINS = [
    "http://localhost:5173",  # Local frontend
    "https://dreamh.vercel.app",
]
MAX_SESSIONS = 5
RTE_URL = "ws://localhost:3758/rte/v1/"
VC_URL = "ws://localhost:3001/ws"
