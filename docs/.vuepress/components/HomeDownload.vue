<script setup lang="ts">
import release from "../data/latest-release.json";
import {VPIcon} from "vuepress-theme-plume/client";
import {computed, onMounted, ref} from "vue";

type Asset = {
    arch: string;
    ext: string;
    name: string;
    os: string;
    size: number;
    // 安卓包没有界面版本之分，ui 为空串；桌面包是 MFAA / MXU。
    ui: "MFAA" | "MXU" | "";
    url: string;
};

type Os = "win" | "macos" | "linux" | "android";
// 桌面是 x86_64 / aarch64；安卓包按 ABI 命名（arm64-v8a / x86_64），另有 universal 全量包。
type Arch = "x86_64" | "aarch64" | "arm64-v8a" | "universal";
type Detected = {os: Os; arch: Arch};

const props = withDefaults(
    defineProps<{
        // Plume 把整条 config 项 v-bind 过来，声明 type 以免它落到 DOM 上。
        type?: string;
        title?: string;
        lang?: "zh" | "en";
        index?: number;
        onlyOnce?: boolean;
    }>(),
    {type: "", title: "", lang: "zh", index: -1, onlyOnce: false},
);

const ARCH_LABEL: Record<string, string> = {
    x86_64: "x86_64",
    aarch64: "ARM64",
    "arm64-v8a": "ARM64",
    universal: "通用",
};
const OS_LABEL: Record<Os, string> = {win: "Windows", macos: "macOS", linux: "Linux", android: "Android"};

const TEXT = {
    zh: {
        hint: "MFAA 与 MXU 只有界面外观的区别，功能完全一致，任选其一即可。",
        version: "当前版本",
        published: "发布于",
        allVersions: "全部版本",
        mirror: "Mirror酱 高速下载",
        unavailable: "发布数据暂不可用（构建时取不到 GitHub Release），请到",
        unavailableTail: "页面查看最新版本。",
        pickedTitle: "已识别你的设备",
        uiLabel: "界面版本",
        download: "下载",
        downloadApk: "下载 APK",
        apk: "APK",
        otherTitle: "其他平台与架构",
        otherHint: "识别有误或想下别的包？点开选择",
    },
    en: {
        hint: "MFAA and MXU differ only in appearance, features are identical, so pick either one.",
        version: "Current version",
        published: "published",
        allVersions: "All versions",
        mirror: "Mirror酱 fast download",
        unavailable: "Release data is unavailable right now (the build could not reach GitHub). See the",
        unavailableTail: "page for the latest version.",
        pickedTitle: "Detected your device",
        uiLabel: "Interface",
        download: "Download",
        downloadApk: "Download APK",
        apk: "APK",
        otherTitle: "Other platforms & architectures",
        otherHint: "Wrong match, or need a different build? Open to pick",
    },
};

const GROUPS = [
    {os: "win", label: "Windows", icon: "ri:windows-line"},
    {os: "macos", label: "macOS", icon: "ri:apple-line"},
    {os: "linux", label: "Linux", icon: "ri:terminal-box-line"},
    {os: "android", label: "Android", icon: "ri:android-line"},
];

const UI_OPTIONS: Asset["ui"][] = [
    "MFAA",
    "MXU",
];

const assets = release.assets as Asset[];
// 生成脚本取不到 release 且没有旧数据可留时会写空占位，这里降级成一行提示，而不是摆一排空分组。
const available = assets.length > 0 && Boolean(release.version);
const t = computed(() => TEXT[props.lang]);

const groups = GROUPS.map((group) => ({
    ...group,
    rows: [...new Set(assets.filter((a) => a.os === group.os).map((a) => a.arch))].map((arch) => ({
        arch,
        label: ARCH_LABEL[arch] ?? arch,
        uis: assets.filter((a) => a.os === group.os && a.arch === arch),
    })),
}));

/**
 * 设备识别结果只在挂载后写入：SSR 阶段 detected 是 null，服务端和客户端首帧都渲染
 * 同一份完整列表，不会产生 hydration 失配；JS 没跑时页面就是原来的完整列表。
 */
