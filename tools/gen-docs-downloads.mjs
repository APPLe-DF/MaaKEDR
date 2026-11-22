import {existsSync, mkdirSync, readFileSync, writeFileSync} from "node:fs";
import {dirname, resolve} from "node:path";
import {fileURLToPath} from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO = process.env.MAAKEDR_REPO ?? "APPLe-DF/MaaKEDR";
const OUT = resolve(__dirname, "..", "docs", ".vuepress", "data", "latest-release.json");
// 桌面包：MaaKEDR-<os>-<arch>-<tag>-<ui>.<ext>
const DESKTOP_ASSET =
    /^MaaKEDR-(?<os>win|macos|linux)-(?<arch>x86_64|aarch64)-(?<tag>v\d+\.\d+\.\d+)-(?<ui>MFAA|MXU)\.(?<ext>zip|tar\.gz)$/;
// 安卓包：MaaKEDR-android-<universal|arm64-v8a|x86_64>-<tag>.apk
// 与 android-build.yml 的 Rename Release APK 步骤保持一致（artifact_prefix 取自
// maa-project.json 的 project.displayName）。
const ANDROID_ASSET = /^MaaKEDR-android-(?<arch>universal|arm64-v8a|x86_64)-(?<tag>v\d+\.\d+\.\d+)\.apk$/;
const OS_ORDER = [
    "win",
    "macos",
    "linux",
    "android",
];
const ARCH_ORDER = [
    "x86_64",
    "aarch64",
    "universal",
    "arm64-v8a",
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
    if (!isNonEmptyString(asset.os) || !isNonEmptyString(asset.arch)) return false;
    // ui 只有桌面包才有；安卓包固定为空串，所以这里只校验"存在且是字符串"。
    if (typeof asset.ui !== "string") return false;
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

/**
 * 2xx 也可能是形状不对的 JSON（assets 不可迭代、资源没有下载地址……），而这段在 fetch 的 try/catch 之外，
 * 抛出去会直接让 docs:build 挂掉，所以坏载荷和网络失败走同一条回退路径，返回 null 表示不可用。
 */
function buildRelease(release) {
    if (!release || typeof release !== "object" || !Array.isArray(release.assets)) return null;

    const assets = [];
    for (const item of release.assets) {
        if (!item || typeof item !== "object") continue;
        const name = item.name ?? "";
        if (typeof item.browser_download_url !== "string") continue;

        const desktop = DESKTOP_ASSET.exec(name);
        if (desktop) {
            const {os, arch, ui, ext} = desktop.groups;
            assets.push({
                name,
                os,
                arch,
                ui,
                ext,
                size: item.size ?? 0,
                url: item.browser_download_url,
            });
            continue;
        }

        // APK 只有 universal / 单 ABI 两种，没有 MFAA/MXU 之分（安卓端只有一个壳），
        // 所以 ui 记成空串，首页据此把这一组渲染成"只有下载按钮、没有界面切换"。
        const android = ANDROID_ASSET.exec(name);
        if (android) {
            const {arch, tag: apkTag} = android.groups;
            // APK 名里的 tag 必须和 release 的 tag 对得上，否则可能是上一次构建残留的工件。
            if (apkTag !== release.tag_name) continue;
            assets.push({
                name,
                os: "android",
                arch,
                ui: "",
                ext: "apk",
                size: item.size ?? 0,
                url: item.browser_download_url,
            });
            continue;
        }
    }

    assets.sort(
        (a, b) =>
            OS_ORDER.indexOf(a.os) - OS_ORDER.indexOf(b.os) ||
            ARCH_ORDER.indexOf(a.arch) - ARCH_ORDER.indexOf(b.arch) ||
            UI_ORDER.indexOf(a.ui) - UI_ORDER.indexOf(b.ui),
    );

    return {
        version: release.tag_name,
        publishedAt: release.published_at,
        releasePage: release.html_url,
        assets,
    };
}

async function main() {
    let release;
    try {
        release = await fetchLatest();
    } catch (error) {
        keep(`GitHub API call failed (${error instanceof Error ? error.message : error})`);
        return;
    }

    const tag = release?.tag_name ?? "?";
    const next = buildRelease(release);
    if (!next) {
        keep(`GitHub API replied with an unusable payload for release ${tag}`);
        return;
    }
    if (!next.assets.length) {
        keep(`no asset matched the naming scheme in release ${tag}`);
        return;
    }
    // 写出去的文件必须能通过同一套校验，否则下一次构建会把它当坏文件再覆盖一遍。
    if (!isUsableRelease(next)) {
        keep(`release ${tag} is missing metadata the homepage needs`);
        return;
    }

    const body = `${JSON.stringify(next, null, 4)}\n`;

    let previous = null;
    try {
        previous = readFileSync(OUT, "utf8");
    } catch {
        /* first run */
    }

    if (body === previous) {
        console.log(`[gen-docs-downloads] ${next.assets.length} assets for ${next.version} — unchanged`);
        return;
    }

    mkdirSync(dirname(OUT), {recursive: true});
    writeFileSync(OUT, body, "utf8");
    console.log(
        `[gen-docs-downloads] wrote ${next.assets.length} assets for ${next.version} to docs/.vuepress/data/latest-release.json`,
    );
}

await main();
