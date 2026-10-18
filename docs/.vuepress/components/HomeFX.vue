<script setup lang="ts">
import {onBeforeUnmount, onMounted, ref} from "vue";

// Plume 会把整条 home config 项 v-bind 过来，声明全部字段以免它们落到 DOM 属性上。
withDefaults(defineProps<{type?: string; index?: number; onlyOnce?: boolean}>(), {
    type: "",
    index: -1,
    onlyOnce: false,
});

/**
 * 首页的三处交互增强，全部与视觉层解耦：
 * 1. 顶部滚动进度条（fixed，2px，不占文档流）
 * 2. 功能卡片里的指针光斑（把鼠标坐标写进 --hp-mx / --hp-my，绘制交给 CSS）
 * 3. hero 滚出视口后停掉首屏常驻动画（data-hp-hero-away）
 * 4. 卡片滚动进场（data-hp-reveal + is-revealed）
 *
 * 三条都只在有精细指针、且用户没要求减少动效时才启用；
 * 关掉时页面回到纯 CSS 的静态样子，不会缺任何内容。
 */
/** 进度条节点在挂载时创建、卸载时移除：SSR 里根本不存在，也就不会有 hydration 失配。 */
let progress: HTMLDivElement | null = null;

const FINE_POINTER = "(pointer: fine)";
const REDUCED = "(prefers-reduced-motion: reduce)";

let home: HTMLElement | null = null;
let hero: HTMLElement | null = null;
let heroObserver: IntersectionObserver | null = null;
let revealObserver: IntersectionObserver | null = null;
let revealFallback: number | undefined;
let revealFlush: (() => void) | null = null;
let enabled = false;
let finePointer = false;
let raf = 0;
let queued = false;
let lastTarget: HTMLElement | null = null;
/** 卡片的 rect 只在换卡片、滚动、resize 时重量，指针移动时直接复用。 */
let lastRect: DOMRect | null = null;
let rectDirty = true;

function onScroll() {
    if (queued) return;
    queued = true;
    raf = requestAnimationFrame(() => {
        queued = false;
        const el = progress;
        if (!el) return;
        // 进度条只在首页滚动时推进；文档页组件不挂载，也不会拿到这个节点。
        rectDirty = true;
        const max = document.documentElement.scrollHeight - window.innerHeight;
        const ratio = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0;
        // scaleX 走合成层，比改 width 便宜。
        el.style.transform = "scaleX(" + ratio.toFixed(4) + ")";
        el.style.opacity = ratio > 0.002 ? "1" : "0";
    });
}

/**
 * 光斑坐标用 event.target.closest 找卡片：指针在卡片内部移动时 target 就是卡片里的
 * 文字/图标，向上找一次即可，不需要遍历所有卡片。写的是相对卡片的 px，
 * 卡片自己换行/缩放都不影响。
 */
function onPointerMove(e: PointerEvent) {
    if (e.pointerType === "touch") return;
    const target = (e.target as Element | null)?.closest?.(".vp-home-feature") as HTMLElement | null;
    if (target !== lastTarget) {
        lastTarget?.style.removeProperty("--hp-mx");
        lastTarget?.style.removeProperty("--hp-my");
        lastTarget = target;
        rectDirty = true;
    }
    if (!target) return;
    // getBoundingClientRect 会强制一次布局，指针每帧都调等于每帧重排，
    // 所以只在换卡片 / 滚动 / 缩放后重量一次。
    if (rectDirty || !lastRect) {
        lastRect = target.getBoundingClientRect();
        rectDirty = false;
    }
    target.style.setProperty("--hp-mx", (e.clientX - lastRect.left).toFixed(1) + "px");
    target.style.setProperty("--hp-my", (e.clientY - lastRect.top).toFixed(1) + "px");
}

function onPointerOut(e: PointerEvent) {
    const target = (e.target as Element | null)?.closest?.(".vp-home-feature") as HTMLElement | null;
    if (!target) return;
    // 指针可能只是移到卡片的子元素上，relatedTarget 仍在卡片内时不能清。
    if (e.relatedTarget instanceof Node && target.contains(e.relatedTarget)) return;
    target.style.removeProperty("--hp-mx");
    target.style.removeProperty("--hp-my");
    if (lastTarget === target) {
        lastTarget = null;
        lastRect = null;
    }
}

function start() {
    if (enabled) return;
    enabled = true;
    window.addEventListener("scroll", onScroll, {passive: true});
    window.addEventListener("resize", onScroll, {passive: true});
    if (finePointer) {
        window.addEventListener("pointermove", onPointerMove, {passive: true});
        window.addEventListener("pointerout", onPointerOut, {passive: true});
    }
    onScroll();
}

function stop() {
    if (!enabled) return;
    enabled = false;
    window.removeEventListener("scroll", onScroll);
    window.removeEventListener("resize", onScroll);
    window.removeEventListener("pointermove", onPointerMove);
    window.removeEventListener("pointerout", onPointerOut);
    cancelAnimationFrame(raf);
    queued = false;
}

/**
 * 滚动进场：先给根节点打上 data-hp-reveal（CSS 里只有这个属性存在时才进入
 * "半透明 + 下移"的初始态），再逐个观察卡片。
 * 已经在视口内的元素不参与观察，直接标成已进场——避免打开页面时首屏先闪一下半透明。
 * 任何一步失败都只是没有入场动画，内容始终可见。
 */
