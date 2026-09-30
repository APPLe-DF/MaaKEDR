import {existsSync, mkdirSync, readFileSync, writeFileSync} from "node:fs";
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

function isNonEmptyString(value) {
    return typeof value === "string" && value.length > 0;
}

// 一个 asset 缺 os/arch/ui 会让首页静默少一行，size 不是数字会渲染成“NaN MB”，所以逐个字段对齐 HomeDownload 的读法。
function isUsableAsset(asset) {
    if (!asset || typeof asset !== "object") return false;
    if (!isNonEmptyString(asset.name) || !isNonEmptyString(asset.url)) return false;
    if (!isNonEmptyString(asset.os) || !isNonEmptyString(asset.arch) || !isNonEmptyString(asset.ui)) return false;
    return Number.isFinite(asset.size) && asset.size >= 0;
}

// 首页还会直接读版本元数据（publishedAt 要 slice(0, 10)，releasePage 当链接），所以「能 parse」不等于「能用」。
function isUsableRelease(value) {
    if (!value || typeof value !== "object") return false;
    if (!Array.isArray(value.assets)) return false;
    if (!value.assets.every(isUsableAsset)) return false;
    if (value.assets.length === 0) {
        return value.version === null && value.publishedAt === null && value.releasePage === null;
    }
    return (
        isNonEmptyString(value.version) && isNonEmptyString(value.publishedAt) && isNonEmptyString(value.releasePage)
    );
}

function readPrevious() {
    try {
        return JSON.parse(readFileSync(OUT, "utf8"));
    } catch {
        // 全新 clone 没有上一次的文件；半截 JSON 也走这里，不能当成“有旧数据”。
        return null;
    }
}

function keep(reason) {
    const previous = readPrevious();
    if (isUsableRelease(previous)) {
        console.warn(`[gen-docs-downloads] ${reason} — keeping the previously generated file`);
        return;
    }
    // 组件是静态 import 这份 JSON 的，缺文件或坏文件都会让整站构建失败，所以必须落成能用的占位。
    // 提示要分清「全新 clone」和「上次留下了坏文件」，否则排查时看不出是后者。
    const hadFile = existsSync(OUT);
    mkdirSync(dirname(OUT), {recursive: true});
    writeFileSync(OUT, PLACEHOLDER, "utf8");
    console.warn(
        `[gen-docs-downloads] ${reason} — ${hadFile ? "replaced the unusable previous file" : "wrote an empty placeholder"} so the docs build still resolves`,
    );
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
