"""Tests hors ligne de sources/mangalek/source.json sur les fichiers de tests/fixtures.

Lancer :  python3 -I tools/test_source.py
Les tests de chapitres et de recherche ne tournent que si leur fixture existe
(voir tests/fixtures/README.md) : aucune donnee n'est inventee.
"""
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import source_engine as eng  # noqa: E402

FIX = os.path.join(ROOT, "tests", "fixtures")
src = eng.load_source(os.path.join(ROOT, "sources", "mangalek", "source.json"))

passed = failed = skipped = 0


def read(name):
    p = os.path.join(FIX, name)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return f.read()


def check(label, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  OK   {label}")
    else:
        failed += 1
        print(f"  FAIL {label} {detail}")


def skip(label, why):
    global skipped
    skipped += 1
    print(f"  SKIP {label} ({why})")


print("[latest] liste + page suivante")
r = eng.parse_listing(read("latest_page1.html"), src["latest"], src)
check("30 mangas extraits", len(r["items"]) == 30, f"(obtenu {len(r['items'])})")
check("page suivante detectee", r["hasNext"] is True)
first = r["items"][0]
check("titre 1 = The Crown Prince That Sells Medicine", first["title"] == "The Crown Prince That Sells Medicine", first["title"])
check("url 1 absolue", first["url"] == "https://mangalik.net/manga/the-crown-prince-that-sells-medicine/", first["url"])
check("couverture sans suffixe -175x238",
      first["cover"] and "-175x238" not in first["cover"] and first["cover"].endswith(".jpg"), str(first["cover"]))
check("toutes les couvertures presentes", all(i["cover"] for i in r["items"]))
check("urls uniques", len({i["url"] for i in r["items"]}) == 30)
check("url page 2", eng.build_url(src, src["latest"]["url"], page=2) == "https://mangalik.net/page/2/")

print("[details] page d'un manga")
r = eng.parse_details(read("details.html"), src)
check("titre", r["title"] == "I Bought the Villains With Money", r["title"])
check("statut ongoing", r["status"] == "ongoing", r["rawStatus"])
check("4 genres", len(r["genres"]) == 4, str(r["genres"]))
check("description non vide", bool(r["description"]) and r["description"].startswith("[إذا شكّ"), str(r["description"])[:40])
check("couverture", bool(r["cover"]) and "-193x278" not in r["cover"], str(r["cover"]))
check("mangaId = 185972", r["mangaId"] == "185972", str(r["mangaId"]))
check("url ajax chapitres", eng.build_url(src, src["chapters"]["request"]["url"],
      mangaUrl="https://mangalik.net/manga/i-bought-the-villains-with-money/")
      == "https://mangalik.net/manga/i-bought-the-villains-with-money/ajax/chapters/")

print("[pages] images d'un chapitre")
urls = eng.parse_pages(read("chapter_pages.html"), src)
check("8 images", len(urls) == 8, f"(obtenu {len(urls)})")
check("ordre image-01 .. image-08",
      [u.rsplit("/", 1)[1] for u in urls] == [f"image-0{i}.jpg" for i in range(1, 9)])

print("[dates] formats arabes")
ch = src["chapters"]
now = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
ts = eng.parse_date("أكتوبر 24, 2026", ch, now)
check("date absolue", ts == int(datetime(2026, 10, 24, tzinfo=timezone.utc).timestamp() * 1000))
ts = eng.parse_date("3 ساعات ago", ch, now)
check("relative 3 ساعات", ts == int(datetime(2026, 11, 1, 7, 0, tzinfo=timezone.utc).timestamp() * 1000))
ts = eng.parse_date("ساعتين ago", ch, now)
check("relative ساعتين", ts == int(datetime(2026, 11, 1, 8, 0, tzinfo=timezone.utc).timestamp() * 1000))
ts = eng.parse_date("22 ساعة ago", ch, now)
check("relative 22 ساعة", ts == int(datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc).timestamp() * 1000))

print("[chapters] reponse AJAX")
html = read("chapters_ajax.html")
if html is None:
    skip("chapitres", "tests/fixtures/chapters_ajax.html absent")
else:
    chs = eng.parse_chapters(html, src, now)
    check("au moins 1 chapitre", len(chs) >= 1)
    check("numeros extraits", all(c["number"] for c in chs))

print("[search] resultats de recherche")
html = read("search_results.html")
if html is None:
    skip("recherche", "tests/fixtures/search_results.html absent")
else:
    r = eng.parse_listing(html, src["search"], src)
    check("au moins 1 resultat", len(r["items"]) >= 1)

print(f"\n{passed} OK, {failed} echecs, {skipped} ignores")
sys.exit(1 if failed else 0)