function setupReveal(root: HTMLElement) {
    if (typeof IntersectionObserver === "undefined") return;

    const targets = root.querySelectorAll<HTMLElement>(".vp-home-feature, .home-download .group, .home-stats .stat");
    if (!targets.length) return;

    const viewport = window.innerHeight;
    const pending: HTMLElement[] = [];
    for (const el of targets) {
        // 进入视口下沿之前不位移，已经在屏幕里的直接算已进场。
        if (el.getBoundingClientRect().top < viewport * 0.92) el.classList.add("is-revealed");
        else pending.push(el);
    }

    root.setAttribute("data-hp-reveal", "");
    if (!pending.length) return;

    let observerFired = false;
    const reveal = (el: Element) => {
        el.classList.add("is-revealed");
        revealObserver?.unobserve(el);
    };
    revealObserver = new IntersectionObserver(
        (entries) => {
            observerFired = true;
            for (const entry of entries) {
                if (!entry.isIntersecting) continue;
                reveal(entry.target);
            }
        },
        // 底部内缩 8%：卡片刚探进屏幕下沿时不急着动，滑到差不多能看清时才进场。
        {rootMargin: "0px 0px -8% 0px"},
    );
    for (const el of pending) revealObserver.observe(el);

    // 兜底只看“观察器到底有没有回调”：IntersectionObserver 对每个被观察元素一定会
    // 先回调一次（哪怕 isIntersecting 是 false），所以 2 秒内一次都没有，就说明它没在工作，
    // 此时无条件全部放行。不能无条件定时全放出来——那会让之后滚动到的卡片失去入场动画。
    revealFallback = window.setTimeout(() => {
        if (observerFired) return;
        for (const el of pending) reveal(el);
        revealObserver?.disconnect();
        revealObserver = null;
    }, 2000);

    // 最后一道保险：进场只影响位移，但万一某张卡因为异常路径永远收不到 is-revealed，
    // 它就会一直偏 22px。滚动结束时把当前视口内的卡片无条件放行，代价只是少一次动画。
    const flushVisible = () => {
        for (const el of pending) {
            const rect = el.getBoundingClientRect();
            if (rect.top < window.innerHeight && rect.bottom > 0) reveal(el);
        }
    };
    window.addEventListener("scroll", flushVisible, {passive: true});
    revealFlush = flushVisible;
}

onMounted(() => {
    // 进度条必须挂在 body 上：.vp-home 自己是 z-index:0 的层叠上下文，
    // 留在里面的话 z-index 再大也压不过外层导航，滚动时整条会被导航盖住。
    progress = document.createElement("div");
    progress.className = "home-fx-progress";
    progress.setAttribute("aria-hidden", "true");
    document.body.appendChild(progress);

    home = document.querySelector(".vp-home");
    hero = document.querySelector(".vp-home-hero");
    if (!home || !hero) return;

    // 减少动效时连进度条也一起关掉：它不是内容，只是一条装饰性的反馈。
    if (window.matchMedia(REDUCED).matches) return;

    finePointer = window.matchMedia(FINE_POINTER).matches;
    start();

    setupReveal(home);

    // 首屏动画在 hero 离开视口后暂停。rootMargin 留一点余量，
    // 免得在 hero 边缘来回滚动时反复开关。
    if (typeof IntersectionObserver !== "undefined") {
        heroObserver = new IntersectionObserver(
            (entries) => {
                for (const entry of entries) {
                    if (entry.isIntersecting) home?.removeAttribute("data-hp-hero-away");
                    else home?.setAttribute("data-hp-hero-away", "");
                }
            },
            {rootMargin: "120px"},
        );
        heroObserver.observe(hero);
    }
});

onBeforeUnmount(() => {
    stop();
    progress?.remove();
    progress = null;
    heroObserver?.disconnect();
    heroObserver = null;
    revealObserver?.disconnect();
    revealObserver = null;
    window.clearTimeout(revealFallback);
    if (revealFlush) window.removeEventListener("scroll", revealFlush);
    revealFlush = null;
    home?.removeAttribute("data-hp-hero-away");
    lastTarget?.style.removeProperty("--hp-mx");
    lastTarget?.style.removeProperty("--hp-my");
    lastTarget = null;
});
</script>

<template>
    <!-- 渲染一个真实但不可见的节点：滚动进度条本身在 onMounted 里创建后挂到 body 上。
         不能返回空模板——空组件在 SSR 里不产出节点、客户端却会补一个注释锚点，
         两边结构对不上就会报 hydration mismatch。给一个 display:none 的空 div
         两边就完全一致了。 -->
    <div class="home-fx-root" aria-hidden="true" />
</template>

<style>
/* 占位节点：只是为了 SSR/客户端结构一致，不占布局。 */
.home-fx-root {
    display: none;
}

/* 全局样式：节点挂在 body 上，拿不到 scoped 属性。
   贴在视口最上沿、压在导航之上：2px 高，不挡任何可点区域。
   初始 opacity:0，滚动后才淡入，静止的首页不会多一条横线。 */
.home-fx-progress {
    position: fixed;
    top: 0;
    right: 0;
    left: 0;
    z-index: 100;
    height: 2px;
    pointer-events: none;
    background: linear-gradient(90deg, var(--vp-c-brand-3), var(--vp-c-brand-1) 45%, #8b5cf6 72%, #22d3ee);
    opacity: 0;
    transform: scaleX(0);
    transform-origin: left center;
    transition: opacity 0.3s ease;
}
</style>
