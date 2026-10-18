<script setup lang="ts">
import stats from "../data/project-stats.json";
import {computed, onBeforeUnmount, onMounted, ref} from "vue";

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

const TEXT = {
    zh: {
        tasks: "自动化任务",
        tasksNote: "界面中可直接运行的条目",
        nodes: "Pipeline 节点",
        nodesNote: (files: number) => `${files} 份 JSON 定义`,
        custom: "Custom 扩展",
        customNote: (actions: number, recognitions: number) => `${recognitions} 识别 + ${actions} 动作`,
        images: "模板图素材",
        imagesNote: "720p 基准识别用",
        docs: "双语文档",
        docsNote: (perLocale: number) => `中英各 ${perLocale} 页`,
        source: "以上数字由构建脚本从仓库源码实时统计，随每次发布重新计算。截至",
        unavailable: "项目规模统计暂不可用（构建脚本未能完成统计）。",
    },
    en: {
        tasks: "Tasks",
        tasksNote: "Entries runnable from the UI",
        nodes: "Pipeline nodes",
        nodesNote: (files: number) => `defined in ${files} JSON files`,
        custom: "Custom extensions",
        customNote: (actions: number, recognitions: number) => `${recognitions} recognitions + ${actions} actions`,
        images: "Templates",
        imagesNote: "cut for the 720p baseline",
        docs: "Docs pages",
        docsNote: (perLocale: number) => `${perLocale} per locale`,
        source: "Every figure above is counted from the repository by a build script and recomputed on each release. As of",
        unavailable: "Project scale figures are unavailable right now (the stats script did not complete).",
    },
};

const t = computed(() => TEXT[props.lang]);

const items = computed(() => {
    const x = t.value;
    return [
        {key: "tasks", value: stats.tasks, label: x.tasks, note: x.tasksNote},
        {key: "nodes", value: stats.pipelineNodes, label: x.nodes, note: x.nodesNote(stats.pipelineFiles)},
        {
            key: "custom",
            value: stats.customActions + stats.customRecognitions,
            label: x.custom,
            note: x.customNote(stats.customActions, stats.customRecognitions),
        },
        {key: "images", value: stats.templateImages, label: x.images, note: x.imagesNote},
        {key: "docs", value: stats.docPagesZh + stats.docPagesEn, label: x.docs, note: x.docsNote(stats.docPagesZh)},
    ];
});

const asOf = computed(() => (stats.generatedAt ? stats.generatedAt.slice(0, 10) : ""));
// 统计脚本失败时会写全零占位，这时候整排 0 比不写更容易误导，直接降级成一行说明。
const available = computed(() => stats.pipelineNodes > 0);

/**
 * 数字滚入视口时从 0 数到目标值。
 * SSR 和首帧渲染的都是真实值，只有挂载之后、元素真的进入视口才清零重数——
 * 这样 JS 没跑、动画被禁用、或者用户直接停在页面底部时，看到的始终是正确数字，
 * 不会出现一排 0 等着数。
 */
const displayed = ref<number[] | null>(null);
const row = ref<HTMLDivElement | null>(null);
let observer: IntersectionObserver | null = null;
let raf = 0;
let started = false;

function animateCounts() {
    if (started) return;
    started = true;
    const targets = items.value.map((item) => item.value);
    const duration = 1100;
    const startAt = performance.now();
    displayed.value = targets.map(() => 0);

    const tick = (now: number) => {
        const t = Math.min(1, (now - startAt) / duration);
        // 末尾收得慢一点，读数停下来时不突兀。
        const eased = 1 - (1 - t) ** 3;
        displayed.value = targets.map((target) => Math.round(target * eased));
        if (t < 1) raf = requestAnimationFrame(tick);
        else displayed.value = targets;
    };
    raf = requestAnimationFrame(tick);
}

onMounted(() => {
    if (!available.value) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (typeof IntersectionObserver === "undefined") return;

    const el = row.value;
    if (!el) return;
    observer = new IntersectionObserver(
        (entries) => {
            for (const entry of entries) {
                if (!entry.isIntersecting) continue;
                observer?.disconnect();
                observer = null;
                animateCounts();
            }
        },
        {threshold: 0.4},
    );
    observer.observe(el);
});

onBeforeUnmount(() => {
    observer?.disconnect();
    observer = null;
    cancelAnimationFrame(raf);
});

function valueOf(index: number, fallback: number): number {
    const shown = displayed.value?.[index];
    return shown === undefined ? fallback : shown;
}
</script>

<template>
    <section class="home-stats">
        <div class="container">
            <h2 v-if="title" class="title">{{ title }}</h2>

            <div v-if="available" ref="row" class="row">
                <div v-for="(item, i) in items" :key="item.key" class="stat">
                    <p class="value">{{ valueOf(i, item.value) }}</p>
                    <p class="label">{{ item.label }}</p>
                    <p class="note">{{ item.note }}</p>
                </div>
            </div>

            <p v-if="available" class="source">{{ t.source }} {{ asOf }}</p>
            <p v-else class="source">{{ t.unavailable }}</p>
        </div>
    </section>
</template>

<style scoped>
/* 和 HomeDownload 同一套内边距/内容宽度，两个区块的左右边界才对得齐。 */
.home-stats {
    padding: 24px;
}

@media (min-width: 640px) {
    .home-stats {
        padding: 32px 48px;
    }
}

@media (min-width: 960px) {
    .home-stats {
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

/* 窄屏用 auto-fit 自然折行；但 5 个条目在 640–960 区间会被算成 4 列、掉出一个孤儿，
   所以从 768 起强制一行五列——此时单格约 126px，最宽的 "Pipeline 节点" 也放得下。 */
.row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px;
}

@media (min-width: 768px) {
    .row {
        grid-template-columns: repeat(5, 1fr);
    }
}

.stat {
    padding: 18px 12px 16px;
    text-align: center;
    /* 和首页卡片共用 home-hero.css 里那组玻璃变量，触屏/高对比模式由那边一次性退回实色。 */
    background-color: var(--vp-home-glass-bg);
    border: 1px solid var(--vp-home-glass-edge);
    border-radius: 12px;
    box-shadow: var(--vp-home-glass-spec);
    -webkit-backdrop-filter: var(--vp-home-glass-blur);
    backdrop-filter: var(--vp-home-glass-blur);
    transition:
        transform 0.25s ease,
        box-shadow 0.25s ease,
        border-color var(--vp-t-color),
        background-color var(--vp-t-color);
}

.stat:hover {
    border-color: var(--vp-c-brand-1);
    transform: translateY(-3px);
    /* 内高光要和 hover 光晕并列，否则一条 box-shadow 就把玻璃上沿顶没了。 */
    box-shadow:
        var(--vp-home-glass-spec),
        0 0 18px -6px color-mix(in srgb, var(--vp-c-brand-1) 80%, transparent);
}

.value {
    margin-bottom: 2px;
    font-size: 32px;
    font-weight: 900;
    line-height: 1.1;
    color: var(--vp-c-brand-1);
    font-variant-numeric: tabular-nums;
}

.label {
    margin-bottom: 2px;
    font-size: 14px;
    font-weight: 600;
    color: var(--vp-c-text-1);
}

.note {
    font-size: 12px;
    line-height: 18px;
    color: var(--vp-c-text-3);
}

.source {
    margin-top: 16px;
    font-size: 12px;
    line-height: 20px;
    color: var(--vp-c-text-3);
    text-align: center;
}
</style>
