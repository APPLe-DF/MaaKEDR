# -*- coding: utf-8 -*-
"""生成 star 历史 SVG 折线图（深色/浅色两版）

用法（需 GitHub token 环境变量，仅需 public_repo 只读权限）：
    GITHUB_TOKEN=xxx python tools/gen_star_history.py
"""
import json
import os
from datetime import datetime, timezone

import urllib.request

REPO = "APPLe-DF/MaaKEDR"


def fetch_stars(token: str) -> list[dict]:
    stars = []
    page = 1
    while True:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/stargazers?per_page=100&page={page}",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.star+json",
                "User-Agent": "maakedr-star-chart",
            },
        )
        with urllib.request.urlopen(req) as r:
            batch = json.load(r)
        if not batch:
            break
        stars.extend([{"starred_at": s["starred_at"], "user": s["user"]["login"]} for s in batch])
        page += 1
        if page > 20:
            break
    return stars


def render(points: list[tuple], bg: str, grid: str, axis: str, line: str, dot: str, accent: str) -> str:
    W, H = 820, 240
    ML, MR, MT, MB = 70, 24, 30, 44
    PW, PH = W - ML - MR, H - MT - MB
    MAX_Y = 10

    t0 = points[0][0]
    t1 = max(t for t, _ in points)
    span = max((t1 - t0).total_seconds(), 86400)

    def x_of(t):
        return ML + PW * (t - t0).total_seconds() / span

    def y_of(n):
        return MT + PH * (1 - n / MAX_Y)

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
    out.append(f'<rect width="{W}" height="{H}" fill="{bg}"/>')
    for n in range(0, MAX_Y + 1, 2):
        y = y_of(n)
        out.append(f'<line x1="{ML}" y1="{y:.1f}" x2="{W - MR}" y2="{y:.1f}" stroke="{grid}" stroke-width="1"/>')
        out.append(f'<text x="{ML - 10}" y="{y + 4:.1f}" fill="{axis}" font-size="12" text-anchor="end" font-family="Arial">{n}</text>')
    n_tick = 4
    for i in range(n_tick):
        t = t0 + (t1 - t0) * i / (n_tick - 1)
        out.append(f'<text x="{x_of(t):.1f}" y="{H - MB + 20}" fill="{axis}" font-size="12" text-anchor="middle" font-family="Arial">{t.strftime("%m-%d")}</text>')
    poly = " ".join(f"{x_of(t):.1f},{y_of(n):.1f}" for t, n in points)
    out.append(f'<polyline points="{poly}" fill="none" stroke="{line}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>')
    for t, n in points:
        out.append(f'<circle cx="{x_of(t):.1f}" cy="{y_of(n):.1f}" r="4" fill="{dot}" stroke="{bg}" stroke-width="1.5"/>')
    t, n = points[-1]
    out.append(f'<text x="{x_of(t):.1f}" y="{y_of(n) - 12:.1f}" fill="{accent}" font-size="13" text-anchor="middle" font-family="Arial" font-weight="bold">{n} ⭐</text>')
    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("缺少环境变量 GITHUB_TOKEN")
    stars = fetch_stars(token)
    stars.sort(key=lambda s: s["starred_at"])
    points = [(datetime.fromisoformat(s["starred_at"].replace("Z", "+00:00")), i + 1) for i, s in enumerate(stars)]
    print(f"stars: {len(points)} ({points[0][0]} ~ {points[-1][0]})")

    out_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
    os.makedirs(out_dir, exist_ok=True)
    themes = {
        "star-history-dark.svg": ("#0d1117", "#21262d", "#8b949e", "#58a6ff", "#58a6ff", "#58a6ff"),
        "star-history-light.svg": ("#ffffff", "#d0d7de", "#57606a", "#0969da", "#0969da", "#1f883d"),
    }
    for name, (bg, grid, axis, line, dot, accent) in themes.items():
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as f:
            f.write(render(points, bg, grid, axis, line, dot, accent))
        print("written:", name)


if __name__ == "__main__":
    main()
