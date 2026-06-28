#!/usr/bin/env python3
"""Static blog generator for echo.srl.

Reads .md files from blog-src/ with YAML frontmatter, produces:
- blog/<slug>.html          (each article)
- blog/index.html           (article list)
- updates sitemap.xml       (adds /blog/* entries, preserves the rest)
- blog/feed.xml             (RSS 2.0)

Run:  python3 scripts/build_blog.py
"""
import os
import re
import sys
import html
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "blog-src"
OUT = ROOT / "blog"
SITEMAP = ROOT / "sitemap.xml"
SITE = "https://www.echo.srl"
CALENDLY = "https://calendly.com/echowebagency-info/formazione"


# ---------- markdown ----------

def md_to_html(md: str) -> str:
    """Minimal markdown to HTML — supports h2/h3, **bold**, *italic*, lists,
    links, paragraphs, blockquotes. No external deps."""
    out = []
    in_ul = False
    in_blockquote = False
    para_buf = []

    def flush_para():
        nonlocal para_buf
        if para_buf:
            text = " ".join(para_buf).strip()
            if text:
                out.append(f"<p>{inline(text)}</p>")
            para_buf = []

    def inline(s: str) -> str:
        s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
                   lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', s)
        s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        s = re.sub(r'(?<![*])\*([^*]+?)\*(?![*])', r'<em>\1</em>', s)
        return s

    for raw in md.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush_para()
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if in_blockquote:
                out.append("</blockquote>")
                in_blockquote = False
            continue
        if line.startswith("## "):
            flush_para()
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(f"<h2>{inline(line[3:].strip())}</h2>")
        elif line.startswith("### "):
            flush_para()
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(f"<h3>{inline(line[4:].strip())}</h3>")
        elif line.startswith("- "):
            flush_para()
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"  <li>{inline(line[2:].strip())}</li>")
        elif line.startswith("> "):
            flush_para()
            if not in_blockquote:
                out.append("<blockquote>")
                in_blockquote = True
            out.append(f"  <p>{inline(line[2:].strip())}</p>")
        else:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if in_blockquote:
                out.append("</blockquote>")
                in_blockquote = False
            para_buf.append(line)
    flush_para()
    if in_ul:
        out.append("</ul>")
    if in_blockquote:
        out.append("</blockquote>")
    return "\n".join(out)


# ---------- frontmatter ----------

