"""국토부 실거래가 API에서 서울 아파트 전월세 거래를 모아 site/data/*.json 으로 저장.

- 구별 파일 하나씩: site/data/<구코드>.json
- 각 거래에 first_seen(처음 수집된 날짜)을 붙여서 웹앱이 '새로 등록된 거래'를 표시
- GitHub Actions가 매일 실행 (로컬에서도 실행 가능)
"""
import json
import os
import sys
import time
import tomllib
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
from molit import fetch_month      # noqa: E402
from regions import resolve_gu     # noqa: E402

ROOT = Path(__file__).parent
DATA = ROOT / "site" / "data"
KST = timezone(timedelta(hours=9))
COLS = ["key", "first_seen", "date", "dong", "apt", "jibun", "area", "floor", "build_year",
        "deposit", "monthly_rent", "contract_type", "contract_term", "pre_deposit", "pre_monthly_rent"]


def api_key():
    key = os.environ.get("MOLIT_API_KEY")
    local = ROOT / "local.toml"
    if not key and local.exists():
        key = tomllib.loads(local.read_text(encoding="utf-8")).get("molit_api_key")
    if not key:
        raise SystemExit("API 키가 없습니다. MOLIT_API_KEY 환경변수나 local.toml 을 설정하세요.")
    return key


def recent_months(today, n):
    y, m, out = today.year, today.month, []
    for _ in range(n):
        out.append(f"{y}{m:02d}")
        y, m = (y - 1, 12) if m == 1 else (y, m - 1)
    return out


def load(path):
    if not path.exists():
        return None
    obj = json.loads(path.read_text(encoding="utf-8"))
    return {r[0]: dict(zip(obj["cols"], r)) for r in obj["rows"]}


def save(path, rows):
    rows.sort(key=lambda r: (r["date"], r["key"]), reverse=True)
    obj = {"cols": COLS, "rows": [[r.get(c) for c in COLS] for r in rows]}
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


TREND_COLS = ["apt_id", "ym", "area", "trade", "n", "deposit", "monthly_rent"]


def _median(xs):
    s = sorted(xs)
    m = len(s) // 2
    return s[m] if len(s) % 2 else round((s[m - 1] + s[m]) / 2)


def aggregate(deals, ym):
    """한 달치 거래 → 단지·전용면적(㎡ 반올림)·구분별 건수와 중앙값."""
    groups = {}
    for d in deals:
        if d["area"] is None or d["deposit"] is None:
            continue
        k = (f"{d['dong']}|{d['apt']}|{d['jibun']}", round(d["area"]), d["trade"])
        groups.setdefault(k, []).append(d)
    return [[apt, ym, area, trade, len(g), _median([x["deposit"] for x in g]),
             _median([x["monthly_rent"] for x in g])]
            for (apt, area, trade), g in sorted(groups.items())]


def update_trend(key, code, fresh_by_month, trend_months):
    """단지별 월간 시세. 최근 몇 달은 매번 다시 계산하고, 그 이전 달은 한 번만 받아서 보관."""
    path = DATA / "trend" / f"{code}.json"
    path.parent.mkdir(exist_ok=True)
    obj = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"rows": [], "done": []}
    keep = set(trend_months)
    rows = {ym: [] for ym in trend_months}
    for r in obj["rows"]:
        if r[1] in keep and r[1] not in fresh_by_month:
            rows[r[1]].append(r)
    done = {ym for ym in obj["done"] if ym in keep}
    for ym, deals in fresh_by_month.items():
        rows[ym] = aggregate(deals, ym)
        done.add(ym)
    for ym in trend_months:
        if ym not in done:  # 과거 달 백필 (처음 한 번만)
            rows[ym] = aggregate(fetch_month(key, code, ym), ym)
            done.add(ym)
            time.sleep(0.2)
    out = {"cols": TREND_COLS, "done": sorted(done),
           "rows": [r for ym in sorted(rows) for r in rows[ym]]}
    path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def collect_gu(key, gu, code, months, today_str, trend_months):
    path = DATA / f"{code}.json"
    old = load(path)
    fetched, by_month = [], {}
    for ym in months:
        by_month[ym] = fetch_month(key, code, ym)
        fetched += by_month[ym]
        time.sleep(0.2)
    update_trend(key, code, by_month, trend_months)
    # 완전히 같은 거래(같은 층·금액·날짜)가 여러 건이면 #2, #3 … 으로 구분
    seen = Counter()
    rows = []
    for d in fetched:
        seen[d["key"]] += 1
        k = d["key"] if seen[d["key"]] == 1 else f"{d['key']}#{seen[d['key']]}"
        prev = old.get(k) if old is not None else None
        # 처음 수집하는 구는 기준점이라 first_seen을 비워 둠 (NEW 아님)
        first = prev["first_seen"] if prev else ("" if old is None else today_str)
        rows.append({**d, "key": k, "first_seen": first})
    save(path, rows)
    return len(rows), sum(1 for r in rows if r["first_seen"] == today_str)


def main():
    cfg = tomllib.loads((ROOT / "config.toml").read_text(encoding="utf-8"))
    gus = resolve_gu(cfg.get("collect", {}).get("gu", []))
    n_months = int(cfg.get("collect", {}).get("months", 3))
    now = datetime.now(KST)
    today_str = now.date().isoformat()
    months = recent_months(now.date(), n_months)
    trend_months = recent_months(now.date(), int(cfg.get("collect", {}).get("trend_months", 24)))
    key = api_key()
    DATA.mkdir(parents=True, exist_ok=True)

    meta_path = DATA / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    gu_meta, failed = meta.get("gu", {}), []
    for gu, code in gus:
        try:
            total, new = collect_gu(key, gu, code, months, today_str, trend_months)
            gu_meta[code] = {"name": gu, "count": total, "new_today": new}
            print(f"{gu:5} {total:6}건  신규 {new}")
        except Exception as e:  # 한 구가 실패해도 나머지는 계속
            failed.append(gu)
            print(f"{gu:5} 실패: {e}", file=sys.stderr)

    meta.update({"updated_at": now.isoformat(timespec="minutes"), "months": months,
                 "trend_months": trend_months, "gu": gu_meta, "failed": failed})
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    if len(failed) == len(gus):
        raise SystemExit("모든 구에서 수집 실패")


if __name__ == "__main__":
    main()
