<script setup lang="ts">
import release from "../data/latest-release.json";
import {VPIcon} from "vuepress-theme-plume/client";
import {computed} from "vue";

type Asset = {
    arch: string;
    ext: string;
    name: string;
    os: string;
    size: number;
    ui: "MFAA" | "MXU";
    url: string;
};

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

const ARCH_LABEL: Record<string, string> = {x86_64: "x86_64", aarch64: "ARM64"};

const TEXT = {
    zh: {
        hint: "MFAA 与 MXU 只有界面外观的区别，功能完全一致，任选其一即可。",
        version: "当前版本",
        published: "发布于",
        allVersions: "全部版本",
        mirror: "Mirror酱 高速下载",
        unavailable: "发布数据暂不可用（构建时取不到 GitHub Release），请到",
        unavailableTail: "页面查看最新版本。",
    },
    en: {
        hint: "MFAA and MXU differ only in appearance, features are identical, so pick either one.",
        version: "Current version",
        published: "published",
        allVersions: "All versions",
        mirror: "Mirror酱 fast download",
        unavailable: "Release data is unavailable right now (the build could not reach GitHub). See the",
        unavailableTail: "page for the latest version.",
    },
};

const GROUPS = [
    {os: "win", label: "Windows", icon: "ri:windows-line"},
    {os: "macos", label: "macOS", icon: "ri:apple-line"},
    {os: "linux", label: "Linux", icon: "ri:terminal-box-line"},
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

function mb(bytes: number): string {
    return `${(bytes / 1048576).toFixed(1)} MB`;
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

            <p v-if="available" class="hint">{{ t.hint }}</p>

            <div v-if="available" class="grid">
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
                                <span class="ui">{{ asset.ui }}</span>
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
    align-items: baseline;
    justify-content: space-between;
    gap: 8px;
    padding: 9px 12px;
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
}

.size {
    font-size: 12px;
    color: var(--vp-c-text-3);
}

/* 768 起就三列，和主题 features 区块在同一断点变成三列，避免出现通栏的第四行卡片；
   此时单卡约 213px，.opts 会自动退成单列，到 960px 卡片变宽后再并排。 */
@media (min-width: 768px) {
    .grid {
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
