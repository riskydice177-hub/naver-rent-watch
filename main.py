"""서울 아파트 전월세 실거래 수집 → 새 거래 표시 → HTML 리포트 생성.

사용법:  .venv\\Scripts\\python.exe main.py
"""
import os
import sys
import time
import tomllib
import webbrowser
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
from molit import fetch_month          # noqa: E402
from regions import resolve_gu         # noqa: E402
from report import build               # noqa: E402
from store import Store                # noqa: E402

ROOT = Path(__file__).parent


def load_config():
    cfg = tomllib.loads((ROOT / "config.toml").read_text(encoding="utf-8"))
    local = ROOT / "local.toml"
    if local.exists():
        cfg.update(tomllib.loads(local.read_text(encoding="utf-8")))
    key = os.environ.get("MOLIT_API_KEY") or cfg.get("molit_api_key", "")
    if not key:
        raise SystemExit("API 키가 없습니다. local.toml에 molit_api_key = \"...\" 를 넣어주세요. (README 참고)")
    return cfg, key


def recent_months(n):
    y, m = date.today().year, date.today().month
    out = []
    for _ in range(n):
        out.append(f"{y}{m:02d}")
        y, m = (y - 1, 12) if m == 1 else (y, m - 1)
    return out


def passes(d, f, dongs):
    if dongs and d["dong"] not in dongs:
        return False
    if f.get("trade") and d["trade"] not in f["trade"]:
        return False
    checks = [("deposit_max", "deposit", lambda v, lim: v <= lim),
              ("monthly_rent_max", "monthly_rent", lambda v, lim: v <= lim),
              ("area_min", "area", lambda v, lim: v >= lim),
              ("area_max", "area", lambda v, lim: v <= lim),
              ("build_year_min", "build_year", lambda v, lim: v >= lim)]
    for opt, field, ok in checks:
        lim = f.get(opt) or 0
        if lim and (d[field] is None or not ok(d[field], lim)):
            return False
    if f.get("new_contracts_only") and d["contract_type"] == "갱신":
        return False
    return True


def main():
    cfg, key = load_config()
    gus = resolve_gu(cfg["regions"].get("gu", []))
    dongs = set(cfg["regions"].get("dong", []))
    months = int(cfg.get("molit", {}).get("months", 3))
    f = cfg.get("filters", {})

    store = Store(ROOT / "data" / "deals.db")
    first_run = store.is_empty()
    run_ts = datetime.now().isoformat(timespec="seconds")

    deals = []
    for gu, code in gus:
        for ym in recent_months(months):
            print(f"  {gu} {ym} ...", end=" ", flush=True)
            rows = fetch_month(key, code, ym)
            for r in rows:
                r["gu"] = gu
            deals += rows
            print(len(rows))
            time.sleep(0.2)

    new_keys = {d["key"] for d in store.upsert(deals, run_ts)}
    picked = [d for d in deals if passes(d, f, dongs)]
    for d in picked:
        d["is_new"] = (not first_run) and d["key"] in new_keys

    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    page = build(picked, date.today().isoformat(), months)
    (out / f"{date.today().isoformat()}.html").write_text(page, encoding="utf-8")
    latest = out / "latest.html"
    latest.write_text(page, encoding="utf-8")

    n_new = sum(d["is_new"] for d in picked)
    print(f"\n조건에 맞는 거래 {len(picked)}건, 새로 등록 {n_new}건"
          + (" (첫 실행이라 NEW 표시는 다음 실행부터)" if first_run else ""))
    print(f"리포트: {latest}")
    if "--open" in sys.argv:
        webbrowser.open(latest.as_uri())


if __name__ == "__main__":
    main()
