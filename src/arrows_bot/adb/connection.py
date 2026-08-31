import socket
from arrows_bot import config

def get_socket() -> socket.socket:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5.0)
    s.connect((config.ADB_HOST, config.ADB_PORT))
    return s

def _adb_command(cmd: str) -> bytes:
    length = f"{len(cmd):04x}"
    return f"{length}{cmd}".encode("utf-8")

def run_shell(command: str) -> str:
    s = get_socket()
    target = f"host:transport:{config.DEVICE_SERIAL}" if config.DEVICE_SERIAL else "host:transport-any"
    
    s.sendall(_adb_command(target))
    if s.recv(4).decode("utf-8") != "OKAY":
        s.close()
        raise RuntimeError("ADB cihaz hedefleme başarısız.")

    s.sendall(_adb_command(f"shell:{command}"))
    if s.recv(4).decode("utf-8") != "OKAY":
        s.close()
        return ""
    
    output = []
    while True:
        chunk = s.recv(4096)
        if not chunk: break
        output.append(chunk)
    s.close()
    return b"".join(output).decode("utf-8", errors="ignore")

def screencap() -> bytes:
    s = get_socket()
    target = f"host:transport:{config.DEVICE_SERIAL}" if config.DEVICE_SERIAL else "host:transport-any"
    s.sendall(_adb_command(target))
    s.recv(4)
    s.sendall(_adb_command("exec:screencap -p"))
    s.recv(4)
    data = []
    while True:
        chunk = s.recv(16384)
        if not chunk: break
        data.append(chunk)
    s.close()
    return b"".join(data)