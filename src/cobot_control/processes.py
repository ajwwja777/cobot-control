"""Linux process identity; the start clock prevents PID reuse mistakes."""
from pathlib import Path

def process_identity(pid):
    try:
        raw = Path(f"/proc/{int(pid)}/stat").read_text()
        fields = raw[raw.rfind(")") + 2:].split()
        return int(fields[19]) if fields[0] != "Z" else None
    except (OSError, ValueError, IndexError):
        return None
