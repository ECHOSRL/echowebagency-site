#!/usr/bin/env python3
"""Inject Vercel Analytics snippet into all HTML pages before </head>.

Idempotent: skips files that already contain the snippet.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNIPPET = '<script defer src="/_vercel/insights/script.js"></script>'
MARKER = "_vercel/insights"

def main():
    htmls = [p for p in ROOT.rglob("*.html") if ".git" not in p.parts and "node_modules" not in p.parts]
    updated = skipped = 0
    for p in htmls:
        text = p.read_text(encoding="utf-8")
        if MARKER in text:
            skipped += 1
            continue
        if "</head>" not in text:
            print(f"  ! no </head>: {p.relative_to(ROOT)}")
            continue
        new = text.replace("</head>", f"{SNIPPET}\n</head>", 1)
        p.write_text(new, encoding="utf-8")
        updated += 1
        print(f"  ✓ {p.relative_to(ROOT)}")
    print(f"\nUpdated: {updated} · Skipped (already had snippet): {skipped} · Total: {len(htmls)}")

if __name__ == "__main__":
    main()