def parse_article(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{path.name}: missing frontmatter")
    end = text.index("\n---", 3)
    fm_raw = text[3:end].strip()
    body = text[end + 4:].lstrip()
    fm = {}
    for line in fm_raw.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            v = v.strip().strip('"')
            if k.strip() == "keywords":
                v = [x.strip() for x in v.strip("[]").split(",") if x.strip()]
            fm[k.strip()] = v
    required = {"title", "slug", "date", "description"}
    missing = required - set(fm.keys())
    if missing:
        raise ValueError(f"{path.name}: missing frontmatter keys {missing}")
    fm["body_html"] = md_to_html(body)
    fm["src_path"] = path
    return fm


# ---------- HTML templates ----------

NAV = '''<nav>
  <a href="/" class="nav-logo">
    <img src="/logo-on-cream.png" alt="Echo S.r.l." onerror="this.style.display='none';this.nextSibling.style.display='block'">
    <span style="display:none;font-family:var(--font-serif);font-size:1.25rem;font-weight:600;">Echo</span>
  </a>
  <ul class="nav-links">
    <li><a href="/#origine">Chi siamo</a></li>
    <li><a href="/#metodo">Metodo</a></li>
    <li><a href="/blog/">Blog</a></li>
    <li><a href="/#contatti">Contatti</a></li>
  </ul>
  <a href="''' + CALENDLY + '''" target="_blank" rel="noopener" class="nav-cta">Prenota una call</a>
</nav>'''

FOOTER = '''<footer>
  <a href="/" class="footer-logo">
    <img src="/logo-on-cream.png" alt="Echo S.r.l." onerror="this.style.display='none';this.nextSibling.style.display='block'">
    <span style="display:none;font-family:var(--font-serif);font-weight:600;">Echo</span>
  </a>
  <p class="footer-copy">Echo S.r.l. &mdash; P.IVA 03135740359 &mdash; Via Lelio e Fausto Socini 32/B, 42122 Reggio Emilia</p>
  <div class="footer-links">
    <a href="mailto:info@echowebagency.it">info@echowebagency.it</a>
    <a href="https://www.linkedin.com/company/echo-srl-re" target="_blank" rel="noopener">LinkedIn</a>
    <a href="https://www.instagram.com/echowebagency/" target="_blank" rel="noopener">Instagram</a>
  </div>
</footer>'''


def head(title: str, description: str, url: str, image: str = "/logo-on-cream.png",
        og_type: str = "website", article_json_ld: str = "") -> str:
    img_full = image if image.startswith("http") else f"{SITE}{image}"
    return f'''<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/styles.css">

<link rel="canonical" href="{url}" />
<link rel="icon" type="image/png" href="/logo-on-cream.png" />
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1" />
<link rel="alternate" type="application/rss+xml" title="Blog Echo" href="/blog/feed.xml" />

<meta property="og:type" content="{og_type}" />
<meta property="og:locale" content="it_IT" />
<meta property="og:url" content="{url}" />
<meta property="og:title" content="{html.escape(title)}" />
<meta property="og:description" content="{html.escape(description)}" />
<meta property="og:image" content="{img_full}" />
<meta property="og:site_name" content="Echo S.r.l." />

<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{html.escape(title)}" />
<meta name="twitter:description" content="{html.escape(description)}" />
<meta name="twitter:image" content="{img_full}" />
{article_json_ld}
</head>
<body>
'''


def render_article(fm: dict) -> str:
    url = f"{SITE}/blog/{fm['slug']}"
    keywords = fm.get("keywords", [])
    article_jsonld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "@id": f"{url}#article",
        "headline": fm["title"],
        "description": fm["description"],
        "url": url,
        "datePublished": fm["date"],
        "dateModified": fm.get("updated", fm["date"]),
        "author": {
            "@type": "Person",
            "name": "Silvia Rinaldi",
            "url": f"{SITE}/#origine",
        },
        "publisher": {
            "@type": "Organization",
            "name": "Echo S.r.l.",
            "logo": {"@type": "ImageObject", "url": f"{SITE}/logo-on-cream.png"},
        },
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "inLanguage": "it-IT",
        "keywords": ", ".join(keywords) if keywords else None,
    }
    article_jsonld = {k: v for k, v in article_jsonld.items() if v is not None}
    jsonld_script = (
        '\n<script type="application/ld+json">'
        + json.dumps(article_jsonld, ensure_ascii=False)
        + "</script>"
    )

    related_links = fm.get("related", "")
    related_html = ""
    if related_links:
        items = [l.strip() for l in related_links.split(",") if l.strip()]
        if items:
            related_html = '<div class="internal-links"><h3>Approfondisci</h3>' \
                + "".join(f'<a href="{i}">{i.strip("/").replace("-", " ").title()}</a>' for i in items) \
                + "</div>"

    body = head(
        title=fm["title"] + " | Blog Echo",
        description=fm["description"],
        url=url,
        og_type="article",
        article_json_ld=jsonld_script,
    )
    body += NAV
    body += f'''
<article>
<section class="page-hero">
  <nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Home</a> &rsaquo; <a href="/blog/">Blog</a> &rsaquo; {html.escape(fm['title'])}</nav>
  <p class="eyebrow">{fm['date']}</p>
  <h1>{html.escape(fm['title'])}</h1>
  <p class="intro">{html.escape(fm['description'])}</p>
</section>

<section class="article-body">
{fm['body_html']}
</section>

<section class="cta-section">
  <h2>Vuoi capire come l'AI<br><em>può lavorare nei tuoi processi?</em></h2>
  <p>Prenota una call gratuita di 30 minuti. Ti aiuto a capire da dove partire, senza vendere niente.</p>
  <a href="{CALENDLY}" target="_blank" rel="noopener" class="btn-primary">Prenota la call gratuita</a>
</section>

{related_html}
</article>

'''
    body += FOOTER
    body += "\n</body>\n</html>\n"
    return body