const detected = ref<Detected | null>(null);
// 界面版本默认 MFAA；用户切到 MXU 后推荐项跟着换。
const uiChoice = ref<Asset["ui"]>("MFAA");

const deviceLabel = computed(() => {
    const d = detected.value;
    return d ? OS_LABEL[d.os] + " / " + (ARCH_LABEL[d.arch] ?? d.arch) : "";
});

/**
 * 推荐项：优先「同系统 + 同架构 + 当前界面版本」，
 * 再退到「同系统 + 同架构」（该架构没有所选界面时，例如 Linux ARM64 只有 MFAA），
 * 最后退到「同系统任意包」。任何一步都找不到就返回 null，卡片整块不渲染。
 */
const recommended = computed<Asset | null>(() => {
    const d = detected.value;
    if (!d) return null;
    const sameOs = assets.filter((a) => a.os === d.os);
    if (!sameOs.length) return null;

    // 安卓只有 universal / 单 ABI 之分，没有界面版本，按架构匹配即可。
    if (d.os === "android") {
        return sameOs.find((a) => a.arch === d.arch) ?? sameOs.find((a) => a.arch === "universal") ?? sameOs[0] ?? null;
    }

    return (
        sameOs.find((a) => a.arch === d.arch && a.ui === uiChoice.value) ??
        sameOs.find((a) => a.arch === d.arch) ??
        sameOs.find((a) => a.ui === uiChoice.value) ??
        sameOs[0] ??
        null
    );
});

// 界面版本切换只在推荐项确实是桌面包时才显示。
const showUiChoice = computed(() => recommended.value !== null && recommended.value.os !== "android");

// MFAA/MXU 的说明只对桌面包成立：
//   - 访问者被推荐的是 APK（安卓设备）时，说明和他的选择无关；
//   - 整份 release 里根本没有桌面包时（只发了 APK 的极端情况），说明更是无稽之谈。
// 识别失败、尚未挂载时 recommended 为 null，这时保留说明：完整列表里确实有 MFAA/MXU 两列。
const hideUiHint = computed(
    () => assets.length > 0 && (assets.every((a) => a.os === "android") || recommended.value?.os === "android"),
);

function isPicked(asset: Asset): boolean {
    return recommended.value?.name === asset.name;
}

type UaData = {
    platform?: string;
    getHighEntropyValues?: (hints: string[]) => Promise<{architecture?: string; bitness?: string}>;
};

/**
 * 判断操作系统。手机/平板/ChromeOS 没有对应包，一律返回 null，让区块保持原样。
 *
 * iPadOS 13+ 的 Safari 会把 UA 伪装成桌面 Mac，只能靠"Mac 平台 + 多点触控"拆穿。
 * 但这条启发式只在拿不到 userAgentData 时才用：Chromium 系浏览器一定带 userAgentData，
 * 而 iPad 上的浏览器（Safari / CriOS）都没有，所以有这个字段就说明是真桌面。
 * 不这么分开的话，任何把 maxTouchPoints 报成非 0 的桌面 Chrome（无头模式、触屏本）
 * 都会被误判成 iPad，macOS 整块识别直接失效。
 */
function detectOs(platform: string, ua: string, maxTouchPoints: number, hasUaData: boolean): Os | null {
    const p = platform.toLowerCase();
    const s = ua.toLowerCase();
    const macLike = p.includes("mac") || s.includes("macintosh");
    if (s.includes("ipad") || s.includes("iphone") || s.includes("ipod")) return null;
    if (macLike && maxTouchPoints > 1 && !hasUaData) return null;
    // Android 现在有 APK 可下，所以不再返回 null；必须排在 Linux 判断之前，
    // 因为安卓的 UA 里始终带 "Linux"。
    if (p.includes("android") || s.includes("android")) return "android";
    if (p.includes("chrome os") || s.includes("cros")) return null;
    if (p.startsWith("win") || s.includes("windows")) return "win";
    if (macLike) return "macos";
    if (p.includes("linux") || s.includes("linux")) return "linux";
    return null;
}

