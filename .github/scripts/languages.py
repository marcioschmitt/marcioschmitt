"""Gera languages.svg com as linguagens mais usadas em todos os repositórios
que o token enxerga (próprios, colaborações e organizações, inclusive privados).

Uso: GITHUB_TOKEN=... python3 .github/scripts/languages.py [saida.svg]
"""
import json
import os
import sys
import urllib.request
from html import escape

TOKEN = os.environ["GITHUB_TOKEN"]
OUTPUT = sys.argv[1] if len(sys.argv) > 1 else "languages.svg"
LIMIT = 8

# Cópias de projetos de terceiros: distorceriam as linguagens do que é escrito aqui.
SKIP_REPOS = {"Villela-Tech/Chat-woot", "Villela-Tech/krayin"}
# Linguagens de marcação/geradas que não dizem nada sobre o código escrito.
SKIP_LANGUAGES = {"Dockerfile", "Makefile", "Procfile", "Batchfile"}

COLORS = {
    "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Python": "#3572A5",
    "PHP": "#4F5D95", "HTML": "#e34c26", "CSS": "#663399", "Shell": "#89e051",
    "C++": "#f34b7d", "Ruby": "#701516", "Blade": "#f7523f", "PLpgSQL": "#336790",
    "Vue": "#41b883", "SCSS": "#c6538c", "Java": "#b07219", "Go": "#00ADD8",
    "C#": "#178600", "Hack": "#878787", "TSQL": "#e38c00", "MQL5": "#4A76B8",
}


def get(url):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(req) as resp:
        return json.load(resp), resp.headers.get("Link", "")


def all_repos():
    url = ("https://api.github.com/user/repos?per_page=100"
           "&affiliation=owner,collaborator,organization_member")
    repos = []
    while url:
        page, link = get(url)
        repos += page
        url = next((p.split(";")[0].strip("<> ") for p in link.split(",")
                    if 'rel="next"' in p), None)
    return repos


def main():
    totals = {}
    for repo in all_repos():
        if repo["fork"] or repo["archived"] or repo["full_name"] in SKIP_REPOS:
            continue
        langs, _ = get(repo["languages_url"])
        for lang, size in langs.items():
            if lang not in SKIP_LANGUAGES:
                totals[lang] = totals.get(lang, 0) + size

    total = sum(totals.values()) or 1
    top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:LIMIT]
    rows = [(lang, size / total * 100) for lang, size in top]

    width, bar_w, pad = 480, 440, 20
    height = 92 + ((len(rows) + 1) // 2) * 26
    parts, x = [], pad
    for lang, pct in rows:
        w = bar_w * pct / sum(p for _, p in rows)
        parts.append(f'<rect x="{x:.2f}" y="52" width="{w:.2f}" height="10" '
                     f'fill="{COLORS.get(lang, "#959da5")}"/>')
        x += w

    legend = []
    for i, (lang, pct) in enumerate(rows):
        lx = pad + (i % 2) * 220
        ly = 92 + (i // 2) * 26
        legend.append(
            f'<circle cx="{lx + 6}" cy="{ly - 4}" r="5" fill="{COLORS.get(lang, "#959da5")}"/>'
            f'<text x="{lx + 18}" y="{ly}" class="lang">{escape(lang)}</text>'
            f'<text x="{lx + 200}" y="{ly}" class="pct" text-anchor="end">{pct:.1f}%</text>')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>
  .title {{ font: 600 16px -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; fill: #2F80ED; }}
  .lang {{ font: 400 14px -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; fill: #8b949e; }}
  .pct {{ font: 600 14px -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; fill: #8b949e; }}
</style>
<text x="{pad}" y="32" class="title">Linguagens mais usadas</text>
<clipPath id="bar"><rect x="{pad}" y="52" width="{bar_w}" height="10" rx="5"/></clipPath>
<g clip-path="url(#bar)">{"".join(parts)}</g>
{"".join(legend)}
</svg>
'''
    with open(OUTPUT, "w") as f:
        f.write(svg)
    print("\n".join(f"{lang}: {pct:.1f}%" for lang, pct in rows))


if __name__ == "__main__":
    main()
