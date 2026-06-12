import json
from pathlib import Path
from typing import Any

DATA_DIR = Path.home() / ".sunlog"
DATA_FILE = DATA_DIR / "data.json"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_entries() -> list[dict[str, Any]]:
    _ensure_data_dir()
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_entries(entries: list[dict[str, Any]]) -> None:
    _ensure_data_dir()
    with open(DATA_FILE, "w") as f:
        json.dump(entries, f, indent=2, default=str)

def add_entry(entry: dict[str, Any]) -> None:
    entries = load_entries()
    entries.append(entry)
    save_entries(entries)

def delete_entry(entry_id: int) -> bool:
    entries = load_entries()
    if entry_id < 1 or entry_id > len(entries):
        return False
    entries.pop(entry_id - 1)
    save_entries(entries)
    return True