/** 读 WebGL 渲染器名。macOS 上 UA 分辨不出芯片，只能靠这个。 */
function gpuRenderer(): string {
    try {
        const canvas = document.createElement("canvas");
        const gl = (canvas.getContext("webgl") ??
            canvas.getContext("experimental-webgl")) as WebGLRenderingContext | null;
        if (!gl) return "";
        const info = gl.getExtension("WEBGL_debug_renderer_info");
        const name = info ? gl.getParameter(info.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
        return typeof name === "string" ? name : "";
    } catch {
        return "";
    }
}

async function detectArch(os: Os, ua: string, uaData?: UaData): Promise<Arch> {
    // Chromium 的高熵提示最可靠：Windows ARM64 上 UA 依然写 x64，只有这里能拆穿。
    if (uaData?.getHighEntropyValues) {
        try {
            const v = await uaData.getHighEntropyValues([
                "architecture",
                "bitness",
            ]);
            if (v.architecture === "arm") return "aarch64";
            if (v.architecture === "x86") return "x86_64";
        } catch {
            // 高熵提示被权限策略拒绝时，继续走下面的兜底判断。
        }
    }

    // 安卓：高熵提示能给出 arm / x86；拿不到时按 arm64-v8a 猜——现在市面上的手机
    // 基本都是 arm64，x86 安卓设备只剩模拟器。模拟器里猜错也无所谓，展开完整列表能改选。
    if (os === "android") {
        return "arm64-v8a";
    }

    // macOS 的 UA 无论 Intel 还是 Apple 芯片都写 "Intel Mac OS X"，必须先看 GPU，
    // 否则会把所有 Apple 芯片的 Mac 判成 x86_64。
    if (os === "macos") {
        const gpu = gpuRenderer().toLowerCase();
        if (gpu.includes("apple")) return "aarch64";
        if (/intel|amd|radeon|nvidia|geforce/.test(gpu)) return "x86_64";
        // 都判不出来时按 Apple 芯片猜：2020 年之后出的 Mac 基本都是 ARM。
        return "aarch64";
    }

    const s = ua.toLowerCase();
    if (/arm64|aarch64|armv8|win arm/.test(s)) return "aarch64";
    if (/x86_64|x64|win64|wow64/.test(s)) return "x86_64";

    // Windows / Linux 的 UA 没写架构时按当前主流架构猜；卡片上会写明识别结果，
    // 下方完整列表始终可以手动改选。
    return "x86_64";
}

async function detectDevice() {
    const nav = navigator as Navigator & {userAgentData?: UaData};
    const uaData = nav.userAgentData;
    const platform = uaData?.platform || nav.platform || "";
    const ua = nav.userAgent ?? "";
    const os = detectOs(platform, ua, nav.maxTouchPoints ?? 0, Boolean(uaData));
    if (!os) return;
    detected.value = {os, arch: await detectArch(os, ua, uaData)};
}

onMounted(() => {
    void detectDevice();
});

function mb(bytes: number): string {
    return (bytes / 1048576).toFixed(1) + " MB";
}
</script>

<template>
    <section id="quick-download" class="home-download">
        <div class="container">
            <h2 v-if="title" class="title">{{ title }}</h2>

            <p v-if="available" class="meta">
                <span>{{ t.version }}</span>
                <code class="version">{{ release.version }}</code>
                <span class="dot">·</span>
                <span>{{ t.published }} {{ release.publishedAt.slice(0, 10) }}</span>
                <span class="dot">·</span>
                <a :href="release.releasePage" target="_blank" rel="noopener noreferrer">{{ t.allVersions }}</a>
                <span class="dot">·</span>
                <a
                    class="mirror"
                    href="https://mirrorchyan.com/zh/projects?rid=MaaKEDR&source=maakedr-release"
                    target="_blank"
                    rel="noopener noreferrer"
                    ><VPIcon name="ri:rocket-2-line" :size="14" />{{ t.mirror }}</a
                >
            </p>

            <p v-else class="meta">
                <span>{{ t.unavailable }}</span>
                <a href="https://github.com/APPLe-DF/MaaKEDR/releases" target="_blank" rel="noopener noreferrer"
                    >Releases</a
                >
                <span>{{ t.unavailableTail }}</span>
            </p>

            <!-- MFAA/MXU 的说明只对桌面包成立，安卓端只有一个壳，不该跟着出现。 -->
            <p v-if="available && !hideUiHint" class="hint">{{ t.hint }}</p>

            <!-- 识别成功时只留一张匹配卡，其他架构收进下面的小入口；
                 识别不出来（手机/平板/JS 未运行）时整块消失，直接回退成完整列表。 -->
            <div v-if="available && recommended" class="picked">
                <p class="picked-head">
                    <VPIcon name="ri:computer-line" :size="18" />
                    <span>{{ t.pickedTitle }}</span>
                    <span class="picked-device">{{ deviceLabel }}</span>
                </p>

                <div class="picked-body">
                    <div v-if="showUiChoice" class="picked-ui" role="group" :aria-label="t.uiLabel">
                        <button
                            v-for="ui in UI_OPTIONS"
                            :key="ui"
                            type="button"
                            class="picked-ui-btn"
                            :class="{active: uiChoice === ui}"
                            :aria-pressed="uiChoice === ui"
                            @click="uiChoice = ui">
                            {{ ui }}
                        </button>
                    </div>

                    <a class="picked-dl" :href="recommended.url" target="_blank" rel="noopener noreferrer">
                        <VPIcon name="ri:download-2-line" :size="18" />
                        <span class="picked-dl-text">
                            {{ recommended.ui ? t.download + " " + recommended.ui : t.downloadApk }}
                        </span>
                        <span class="picked-dl-size">{{ mb(recommended.size) }}</span>
                    </a>
                </div>
            </div>

            <!-- 识别成功时，其他平台收成一行入口，放在卡片外面：
                 它比匹配卡窄、居中，是"还有别的包"的附属入口，不该占据列表的位置。 -->
            <details v-if="available && recommended" class="others">
                <summary class="others-toggle">
                    <VPIcon name="ri:apps-2-line" :size="16" />
                    <span>{{ t.otherTitle }}</span>
                    <span class="others-hint">{{ t.otherHint }}</span>
                </summary>

                <div class="others-body">
                    <div v-for="group in groups" :key="group.os" class="group">
                        <p class="group-head">
                            <VPIcon :name="group.icon" :size="20" />
                            <span>{{ group.label }}</span>
                        </p>

                        <div v-for="row in group.rows" :key="row.arch" class="arch">
                            <p class="arch-label">{{ row.label }}</p>
                            <div class="opts">
                                <a
                                    v-for="asset in row.uis"
                                    :key="asset.name"
                                    class="dl"
                                    :href="asset.url"
                                    target="_blank"
                                    rel="noopener noreferrer">
                                    <span class="ui">{{ asset.ui || t.apk }}</span>
                                    <span class="size">{{ mb(asset.size) }}</span>
                                    <span v-if="isPicked(asset)" class="picked-mark" :title="t.pickedTitle">
                                        <VPIcon name="ri:check-line" :size="14" />
                                    </span>
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </details>

            <!-- 完整三平台列表：识别失败时是唯一出口；识别成功时收在上面那个 details 里。 -->
            <div v-if="available && !recommended" class="grid">
                <div v-for="group in groups" :key="group.os" class="group">
                    <p class="group-head">
                        <VPIcon :name="group.icon" :size="20" />
                        <span>{{ group.label }}</span>
                    </p>

                    <div v-for="row in group.rows" :key="row.arch" class="arch">
                        <p class="arch-label">{{ row.label }}</p>
                        <div class="opts">
                            <a
                                v-for="asset in row.uis"
                                :key="asset.name"
                                class="dl"
                                :href="asset.url"
                                target="_blank"
                                rel="noopener noreferrer">
                                <span class="ui">{{ asset.ui || t.apk }}</span>
                                <span class="size">{{ mb(asset.size) }}</span>
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>
</template>

<style scoped>
/* 与主题 VPHomeBox 的内边距/内容宽度保持一致，否则各区块的左右边界对不齐。 */
.home-download {
    padding: 24px;
}

@media (min-width: 640px) {
    .home-download {
        padding: 32px 48px;
    }
}

@media (min-width: 960px) {
    .home-download {
        padding: 48px;
    }
}

.container {
    width: 100%;
    max-width: 1152px;
    margin: 0 auto;
}

.title {
    margin-bottom: 20px;
    font-size: 20px;
    font-weight: 900;
    color: var(--vp-c-text-1);
    text-align: center;
}

.meta {
    margin-bottom: 6px;
    font-size: 14px;
    line-height: 24px;
    color: var(--vp-c-text-2);
    text-align: center;
}

.hint {
    margin-bottom: 24px;
    font-size: 13px;
    line-height: 22px;
    color: var(--vp-c-text-3);
    text-align: center;
}

.dot {
    margin: 0 6px;
    color: var(--vp-c-text-3);
}

.version {
    margin: 0 2px;
    font-size: 13px;
    color: var(--vp-c-brand-1);
}

/* Mirror酱是这条 meta 里唯一的“另一条获取途径”，做成胶囊才不会被看成又一个普通链接。
   配色沿用主题 hero 主按钮的 brand-soft → brand-1 过渡。 */
.mirror {
    position: relative;
    display: inline-flex;
    overflow: hidden;
    gap: 4px;
    align-items: center;
    padding: 1px 8px;
    font-size: 13px;
    font-weight: 600;
    color: var(--vp-c-brand-1);
    text-decoration: none;
    background-color: var(--vp-c-brand-soft);
    border-radius: 999px;
    /* 胶囊自己是 overflow: hidden 的（扫光要用），但 box-shadow 画在本元素的 border-box 外，
       不会被自己的 overflow 裁掉，所以这里能直接给它一圈常态光晕。
       呼吸动画留给 hero 那颗主按钮，一页两个脉动就开始抢注意力了。 */
    box-shadow: 0 0 14px -2px color-mix(in srgb, var(--vp-c-brand-1) 55%, transparent);
    transition:
        color var(--vp-t-color),
        background-color var(--vp-t-color),
        box-shadow var(--vp-t-color);
}

.mirror:hover {
    color: var(--vp-c-white);
    background-color: var(--vp-c-brand-1);
    box-shadow: 0 0 20px 1px color-mix(in srgb, var(--vp-c-brand-1) 75%, transparent);
}

/* 胶囊是这块唯一的高亮入口，hover 时扫一道斜光，把它和普通文本链接区分开。
   平移用 transform 而不是移 background-position，重绘只发生在这一小块里。
   只在 hover 时跑，是为了不再给整页添第三个常驻动画。 */
.mirror::after {
    content: "";
    position: absolute;
    top: -30%;
    left: -45%;
    width: 40%;
    height: 160%;
    pointer-events: none;
    background: linear-gradient(105deg, transparent, rgb(255 255 255 / 0.6), transparent);
    opacity: 0;
    transform: rotate(14deg);
}

.mirror:hover::after {
    animation: mirror-sheen 0.9s ease-out;
}

@keyframes mirror-sheen {
    0% {
        opacity: 0;
        transform: rotate(14deg) translateX(0);
    }

    18% {
        opacity: 1;
    }

    100% {
        opacity: 0;
        transform: rotate(14deg) translateX(340%);
    }
}

.grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 16px;
}

