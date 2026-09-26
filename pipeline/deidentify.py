"""作者雜湊。與去識別語料使用同一套 salt 與 hid。

salt 只讀 D:\\hf_cache\\deid_salt.txt，不在這裡產生新 salt。
"""
import hashlib
from pathlib import Path

SALT_PATH = Path(r"D:\hf_cache\deid_salt.txt")


def load_salt() -> str:
    if not SALT_PATH.exists():
        raise FileNotFoundError(f"缺少去識別 salt：{SALT_PATH}")
    salt = SALT_PATH.read_text(encoding="utf-8").strip()
    if not salt:
        raise RuntimeError(f"去識別 salt 是空的：{SALT_PATH}")
    return salt


def hid(salt: str, source: str, value: str) -> str:
    raw = f"{salt}{source}{value if value is not None else ''}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:12]
