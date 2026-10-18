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
/**
 * arch 为 "unknown" 表示浏览器没给出可信的架构信息（Safari / Firefox 的 macOS 就是这样）。
 * 这时不去猜：猜错会让用户下到一个跑不起来的包，宁可把选择权交回去。
 */
type Detected = {os: Os; arch: Arch | "unknown"};

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
        crossArch: "该构建与当前系统架构不一致，可能无法运行。如装不上，请展开下方列表选择对应架构。",
        missingArch: "这个版本没有发布适配你当前架构的安装包。请展开下方列表，选择其他架构的包。",
        macHint: "无法自动识别 Mac 芯片类型。在「关于本机」中查看芯片，或点下面任一项：",
        macArm: "下载 Apple 芯片版",
        macIntel: "下载 Intel 芯片版",
        unknownArch: "未能识别架构，已按兼容性推荐",
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
        crossArch:
            "This build does not match your architecture and may not run. If it fails, open the list below and pick the right one.",
        missingArch:
            "This release has no build for your architecture. Open the list below to pick another architecture.",
        macHint: "Could not detect your Mac chip type. Check “About This Mac”, or pick one below:",
        macArm: "Download Apple silicon",
        macIntel: "Download Intel",
        unknownArch: "Architecture not detected — showing the most compatible build",
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

/**
 * 按平台分组。**过滤掉没有资产的分组**——否则当前版本还没发 APK 时，
 * 展开「其他平台与架构」会看到一个只有标题、没有任何下载项的 Android 空卡片。
 * （v1.5.6 就是这种情况，截图里能直接看到那个空块。）
 */
const groups = GROUPS.map((group) => ({
    ...group,
    rows: [...new Set(assets.filter((a) => a.os === group.os).map((a) => a.arch))].map((arch) => ({
        arch,
        label: ARCH_LABEL[arch] ?? arch,
        uis: assets.filter((a) => a.os === group.os && a.arch === arch),
    })),
})).filter((group) => group.rows.length > 0);

/**
 * 设备识别结果只在挂载后写入：SSR 阶段 detected 是 null，服务端和客户端首帧都渲染
 * 同一份完整列表，不会产生 hydration 失配；JS 没跑时页面就是原来的完整列表。
 */
const detected = ref<Detected | null>(null);
// 界面版本默认 MFAA；用户切到 MXU 后推荐项跟着换。
// 若当前架构没有 MFAA（极端情况），recommended 的兜底会选中实际存在的那个。
const uiChoice = ref<Asset["ui"]>("MFAA");

const deviceLabel = computed(() => {
    const d = detected.value;
    if (!d) return "";
    // 架构未知时只显示系统名，不写 "unknown" 这种给用户看没有意义的东西。
    if (d.arch === "unknown") return OS_LABEL[d.os];
    return OS_LABEL[d.os] + " / " + (ARCH_LABEL[d.arch] ?? d.arch);
});

/**
 * 桌面推荐项：优先「同系统 + 同架构 + 当前界面版本」，
 * 再退到「同系统 + 同架构」（该架构没有所选界面时，例如 Linux ARM64 只有 MFAA）。
 *
 * **绝不跨架构回退**：上游并没有 Linux aarch64 的 MXU 构建，硬回退会让 ARM 用户
 * 拿到跑不起来的 x64 包。同架构里一个都没有时返回 null，让 UI 去问用户。
 * 架构未知（unknown）时也返回 null —— 选择权交回去，不替用户猜。
 */
const recommended = computed<Asset | null>(() => {
    const d = detected.value;
    if (!d || d.arch === "unknown") return null;
    const sameOs = assets.filter((a) => a.os === d.os);
    if (!sameOs.length) return null;

    // 安卓只有 ABI 之分，没有界面版本；universal 能覆盖所有设备，放在架构匹配之后。
    if (d.os === "android") {
        const exact = sameOs.find((a) => a.arch === d.arch);
        if (exact) return exact;
        // 该 ABI 没出包时退到 universal（两个 ABI 都含），再退到 arm64 —— 市面上
        // 绝大多数是 arm64，x86 安卓设备基本只剩模拟器。
        return sameOs.find((a) => a.arch === "universal") ?? sameOs.find((a) => a.arch === "arm64-v8a") ?? null;
    }

    return (
        sameOs.find((a) => a.arch === d.arch && a.ui === uiChoice.value) ??
        sameOs.find((a) => a.arch === d.arch) ??
        null
    );
});