def render_index(articles: list) -> str:
    url = f"{SITE}/blog/"
    body = head(
        title="Blog Echo — AI, governance, processi per PMI italiane",
        description="Articoli operativi su AI Act, Digital Product Passport, AI nei processi aziendali e formazione. Scritto da Silvia Rinaldi, founder Echo S.r.l.",
        url=url,
    )
    body += NAV
    body += '''
<section class="page-hero">
  <nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Home</a> &rsaquo; Blog</nav>
  <p class="eyebrow">Note di lavoro</p>
  <h1>Blog<br><em>Echo</em></h1>
  <p class="intro">Riflessioni operative su AI, processi e governance. Per chi guida un'azienda manifatturiera, moda o beauty in Italia e vuole capire dove l'intelligenza artificiale fa davvero la differenza.</p>
</section>

<section class="article-list">
'''
    for a in sorted(articles, key=lambda x: x["date"], reverse=True):
        body += f'''  <article class="article-card">
    <p class="article-date">{a['date']}</p>
    <h2><a href="/blog/{a['slug']}">{html.escape(a['title'])}</a></h2>
    <p>{html.escape(a['description'])}</p>
    <a href="/blog/{a['slug']}" class="read-more">Leggi &rsaquo;</a>
  </article>
'''
    body += '</section>\n'
    body += FOOTER
    body += "\n</body>\n</html>\n"
    return body


def render_rss(articles: list) -> str:
    items = []
    for a in sorted(articles, key=lambda x: x["date"], reverse=True)[:30]:
        url = f"{SITE}/blog/{a['slug']}"
        pub = a["date"] + "T09:00:00+00:00"
        items.append(f'''  <item>
    <title>{html.escape(a['title'])}</title>
    <link>{url}</link>
    <guid isPermaLink="true">{url}</guid>
    <pubDate>{pub}</pubDate>
    <description>{html.escape(a['description'])}</description>
  </item>''')
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>Blog Echo S.r.l.</title>
  <link>{SITE}/blog/</link>
  <description>AI, governance, processi per PMI italiane. Scritto da Silvia Rinaldi.</description>
  <language>it-IT</language>
{chr(10).join(items)}
</channel>
</rss>
'''


# ---------- sitemap update ----------

def update_sitemap(articles: list):
    """Replace any existing /blog/* entries with current set."""
    text = SITEMAP.read_text(encoding="utf-8")
    # Strip namespace for simpler parsing — re-add on write
    text_no_ns = re.sub(r'xmlns="[^"]*"', '', text, count=1)
    root = ET.fromstring(text_no_ns)
    # Remove existing /blog/* and /blog entries
    to_remove = [u for u in root.findall("url") if "/blog" in (u.find("loc").text or "")]
    for u in to_remove:
        root.remove(u)
    # Add blog index
    for url_str, prio, lastmod in [
        (f"{SITE}/blog/", "0.9", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
    ] + [
        (f"{SITE}/blog/{a['slug']}", "0.7", a['date']) for a in articles
    ]:
        u = ET.SubElement(root, "url")
        ET.SubElement(u, "loc").text = url_str
        ET.SubElement(u, "lastmod").text = lastmod
        ET.SubElement(u, "changefreq").text = "monthly"
        ET.SubElement(u, "priority").text = prio
    # Serialize
    body = ET.tostring(root, encoding="unicode")
    body = body.replace("<urlset>", '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    body = '<?xml version="1.0" encoding="UTF-8"?>\n' + body + "\n"
    SITEMAP.write_text(body, encoding="utf-8")


def main():
    if not SRC.exists():
        print(f"No {SRC}, exiting", file=sys.stderr); sys.exit(1)
    OUT.mkdir(exist_ok=True)
    md_files = sorted(SRC.glob("*.md"))
    if not md_files:
        print("No articles found", file=sys.stderr); sys.exit(0)

    articles = []
    for p in md_files:
        try:
            fm = parse_article(p)
        except Exception as e:
            print(f"ERROR {p.name}: {e}", file=sys.stderr); continue
        out_path = OUT / f"{fm['slug']}.html"
        out_path.write_text(render_article(fm), encoding="utf-8")
        print(f"  ✓ {out_path.relative_to(ROOT)}")
        articles.append(fm)

    # Index + RSS
    (OUT / "index.html").write_text(render_index(articles), encoding="utf-8")
    print(f"  ✓ blog/index.html")
    (OUT / "feed.xml").write_text(render_rss(articles), encoding="utf-8")
    print(f"  ✓ blog/feed.xml")

    # Sitemap
    update_sitemap(articles)
    print(f"  ✓ sitemap.xml updated ({len(articles)} blog URLs)")

    print(f"\nBuilt {len(articles)} articles.")


if __name__ == "__main__":
    main()
