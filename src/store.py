"""이미 본 거래를 SQLite에 저장해서 '새로 올라온 것'만 골라낸다."""
import json
import sqlite3
from pathlib import Path


class Store:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS deals (key TEXT PRIMARY KEY, first_seen TEXT, data TEXT)")

    def is_empty(self):
        return self.db.execute("SELECT 1 FROM deals LIMIT 1").fetchone() is None

    def upsert(self, deals, run_ts):
        """처음 보는 거래만 저장하고 그 목록을 돌려준다."""
        new = []
        for d in deals:
            cur = self.db.execute(
                "INSERT OR IGNORE INTO deals VALUES (?, ?, ?)",
                (d["key"], run_ts, json.dumps(d, ensure_ascii=False)))
            if cur.rowcount:
                new.append(d)
        self.db.commit()
        return new

    def first_seen(self, keys):
        q = "SELECT key, first_seen FROM deals WHERE key IN (%s)"
        res = {}
        keys = list(keys)
        for i in range(0, len(keys), 500):
            chunk = keys[i:i + 500]
            res.update(self.db.execute(q % ",".join("?" * len(chunk)), chunk).fetchall())
        return res