/**
 * 安卓设备识别不出 ABI（真机 UA 不写架构）时，仍然可以按覆盖面推荐一版：
 * arm64-v8a → universal → 第一个。这与 M9A 的策略一致，绝大多数手机都能装。
 * 桌面不走这条路——桌面上按错架构的包是直接跑不起来的。
 */
const recommendedApk = computed<Asset | null>(() => {
    const d = detected.value;
    if (d?.os !== "android") return null;
    const apks = assets.filter((a) => a.os === "android");
    if (!apks.length) return null;
    // 已有精确匹配时交给 recommended，这里不重复推荐。
    if (recommended.value?.os === "android") return null;
    return apks.find((a) => a.arch === "arm64-v8a") ?? apks.find((a) => a.arch === "universal") ?? apks[0] ?? null;
});

/** 实际上是"当前要展示的那一个推荐包"，安卓未知 ABI 时走覆盖面兜底。 */
const primary = computed<Asset | null>(() => recommended.value ?? recommendedApk.value);

/** 安卓 ABI 未知：走覆盖面兜底，UI 上标注一句"未能识别架构"。 */
const crossArchUnknown = computed(
    () => detected.value?.os === "android" && detected.value.arch === "unknown" && recommendedApk.value !== null,
);

/**
 * 当前平台/架构下可选的界面版本。
 *
 * 从实际资产推导，而不是写死 ["MFAA","MXU"]：上游某些版本的 macOS ARM64 只发
 * MFAA（没有 MXU），写死的话切到 MXU 会让按钮静默消失，界面上没有任何解释。
 */
const availableUis = computed<Asset["ui"][]>(() => {
    const d = detected.value;
    if (!d || d.os === "android" || d.arch === "unknown") return [];
    const uis = assets.filter((a) => a.os === d.os && a.arch === d.arch && a.ui !== "").map((a) => a.ui as Asset["ui"]);
    return UI_OPTIONS.filter((ui) => uis.includes(ui));
});

/**
 * 是否显示界面版本切换。
 * 安卓端只有一个壳，MFAA/MXU 之分不成立；架构未知时不知道该比哪些包；
 * 只有当前架构真的存在两个界面版本时才值得给切换控件。
 */
const showUiChoice = computed(() => availableUis.value.length > 1);

/**
 * 是否隐藏「MFAA 与 MXU 只有界面外观的区别」这句说明。
 * 安卓设备被推荐的是 APK，说明和他的选择无关；整份 release 里没有桌面包时
 * 更是无稽之谈。识别失败、尚未挂载时 detected 为 null，此时保留说明——
 * 完整列表里确实有 MFAA/MXU 两列。
 */
const hideUiHint = computed(() => {
    const d = detected.value;
    if (!d) return assets.length > 0 && assets.every((a) => a.os === "android");
    return d.os === "android";
});

/**
 * 桌面端"本机架构没有对应包"的情况。
 *
 * 桌面刻意不跨架构回退（见 recommended），所以当某个平台上没有本机架构的构建时，
 * primary 是 null，推荐卡不出现——用户看到的是完整列表，但**不知道原因**。
 * 这里把原因说明出来，而不是静默退回：
 *   例：Linux ARM64 用户碰上只发了 x86_64 的版本。
 * 安卓不走这条（它有自己的覆盖面兜底）。
 */
const missingArch = computed(() => {
    const d = detected.value;
    if (!d || d.os === "android" || d.arch === "unknown") return null;
    // macOS 架构未知时走 needsArchChoice 的双按钮，不走这条。
    if (needsArchChoice.value) return null;
    const sameOs = assets.filter((a) => a.os === d.os);
    // 整个平台都没包时不算"架构缺失"——那是 release 数据不全，交给完整列表/占位文案。
    if (!sameOs.length) return null;
    if (sameOs.some((a) => a.arch === d.arch)) return null;
    return {os: d.os, arch: d.arch};
});

/**
 * 推荐卡是否该出现。macOS 架构未知时没有"唯一正确包"，但仍要展示两颗按钮；
 * 安卓 ABI 未知时也要展示覆盖面推荐；其余情况看 primary 是否非空。
 */
const showCard = computed(
    () => available && (primary.value !== null || needsArchChoice.value || missingArch.value !== null),
);