.group {
    padding: 18px 20px 20px;
    /* 和首页卡片共用 home-hero.css 里那组玻璃变量，触屏/高对比模式由那边一次性退回实色。 */
    background-color: var(--vp-home-glass-bg);
    border: 1px solid var(--vp-home-glass-edge);
    border-radius: 12px;
    box-shadow: var(--vp-home-glass-spec);
    -webkit-backdrop-filter: var(--vp-home-glass-blur);
    backdrop-filter: var(--vp-home-glass-blur);
    transition: background-color var(--vp-t-color);
}

.group-head {
    display: flex;
    gap: 8px;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 12px;
    font-size: 16px;
    font-weight: 600;
    color: var(--vp-c-text-1);
    border-bottom: 1px solid var(--vp-c-divider);
}

.arch + .arch {
    margin-top: 14px;
}

.arch-label {
    margin-bottom: 6px;
    font-size: 12px;
    font-weight: 600;
    color: var(--vp-c-text-3);
}

/* 只出单个界面的架构（Linux ARM64）会自动占满整行。 */
.opts {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(118px, 1fr));
    gap: 8px;
}

.dl {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 6px;
    padding: 9px 10px;
    color: var(--vp-c-text-1);
    text-decoration: none;
    background-color: var(--vp-c-bg);
    border: 1px solid var(--vp-c-divider);
    border-radius: 8px;
    transition:
        color var(--vp-t-color),
        border-color var(--vp-t-color),
        transform 0.18s ease,
        box-shadow 0.18s ease;
}

