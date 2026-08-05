"""生成 star 历史 SVG 折线图（深色/浅色两版，star-history 风格）

用法（需 GitHub token 环境变量，仅需 public_repo 只读权限）：
    GITHUB_TOKEN=xxx python tools/gen_star_history.py
"""
import json
import math
import os
import urllib.request
from datetime import datetime

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


def catmull_rom_to_bezier(pts: list[tuple[float, float]]) -> list[tuple[float, float, float, float, float, float]]:
    """Catmull-Rom 样条转三次贝塞尔控制点（平滑曲线）。"""
    segments = []
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        segments.append((*c1, *c2, *p2))
    return segments


def render(points: list[tuple], theme: dict) -> str:
    W, H = 920, 300
    ML, MR, MT, MB = 64, 24, 56, 46
    PW, PH = W - ML - MR, H - MT - MB
    bg = theme["bg"]
    grid = theme["grid"]
    axis = theme["axis"]
    line_c = theme["line"]
    grad_c = theme.get("gradient", line_c)
    title_c = theme["title"]
    sub_c = theme["subtitle"]

    max_n = max(n for _, n in points)
    y_max = max(6, math.ceil((max_n + 2) / 2) * 2)

    t0 = points[0][0]
    t1 = max(t for t, _ in points)
    span = max((t1 - t0).total_seconds(), 86400)

    def x_of(t):
        return ML + PW * (t - t0).total_seconds() / span

    def y_of(n):
        return MT + PH * (1 - n / y_max)

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="-apple-system, Segoe UI, Helvetica, Arial, sans-serif">']
    out.append(f'<defs><linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">'
               f'<stop offset="0%" stop-color="{grad_c}" stop-opacity="0.28"/>'
               f'<stop offset="100%" stop-color="{grad_c}" stop-opacity="0"/>'
               f'</linearGradient></defs>')
    out.append(f'<rect width="{W}" height="{H}" rx="10" fill="{bg}"/>')

    # 标题区：repo 名 + Star History + 总星数
    out.append(f'<text x="{ML}" y="32" fill="{title_c}" font-size="17" font-weight="600">{REPO}</text>')
    out.append(f'<text x="{ML + 8}" y="50" fill="{sub_c}" font-size="12">{max_n} stars · Star History</text>')

    # 横向网格 + y 轴标签
    step = y_max // 4 or 1
    for n in range(0, y_max + 1, step):
        y = y_of(n)
        out.append(f'<line x1="{ML}" y1="{y:.1f}" x2="{W - MR}" y2="{y:.1f}" stroke="{grid}" stroke-width="1"/>')
        out.append(f'<text x="{ML - 10}" y="{y + 4:.1f}" fill="{axis}" font-size="12" text-anchor="end">{n}</text>')

    # x 轴日期刻度（8 个均匀分布）
    n_tick = 8
    for i in range(n_tick):
        t = t0 + (t1 - t0) * i / (n_tick - 1)
        out.append(f'<text x="{x_of(t):.1f}" y="{H - MB + 18}" fill="{axis}" font-size="11" text-anchor="middle">{t.strftime("%Y-%m-%d")}</text>')

    xy = [(x_of(t), y_of(n)) for t, n in points]

    # 面积渐变填充
    area = f"M {xy[0][0]:.1f} {H - MB:.1f} L " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in xy) + f" L {xy[-1][0]:.1f} {H - MB:.1f} Z"
    out.append(f'<path d="{area}" fill="url(#areaGrad)"/>')

    # 平滑曲线
    if len(xy) >= 2:
        segs = catmull_rom_to_bezier(xy)
        d = f"M {xy[0][0]:.1f} {xy[0][1]:.1f} "
        for c1x, c1y, c2x, c2y, ex, ey in segs:
            d += f"C {c1x:.1f} {c1y:.1f} {c2x:.1f} {c2y:.1f} {ex:.1f} {ey:.1f} "
        out.append(f'<path d="{d}" fill="none" stroke="{line_c}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>')

    # 数据点（首尾点略大）
    for i, (x, y) in enumerate(xy):
        r = 4.5 if i in (0, len(xy) - 1) else 3.5
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{bg}" stroke="{line_c}" stroke-width="2"/>')

    # 最新值标注（右侧标签）
    x, y = xy[-1]
    out.append(
        f'<g><rect x="{x + 8:.1f}" y="{y - 13:.1f}" rx="10" width="30" height="22" fill="{line_c}"/>'
        f'<text x="{x + 23:.1f}" y="{y + 3:.1f}" fill="{bg}" font-size="12" font-weight="600" text-anchor="middle">{max_n}</text></g>'
    )

    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    import sys

    token = os.environ.get("GITHUB_TOKEN")
    cache = sys.argv[1] if len(sys.argv) > 1 else None
    if cache:
        with open(cache, encoding="utf-8") as f:
            stars = json.load(f)
    elif token:
        stars = fetch_stars(token)
    else:
        raise SystemExit("缺少环境变量 GITHUB_TOKEN，或传入 stars JSON 缓存路径")
    stars.sort(key=lambda s: s["starred_at"])
    # 按天聚合（同一天多个 star 合并为一个点，避免密集点导致平滑曲线过冲）
    by_day: dict[str, int] = {}
    for i, s in enumerate(stars, 1):
        day = s["starred_at"][:10]
        by_day[day] = i
    points = [
        (datetime.fromisoformat(day + "T00:00:00+00:00"), n) for day, n in sorted(by_day.items())
    ]
    print(f"stars: {len(stars)} ({points[0][0]} ~ {points[-1][0]}), points: {len(points)}")

    out_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
    os.makedirs(out_dir, exist_ok=True)
    themes = {
        "star-history-dark.svg": {
            "bg": "#0d1117", "grid": "#1c2128", "axis": "#8b949e",
            "line": "#58a6ff", "gradient": "#58a6ff",
            "title": "#e6edf3", "subtitle": "#8b949e",
        },
        "star-history-light.svg": {
            "bg": "#ffffff", "grid": "#eef1f4", "axis": "#656d76",
            "line": "#0969da", "gradient": "#0969da",
            "title": "#1f2328", "subtitle": "#656d76",
        },
    }
    for name, theme in themes.items():
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as f:
            f.write(render(points, theme))
        print("written:", name)


if __name__ == "__main__":
    main()
