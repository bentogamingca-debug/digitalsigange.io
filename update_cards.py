#!/usr/bin/env python3
"""Pulls Collectr's trending cards and writes cards.json (USD prices) for the Yodeck page."""
import html as H, json, re, sys, urllib.request

URL = "https://app.getcollectr.com/?sortType=trendingToday&sortOrder=DESC&category=89,68,3&cardType=cards"
MAX_CARDS = 30
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def parse(page):
    out, seen = [], set()
    for li in re.findall(r"<li\b.*?</li>", page, re.S):
        m = re.search(r"product_(\d+)", li)
        if not m or m.group(1) in seen:
            continue
        li = re.sub(r"<(script|style)\b.*?</\1>", "", li, flags=re.S)
        tx = [t for t in (re.sub(r"\s+", " ", H.unescape(x)).strip()
                          for x in re.sub(r"<[^>]+>", "\n", li).split("\n")) if t]
        j = " ".join(tx)
        pm = re.search(r"\$([\d,]+\.\d{2})", j)
        cm = re.search(r"([+-])\s*\$([\d,]+\.\d{2})\s*\(\s*([+-]?[\d.]+)%", j)
        if not pm or len(tx) < 3:
            continue
        line = next((t for t in tx if "\u2022" in t), "")
        rar, _, rest = line.partition("\u2022")
        rar, rest = rar.strip(), rest.strip()
        nm = re.match(r"(\d+(?:/\d+)?)", rest)
        num = nm.group(1) if nm else re.sub(r"(Reverse )?(Holofoil|Normal)$", "", rest, flags=re.I).strip()
        if rar.lower() == "none":
            rar = ""
        sg = -1 if cm and cm.group(1) == "-" else 1
        seen.add(m.group(1))
        out.append({
            "id": int(m.group(1)),
            "name": re.sub(r"\s+-\s+\S+\s*\(.*\)\s*$", "", tx[0]),
            "set": tx[1],
            "rarity": rar,
            "num": num,
            "price": float(pm.group(1).replace(",", "")),
            "chg": sg * float(cm.group(2).replace(",", "")) if cm else 0,
            "pct": sg * abs(float(cm.group(3))) if cm else 0,
        })
    return out[:MAX_CARDS]


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": UA, "Accept": "text/html"})
    page = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    cards = parse(page)
    if len(cards) < 10:  # page changed or blocked: keep the existing cards.json untouched
        sys.exit("Only parsed %d cards - not overwriting cards.json" % len(cards))
    with open("cards.json", "w", encoding="utf-8") as f:
        json.dump(cards, f, indent=2, ensure_ascii=False)
    print("Wrote %d cards; first: %s $%.2f" % (len(cards), cards[0]["name"], cards[0]["price"]))


if __name__ == "__main__":
    main()
