import os

ADB_HOST = os.getenv("ADB_HOST", "host.docker.internal")
ADB_PORT = int(os.getenv("ADB_PORT", 5037))
DEVICE_SERIAL = os.getenv("DEVICE_SERIAL", "")

# Yön vektörleri
DIR_VECTORS = {
    'UP': (0, -1),
    'DOWN': (0, 1),
    'LEFT': (-1, 0),
    'RIGHT': (1, 0)
}