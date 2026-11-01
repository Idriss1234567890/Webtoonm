"""Moteur de reference (hors ligne) : applique un source.json a du HTML.

Il sert a tester les selecteurs et de specification executable pour
l'application Android (qui reimplementera la meme logique en Kotlin/Jsoup).
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup


def load_source(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def extract(node, spec: dict, base_url: str = ""):
    """Extrait une valeur (ou une liste si spec['multiple'])."""
    if spec.get("multiple"):
        return [v for v in (_one(n, spec, base_url) for n in node.select(spec["selector"])) if v]
    found = node.select_one(spec["selector"])
    if found is None:
        fb = spec.get("fallback")
        if fb:
            return extract(node, fb, base_url)
        return None
    return _one(found, spec, base_url)


def _one(el, spec: dict, base_url: str):
    attr = spec.get("attr", "text")
    attrs = attr if isinstance(attr, list) else [attr]
    for a in attrs:
        if a == "text":
            value = _clean(el.get_text(" "))
        else:
            value = (el.get(a) or "").strip()
        if value:
            if a in ("href", "src", "data-src", "data-lazy-src") and base_url:
                value = urljoin(base_url, value)
            return value
    return None


def apply_cover_transform(url: str | None, rules: list[dict]) -> str | None:
    if not url:
        return url
    for r in rules:
        url = re.sub(r["regex"], r["replace"], url)
    return url


def parse_listing(html: str, section: dict, src: dict) -> dict:
    d = soup(html)
    base = src["baseUrl"]
    items = []
    for node in d.select(section["list"]):
        url = extract(node, section["item"]["url"], base)
        title = extract(node, section["item"]["title"], base)
        if not url or not title:
            continue
        cover = apply_cover_transform(
            extract(node, section["item"]["cover"], base), src.get("coverTransform", [])
        )
        items.append({"url": url, "title": title, "cover": cover})
    has_next = d.select_one(section["nextPage"]) is not None
    return {"items": items, "hasNext": has_next}


def parse_details(html: str, src: dict) -> dict:
    d = soup(html)
    s = src["details"]
    base = src["baseUrl"]
    out = {}
    for key in ("title", "cover", "description", "genres", "author", "artist"):
        if key in s:
            out[key] = extract(d, s[key], base)
    out["cover"] = apply_cover_transform(out.get("cover"), src.get("coverTransform", []))
    raw_status = (extract(d, s["status"], base) or "").lower()
    out["status"] = s["statusMap"].get(raw_status, "unknown")
    out["rawStatus"] = raw_status
    ch = src["chapters"]
    out["mangaId"] = extract(d, ch["mangaId"], base)
    return out


def parse_date(text: str | None, ch: dict, now: datetime | None = None) -> int | None:
    """Retourne un timestamp (ms) ou None."""
    if not text:
        return None
    now = now or datetime.now(timezone.utc)
    text = _clean(text)
    m = re.match(r"^(\S+)\s+(\d{1,2}),\s*(\d{4})$", text)
    if m and m.group(1) in ch["arabicMonths"]:
        dt = datetime(int(m.group(3)), ch["arabicMonths"][m.group(1)], int(m.group(2)), tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    m = re.match(ch["relativeDatePattern"], text)
    if m:
        n = int(m.group(1)) if m.group(1) else None
        unit = m.group(2)
        table = {
            "دقيقة": ("minutes", 1), "دقيقتين": ("minutes", 2), "دقائق": ("minutes", None),
            "ساعة": ("hours", 1), "ساعتين": ("hours", 2), "ساعات": ("hours", None),
            "يوم": ("days", 1), "يومين": ("days", 2), "أيام": ("days", None),
            "اسبوع": ("weeks", 1), "أسبوع": ("weeks", 1), "أسبوعين": ("weeks", 2), "أسابيع": ("weeks", None),
            "شهر": ("days", 30), "شهرين": ("days", 60), "أشهر": ("days", None),
        }
        kind, fixed = table[unit]
        amount = n if n is not None else fixed
        if amount is None:
            return None
        if unit == "أشهر":
            amount *= 30
        return int((now - timedelta(**{kind: amount})).timestamp() * 1000)
    return None


def parse_chapters(html: str, src: dict, now: datetime | None = None) -> list[dict]:
    d = soup(html)
    ch = src["chapters"]
    base = src["baseUrl"]
    out = []
    for node in d.select(ch["list"]):
        url = extract(node, ch["item"]["url"], base)
        name = extract(node, ch["item"]["name"], base)
        if not url or not name:
            continue
        date_text = extract(node, ch["item"]["date"], base) if "date" in ch["item"] else None
        date_ms = parse_date(date_text, ch, now)
        if date_ms is None and "dateTitle" in ch["item"]:
            date_ms = parse_date(extract(node, ch["item"]["dateTitle"], base), ch, now)
        m = re.search(ch["numberFromUrl"], url)
        out.append({
            "url": url,
            "name": name,
            "number": m.group(1).replace("-", ".") if m else None,
            "date": date_ms,
        })
    return out


def parse_pages(html: str, src: dict) -> list[str]:
    d = soup(html)
    p = src["pages"]
    base = src["baseUrl"]
    urls = []
    for img in d.select(p["list"]):
        v = _one(img, {"attr": p["image"]["attr"]}, base)
        if v:
            urls.append(v)
    return urls


def build_url(src: dict, template: str, **kw) -> str:
    url = template
    for k, v in kw.items():
        url = url.replace("{" + k + "}", str(v))
    return urljoin(src["baseUrl"] + "/", url)
