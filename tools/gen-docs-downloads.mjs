import {mkdirSync, readFileSync, writeFileSync} from "node:fs";
import {dirname, resolve} from "node:path";
import {fileURLToPath} from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO = process.env.MAAKEDR_REPO ?? "APPLe-DF/MaaKEDR";
const OUT = resolve(__dirname, "..", "docs", ".vuepress", "data", "latest-release.json");
const ASSET =
    /^MaaKEDR-(?<os>win|macos|linux)-(?<arch>x86_64|aarch64)-(?<tag>v\d+\.\d+\.\d+)-(?<ui>MFAA|MXU)\.(?<ext>zip|tar\.gz)$/;
const OS_ORDER = [
    "win",
    "macos",
    "linux",
];
const ARCH_ORDER = [
    "x86_64",
    "aarch64",
];
const UI_ORDER = [
    "MFAA",
    "MXU",
];

// Never fail the docs build over a release lookup: fall back to the committed file.
const PLACEHOLDER = `${JSON.stringify({version: null, publishedAt: null, releasePage: null, assets: []}, null, 4)}\n`;

function keep(reason) {
    console.warn(`[gen-docs-downloads] ${reason} — keeping the previously generated file`);
    // 全新 clone 没有“上一次的文件”可留，而组件是静态 import 这份 JSON 的，缺文件会让整站构建失败。
    // 所以补一份空数据，首页自己降级成“暂无发布数据”。
    try {
        readFileSync(OUT);
    } catch {
        mkdirSync(dirname(OUT), {recursive: true});
        writeFileSync(OUT, PLACEHOLDER, "utf8");
        console.warn("[gen-docs-downloads] wrote an empty placeholder so the docs build still resolves");
    }
}

async function fetchLatest() {
    const headers = {
        Accept: "application/vnd.github+json",
        "User-Agent": "MaaKEDR-docs",
    };
    const token = process.env.GH_TOKEN ?? process.env.GITHUB_TOKEN;
    if (token) headers.Authorization = `Bearer ${token}`;

    const res = await fetch(`https://api.github.com/repos/${REPO}/releases/latest`, {
        headers,
        signal: AbortSignal.timeout(20_000),
    });
    if (!res.ok) throw new Error(`GitHub API replied ${res.status}`);
    return await res.json();
}

async function main() {
    let release;
    try {
        release = await fetchLatest();
    } catch (error) {
        keep(`GitHub API unreachable (${error instanceof Error ? error.message : error})`);
        return;
    }

    const assets = [];
    for (const item of release.assets ?? []) {
        const m = ASSET.exec(item.name ?? "");
        if (!m) continue;
        const {os, arch, ui, ext} = m.groups;
        assets.push({
            name: item.name,
            os,
            arch,
            ui,
            ext,
            size: item.size ?? 0,
            url: item.browser_download_url,
        });
    }

    if (!assets.length) {
        keep(`no asset matched the naming scheme in release ${release.tag_name ?? "?"}`);
        return;
    }

    assets.sort(
        (a, b) =>
            OS_ORDER.indexOf(a.os) - OS_ORDER.indexOf(b.os) ||
            ARCH_ORDER.indexOf(a.arch) - ARCH_ORDER.indexOf(b.arch) ||
            UI_ORDER.indexOf(a.ui) - UI_ORDER.indexOf(b.ui),
    );

    const next = `${JSON.stringify(
        {
            version: release.tag_name,
            publishedAt: release.published_at,
            releasePage: release.html_url,
            assets,
        },
        null,
        4,
    )}\n`;

    let previous = null;
    try {
        previous = readFileSync(OUT, "utf8");
    } catch {
        /* first run */
    }

    if (next === previous) {
        console.log(`[gen-docs-downloads] ${assets.length} assets for ${release.tag_name} — unchanged`);
        return;
    }

    mkdirSync(dirname(OUT), {recursive: true});
    writeFileSync(OUT, next, "utf8");
    console.log(
        `[gen-docs-downloads] wrote ${assets.length} assets for ${release.tag_name} to docs/.vuepress/data/latest-release.json`,
    );
}

await main();