/**
 * 跨架构提示：只在本机架构已知、且与将要下载的包不一致时出现。
 * 说清楚"可能跑不起来"，比让用户装完才发现好。
 */
const crossArch = computed(() => {
    const d = detected.value;
    const pick = primary.value;
    if (!d || d.arch === "unknown" || !pick) return false;
    // universal 包同时含两个 ABI，装在哪都不会错。
    if (pick.arch === "universal") return false;
    return pick.arch !== d.arch;
});

/** macOS 识别不出芯片时，给两颗按钮让用户自己选，而不是猜一个可能是错的。 */
const needsArchChoice = computed(() => detected.value?.os === "macos" && detected.value.arch === "unknown");
const macArmBuild = computed(() =>
    assets.find((a) => a.os === "macos" && a.arch === "aarch64" && a.ui === uiChoice.value),
);
const macIntelBuild = computed(() =>
    assets.find((a) => a.os === "macos" && a.arch === "x86_64" && a.ui === uiChoice.value),
);

function isPicked(asset: Asset): boolean {
    return primary.value?.name === asset.name;
}

type UaData = {
    platform?: string;
    getHighEntropyValues?: (hints: string[]) => Promise<{architecture?: string; bitness?: string; platform?: string}>;
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

/**
 * 判断架构。拿不到可信信息时返回 "unknown"，**不做猜测**。
 *
 * 取舍：猜对的收益只是省一次点击，猜错的代价是让用户下到一个装不上/跑不起来的包。
 * 所以这里只在有确凿证据（高熵提示、UA 里明确写出的架构、macOS 的 GPU 名）时才表态。
 */
async function detectArch(os: Os, ua: string, uaData?: UaData): Promise<Arch | "unknown"> {
    // 1. Chromium 的高熵提示最可靠：Windows ARM64 的 UA 依然写 x64，只有这里能拆穿。
    const hint = await highEntropyArch(uaData);
    if (hint) {
        if (os === "android") return hint === "aarch64" ? "arm64-v8a" : "x86_64";
        return hint;
    }

    // 2. 安卓：UA 里通常能看出模拟器的 ABI（"sdk_gphone64_x86_64"、
    //    "Android SDK built for x86_64"）。真机 UA 一般不写架构，那就不表态——
    //    交给推荐逻辑按覆盖面选 ARM64 包（见 preferredApk）。
    if (os === "android") {
        const s = ua.toLowerCase();
        if (/x86_64|x86|intel/.test(s)) return "x86_64";
        if (/arm64|aarch64|armv8/.test(s)) return "arm64-v8a";
        return "unknown";
    }

    // 3. macOS：UA 无论 Intel 还是 Apple 芯片都写 "Intel Mac OS X"，只能靠 GPU。
    //    GPU 名也拿不到（隐私模式、驱动屏蔽）时返回 unknown，由 UI 给出两颗按钮。
    //
    //    顺序很关键：**先认 Intel/AMD，再认 Apple**。
    //    Chrome 在 macOS 上的渲染器字符串是 "ANGLE (Apple, ANGLE Metal Renderer: <真实GPU>)"
    //    —— 前缀恒为 Apple（那是 ANGLE 的后端名），真正的芯片名在后半段。
    //    Intel Mac 上这个字符串同时含 "apple" 和 "intel"，先匹配 apple 会把
    //    Intel 机器判成 Apple 芯片，用户就会下到一个装不上的 ARM 包。
    if (os === "macos") {
        const gpu = gpuRenderer().toLowerCase();
        // Intel / AMD / N 卡：明确是 x86 机器。
        if (/intel|amd|radeon|nvidia|geforce/.test(gpu)) return "x86_64";
        // 只有拿不到具体型号、或明确写着 Apple M 系列时，才认为是 Apple 芯片。
        if (gpu.includes("apple")) return "aarch64";
        return "unknown";
    }

    // 4. Windows / Linux：UA 里显式写了架构才采信。
    //    注意 Windows 的 UA 恒为 "Win64; x64"（Windows on ARM 也一样），
    //    但 x64 包在 ARM Windows 上能靠模拟运行，属于安全默认值。
    const s = ua.toLowerCase();
    if (/arm64|aarch64|armv8|win arm/.test(s)) return "aarch64";
    if (/x86_64|x64|win64|wow64/.test(s)) return "x86_64";

    return "unknown";
}

/** 读高熵提示里的 architecture；浏览器拒绝或超时都返回 null。 */
async function highEntropyArch(uaData?: UaData): Promise<Arch | null> {
    if (!uaData?.getHighEntropyValues) return null;
    try {
        const v = await uaData.getHighEntropyValues([
            "architecture",
            "bitness",
            "platform",
        ]);
        // 32 位设备（armeabi-v7a / x86）装不了 arm64-v8a 或 x64 包。
        // 这里返回 null 让调用方走"未知"路径：安卓侧交给覆盖面兜底并标注
        // 「未能识别架构」，桌面侧交给 macOS 双按钮或完整列表，都不至于硬塞一个装不上的包。
        if (v.bitness === "32") return null;
        if (v.architecture === "arm") return "aarch64";
        if (v.architecture === "x86") return "x86_64";
    } catch {
        // 有的浏览器暴露了 userAgentData 却拒绝高熵提示，退回 UA 判断。
    }
    return null;
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

            <!-- 推荐卡：多数情况下只展示一张匹配当前设备的包，其余收进下面的小入口。
                 三种形态：
                   1. 普通情况  —— 一颗下载按钮
                   2. macOS 架构未知 —— 两颗按钮让用户自己选（猜错等于给一个跑不起来的包）
                   3. 安卓 ABI 未知 —— 按覆盖面推荐 arm64，并标注"未能识别架构"
                 识别不出来（iOS、JS 未运行）时整块不渲染，直接回退完整列表。 -->
            <div v-if="showCard" class="picked">
                <p class="picked-head">
                    <VPIcon name="ri:computer-line" :size="18" />
                    <span>{{ t.pickedTitle }}</span>
                    <span class="picked-device">{{ deviceLabel }}</span>
                </p>

                <div class="picked-body">
                    <div
                        v-if="showUiChoice && (primary || needsArchChoice)"
                        class="picked-ui"
                        role="group"
                        :aria-label="t.uiLabel">
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

                    <!-- macOS 芯片未知：并排两颗，不预设哪一个是"对"的。 -->
                    <template v-if="needsArchChoice">
                        <a
                            v-if="macArmBuild"
                            class="picked-dl"
                            :href="macArmBuild.url"
                            target="_blank"
                            rel="noopener noreferrer">
                            <VPIcon name="ri:download-2-line" :size="18" />
                            <span class="picked-dl-text">{{ t.macArm }}</span>
                            <span class="picked-dl-size">{{ mb(macArmBuild.size) }}</span>
                        </a>
                        <a
                            v-if="macIntelBuild"
                            class="picked-dl picked-dl-quiet"
                            :href="macIntelBuild.url"
                            target="_blank"
                            rel="noopener noreferrer">
                            <VPIcon name="ri:download-2-line" :size="18" />
                            <span class="picked-dl-text">{{ t.macIntel }}</span>
                            <span class="picked-dl-size">{{ mb(macIntelBuild.size) }}</span>
                        </a>
                    </template>

                    <!-- primary 可能为 null：桌面端本机架构没有对应包时，卡片只负责
                         说明原因（走上面的 missingArch 提示），不提供下载按钮。 -->
                    <a
                        v-else-if="primary"
                        class="picked-dl"
                        :href="primary.url"
                        target="_blank"
                        rel="noopener noreferrer">
                        <VPIcon name="ri:download-2-line" :size="18" />
                        <span class="picked-dl-text">
                            {{ primary.ui ? t.download + " " + primary.ui : t.downloadApk }}
                        </span>
                        <span class="picked-dl-size">{{ mb(primary.size) }}</span>
                    </a>
                </div>

                <!-- 三条提示互斥：macOS 先告诉用户怎么选；架构不匹配给警告；
                     桌面端本机架构没有对应包时说明原因（而不是静默退回列表）。 -->
                <p v-if="needsArchChoice" class="picked-note">{{ t.macHint }}</p>
                <p v-else-if="missingArch" class="picked-note picked-note-warn">
                    <VPIcon name="ri:error-warning-line" :size="14" />
                    <span>{{ t.missingArch }}</span>
                </p>
                <p v-else-if="crossArch" class="picked-note picked-note-warn">
                    <VPIcon name="ri:error-warning-line" :size="14" />
                    <span>{{ t.crossArch }}</span>
                </p>
                <p v-else-if="crossArchUnknown" class="picked-note">{{ t.unknownArch }}</p>
            </div>

            <!-- 识别成功时，其他平台收成一行入口，放在卡片外面：
                 它比匹配卡窄、居中，是"还有别的包"的附属入口，不该占据列表的位置。 -->
            <details v-if="available && showCard" class="others">
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
            <div v-if="available && !showCard" class="grid">
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

/* 推荐卡的主 CTA。光效分两层，和首页 hero 那颗主按钮的语义对齐：
     常态 —— 一圈柔和的静态光晕（"这是主入口"）
     hover —— 光晕增强 + 抬升（"你正要点它"）
   第一版只写了 hover 的投影，常态什么都没有；加上按钮本身底色就深，
   看起来就像"默认已经很亮，移上去反而变暗"。光晕用两层 box-shadow：
   贴边一层保证在任何背景上都能看出边界，外扩一层负责氛围。 */
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
    box-shadow:
        0 0 0 1px color-mix(in srgb, var(--vp-c-brand-2) 45%, transparent),
        0 4px 14px -6px color-mix(in srgb, var(--vp-c-brand-1) 55%, transparent);
    transition:
        background-color var(--vp-t-color),
        transform 0.18s ease,
        box-shadow 0.25s ease;
}

.picked-dl:hover,
.picked-dl:focus-visible {
    color: var(--vp-c-white);
    background-color: var(--vp-c-brand-2);
    outline: none;
    transform: translateY(-1px);
    /* hover 时两层都加强：描边更实、外扩光晕更大更亮，位移同时发生，
       三个变化叠起来就是"被点亮"，而不是"变暗"。 */
    box-shadow:
        0 0 0 1px color-mix(in srgb, var(--vp-c-brand-2) 75%, transparent),
        0 8px 24px -8px color-mix(in srgb, var(--vp-c-brand-1) 85%, transparent);
}

.picked-dl:active {
    transform: translateY(0) scale(0.99);
}

/* 深色主题下 --vp-c-brand-1 是浅粉（#f9a8d4），白字压在上面对比度只有 1.7:1，
   几乎看不清，所以改用深色字。
   hover 不能跟着换 brand-2/brand-3 —— 那两个在深色主题里更深，深色字会一起失效；
   统一往白里掺 12%，越 hover 越亮，方向感和浅色主题一致。 */
html[data-theme="dark"] .picked-dl {
    color: var(--vp-c-black);
}

html[data-theme="dark"] .picked-dl:hover,
html[data-theme="dark"] .picked-dl:focus-visible {
    color: var(--vp-c-black);
    background-color: color-mix(in srgb, var(--vp-c-brand-1) 88%, var(--vp-c-white));
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

/* macOS 架构未知时的第二颗按钮：它是"另一个可能"，不该和主推荐抢注意力。 */
/* macOS 架构未知时的第二颗按钮：它是"另一个可能"，不该和主推荐抢注意力，
   所以常态完全去掉光晕，只保留玻璃底 + 描边。 */
.picked-dl-quiet {
    color: var(--vp-c-text-1);
    background-color: var(--vp-home-glass-btn);
    border: 1px solid var(--vp-home-glass-edge);
    box-shadow: none;
}

.picked-dl-quiet:hover,
.picked-dl-quiet:focus-visible {
    color: var(--vp-c-brand-1);
    background-color: var(--vp-home-glass-btn-hover);
    box-shadow: 0 4px 14px -8px color-mix(in srgb, var(--vp-c-brand-1) 55%, transparent);
}

.picked-note {
    margin-top: 10px;
    font-size: 12px;
    line-height: 18px;
    color: var(--vp-c-text-3);
}

/* 跨架构提醒：用警示色，但保持小字，不喧宾夺主。
   必须写在 .picked-note 之后 —— 两者特异性同为 (0,1,0)，靠源码顺序决定胜负，
   放在前面的话 color 会被 .picked-note 的 --vp-c-text-3 覆盖掉，只剩图标是警示色。 */
.picked-note-warn {
    display: flex;
    gap: 6px;
    align-items: flex-start;
    color: var(--vp-c-warning-1);
}

/* 其他平台入口：收成一行，和匹配卡同样宽度对齐，视觉上是一个"折叠尾巴"。
   details/summary 自带展开语义和键盘行为，不需要自己维护 aria-expanded。
   它是 .container 的直接子元素（不在 .grid 里），所以宽度由自己控制：
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