.dl:hover,
.dl:focus-visible {
    color: var(--vp-c-brand-1);
    border-color: var(--vp-c-brand-1);
    outline: none;
    transform: translateY(-1px);
    /* 掺主色的光晕，浏览器不认 color-mix 时整行被忽略，只剩描边变化。 */
    box-shadow: 0 0 16px -4px color-mix(in srgb, var(--vp-c-brand-1) 80%, transparent);
}

.dl:active {
    transform: translateY(0) scale(0.99);
}

.ui {
    font-size: 14px;
    font-weight: 600;
    white-space: nowrap;
}

.size {
    /* 窄屏上加了勾选图标后这一行会被挤到换行，"168.4 MB" 折成两行很难看；
       禁止在数字和单位之间断行，同时允许整行在极端窄的屏上省略。 */
    font-size: 12px;
    color: var(--vp-c-text-3);
    white-space: nowrap;
}

/* 推荐下载卡：设备识别成功后出现。材质沿用首页统一的玻璃变量
   （--vp-home-glass-* 定义在 home-hero.css，触屏/高对比模式在那里一次性退回实色），
   所以它和下面的分组卡是同一块料，不会像第一版那样实心发白、突兀地浮在页面上。 */
.picked {
    max-width: 560px;
    margin: 0 auto 12px;
    padding: 16px 20px;
    background-color: var(--vp-home-glass-bg);
    border: 1px solid var(--vp-home-glass-edge);
    border-radius: 12px;
    box-shadow:
        var(--vp-home-glass-spec),
        0 0 24px -16px color-mix(in srgb, var(--vp-c-brand-1) 80%, transparent);
    -webkit-backdrop-filter: var(--vp-home-glass-blur);
    backdrop-filter: var(--vp-home-glass-blur);
}

