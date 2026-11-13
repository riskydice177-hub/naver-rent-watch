"""국토교통부 아파트 전월세 실거래가 API (공공데이터포털)."""
import time
import xml.etree.ElementTree as ET

import requests

ENDPOINT = "https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent"


def _num(s):
    s = (s or "").replace(",", "").strip()
    try:
        return float(s) if "." in s else int(s)
    except ValueError:
        return None


def _text(item, tag):
    el = item.find(tag)
    return el.text.strip() if el is not None and el.text else ""


def _get(params, tries=4):
    """공공데이터 API가 가끔 느리거나 5xx를 주므로 간격을 늘려가며 재시도."""
    for i in range(tries):
        try:
            r = requests.get(ENDPOINT, params=params, timeout=60)
            if r.status_code < 500:
                r.raise_for_status()
                return r
        except (requests.ConnectionError, requests.Timeout):
            if i == tries - 1:
                raise
        time.sleep(5 * (i + 1))
    r.raise_for_status()
    return r


def fetch_month(api_key, lawd_cd, yyyymm, rows=1000):
    """한 구, 한 달치 전월세 거래를 모두 가져온다."""
    out, page = [], 1
    while True:
        r = _get({"serviceKey": api_key, "LAWD_CD": lawd_cd, "DEAL_YMD": yyyymm,
                  "pageNo": page, "numOfRows": rows})
        root = ET.fromstring(r.content)
        code = root.findtext(".//resultCode") or ""
        if code not in ("00", "000"):
            msg = root.findtext(".//resultMsg") or r.text[:300]
            raise RuntimeError(f"API 오류 ({code}): {msg}")
        items = root.findall(".//item")
        for it in items:
            out.append(_parse(it, lawd_cd))
        total = int(root.findtext(".//totalCount") or 0)
        if page * rows >= total or not items:
            return out
        page += 1
        time.sleep(0.2)


def _parse(it, lawd_cd):
    y, m, d = _text(it, "dealYear"), _text(it, "dealMonth"), _text(it, "dealDay")
    rent = _num(_text(it, "monthlyRent")) or 0
    deal = {
        "lawd_cd": lawd_cd,
        "dong": _text(it, "umdNm"),
        "apt": _text(it, "aptNm"),
        "jibun": _text(it, "jibun"),
        "area": _num(_text(it, "excluUseAr")),
        "floor": _num(_text(it, "floor")),
        "build_year": _num(_text(it, "buildYear")),
        "deposit": _num(_text(it, "deposit")),        # 만원
        "monthly_rent": rent,                          # 만원
        "trade": "월세" if rent else "전세",
        "date": f"{y}-{int(m):02d}-{int(d):02d}" if y and m and d else "",
        "contract_type": _text(it, "contractType"),    # 신규/갱신
        "contract_term": _text(it, "contractTerm"),
        "pre_deposit": _num(_text(it, "preDeposit")),
        "pre_monthly_rent": _num(_text(it, "preMonthlyRent")),
    }
    deal["key"] = "|".join(str(deal[k]) for k in (
        "lawd_cd", "dong", "apt", "jibun", "area", "floor", "deposit", "monthly_rent", "date"))
    return deal