.picked-head {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
    margin-bottom: 12px;
    font-size: 13px;
    font-weight: 600;
    color: var(--vp-c-text-2);
}

/* 识别出来的系统 / 架构用等宽字体，读起来像一条检测结果而不是正文。 */
.picked-device {
    padding: 1px 8px;
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 12px;
    color: var(--vp-c-brand-1);
    background-color: var(--vp-c-brand-soft);
    border-radius: 999px;
}

.picked-body {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: stretch;
}

/* 界面版本切换：两颗按钮，默认 MFAA。用真正的 button 而不是 span，
   键盘和读屏都能操作，aria-pressed 让状态可被读出来。 */
.picked-ui {
    display: flex;
    gap: 4px;
    padding: 3px;
    background-color: var(--vp-home-glass-btn);
    border: 1px solid var(--vp-home-glass-edge);
    border-radius: 8px;
}

.picked-ui-btn {
    padding: 5px 12px;
    font-size: 13px;
    font-weight: 600;
    color: var(--vp-c-text-2);
    cursor: pointer;
    background-color: transparent;
    border: 0;
    border-radius: 6px;
    transition:
        color var(--vp-t-color),
        background-color var(--vp-t-color);
}

.picked-ui-btn:hover {
    color: var(--vp-c-text-1);
}

.picked-ui-btn.active {
    color: var(--vp-c-brand-1);
    background-color: var(--vp-c-bg);
    box-shadow: 0 1px 3px rgb(0 0 0 / 0.1);
}

.picked-dl {
    display: inline-flex;
    flex: 1;
    gap: 8px;
    align-items: center;
    justify-content: center;
    min-width: 180px;
    padding: 9px 16px;
    font-size: 14px;
    font-weight: 600;
    color: var(--vp-c-white);
    text-decoration: none;
    background-color: var(--vp-c-brand-1);
    border-radius: 8px;
    transition:
        background-color var(--vp-t-color),
        transform 0.18s ease,
        box-shadow 0.18s ease;
}

.picked-dl:hover,
.picked-dl:focus-visible {
    color: var(--vp-c-white);
    background-color: var(--vp-c-brand-2);
    outline: none;
    transform: translateY(-1px);
    box-shadow: 0 6px 18px -8px color-mix(in srgb, var(--vp-c-brand-1) 90%, transparent);
}

.picked-dl:active {
    transform: translateY(0) scale(0.99);
}

.picked-dl-text {
    flex: 1;
    text-align: center;
}

.picked-dl-size {
    font-size: 12px;
    font-weight: 500;
    opacity: 0.8;
}

/* 其他平台入口：收成一行，和匹配卡同样宽度对齐，视觉上是一个"折叠尾巴"。
   details/summary 自带展开语义和键盘行为，不需要自己维护 aria-expanded。
   注意 .grid 是 grid 容器，子项默认 stretch 到整列，所以这里用 justify-self: center
   把 details 自己收窄居中——光给内部 summary 加 max-width/margin:auto 不管用，
   因为 details 本身已经是整列宽了。 */
/* 入口是 .container 的直接子元素（不在 .grid 里），所以它的宽度由自己控制：
   收起时和匹配卡同宽（560px）居中，展开后铺满整行放三列卡片。 */
.others {
    width: 100%;
    max-width: 1152px;
    margin: 0 auto;
}

.others:not([open]) {
    max-width: 560px;
    margin-bottom: 12px;
}

.others-toggle {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
    justify-content: center;
    padding: 10px 16px;
    font-size: 13px;
    font-weight: 600;
    color: var(--vp-c-text-2);
    cursor: pointer;
    list-style: none;
    background-color: var(--vp-home-glass-bg);
    border: 1px solid var(--vp-home-glass-edge);
    border-radius: 12px;
    box-shadow: var(--vp-home-glass-spec);
    -webkit-backdrop-filter: var(--vp-home-glass-blur);
    backdrop-filter: var(--vp-home-glass-blur);
    transition:
        color var(--vp-t-color),
        border-color var(--vp-t-color),
        background-color var(--vp-t-color);
}

/* 去掉浏览器默认的三角标记，用图标 + 旋转箭头表达展开状态。 */
.others-toggle::-webkit-details-marker {
    display: none;
}

.others-toggle:hover {
    color: var(--vp-c-brand-1);
    border-color: var(--vp-c-brand-1);
}

.others-toggle:focus-visible {
    outline: 2px solid var(--vp-c-brand-1);
    outline-offset: 2px;
}

.others-hint {
    font-weight: 500;
    color: var(--vp-c-text-3);
}

/* 展开后列表从入口下方展开：details[open] 时才出现内容，动画只做淡入上浮，
   不做高度过渡（高度 auto 无法过渡，硬做要 JS 量尺寸，不值当）。 */
.others[open] .others-toggle {
    max-width: 560px;
    margin: 0 auto 16px;
    border-color: color-mix(in srgb, var(--vp-c-brand-1) 45%, transparent);
}

.others-body {
    display: grid;
    grid-template-columns: 1fr;
    gap: 16px;
    width: 100%;
    padding-top: 4px;
}

@media (prefers-reduced-motion: no-preference) {
    .others[open] .others-body {
        animation: others-fade 0.28s ease-out;
    }
}

@keyframes others-fade {
    from {
        opacity: 0;
        transform: translateY(-6px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* 完整列表里把推荐项标出来：和上面的卡片呼应，用户改选后标记会跟着走。 */
.picked-mark {
    display: inline-flex;
    flex-shrink: 0;
    align-items: center;
    color: var(--vp-c-brand-1);
}

/* 768 起就三列，和主题 features 区块在同一断点变成三列，避免出现通栏的第四行卡片；
   此时单卡约 213px，.opts 会自动退成单列，到 960px 卡片变宽后再并排。
   .others-body 是展开后的同一份列表，断点必须和 .grid 保持一致，否则展开会变成一长条。 */
@media (min-width: 768px) {
    .grid,
    .others-body {
        grid-template-columns: repeat(3, 1fr);
    }

    .title {
        font-size: 24px;
    }
}

@media (min-width: 960px) {
    .title {
        font-size: 28px;
    }
}
</style>
