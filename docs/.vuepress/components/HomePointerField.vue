<script setup lang="ts">
import {onBeforeUnmount, onMounted, ref} from "vue";

// Plume 会把整条 home config 项 v-bind 过来，声明 type 以免它落到 canvas 的 DOM 属性上。
withDefaults(defineProps<{type?: string}>(), {type: ""});

const canvas = ref<HTMLCanvasElement | null>(null);

/**
 * 标签取自 resource/base/pipeline/*.json 里真实存在的节点名（去掉前缀段），
 * 不是编出来的装饰文字。全 ASCII，两份语言共用一套，不需要 i18n。
 */
const LABELS = [
    "ClickStage",
    "SelectStage",
    "EnsureHome",
    "CheckStamina",
    "NoStamina",
    "BattlePass",
    "Mailbox",
    "ClickVictory",
    "SwipeToBegin",
    "ReturnMain",
    "LaunchGame",
    "PrepareBattle",
    "SelectOpponent",
    "RewardDisplay",
    "StaminaInfo",
    "ClaimRewards",
    "SkillTraining",
    "CheckHomePage",
    "EventHubShop",
    "ExitResult",
];

const FONT = "10px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace";
/** 指针这个半径内的框会“锁定”：补全边框、扫线、标签提亮。 */
const LOCK_DIST = 168;
/** 光标正下方这个半径内改成排斥，框会被让开一点，不至于和十字准星叠在一起。 */
const HOLLOW_RADIUS = 46;
const MAX_DPR = 1.5;
const MAX_BOXES = 16;
/** 每 74000 CSS 平方像素一个框。比原来粒子的 12500 稀得多，因为一个框的视觉重量远大于一个点。 */
const AREA_PER_BOX = 74_000;
/** 点击扫描环：半径线性外扩，环前扫到的框会被点亮一次。 */
const RING_LIFE = 900;
const RING_SPEED = 0.34;
/** 指针静止这么久就停掉重绘。 */
const IDLE_MS = 2600;

type Box = {
    x: number;
    y: number;
    w: number;
    h: number;
    /** 自身匀速漂移，和指针冲量分开存，否则阻尼会把漂移一起衰减掉、整场会慢慢冻住。 */
    dx: number;
    dy: number;
    /** 指针给的临时冲量 */
    ix: number;
    iy: number;
    label: string;
    conf: number;
    /** 0..1 的锁定程度，向目标值缓动，所以指针离开后是慢慢淡出而不是瞬间消失。 */
    lock: number;
    /** 每框一个错相量，扫线才不会所有框同步上下跳。 */
    seed: number;
};

let ctx: CanvasRenderingContext2D | null = null;
let boxes: Box[] = [];
let rings: {x: number; y: number; born: number}[] = [];
let raf = 0;
let width = 0;
let height = 0;
let rgb = "219, 39, 119";
let running = false;
let idleTimer: number | undefined;
let observer: MutationObserver | null = null;
const pointer = {x: -1e4, y: -1e4, inside: false};

/**
 * 只读一个 CSS 变量，颜色就跟着主题走。
 * brand-2 在浅色下是深玫红、深色下是亮粉，两种底色都看得见；
 * brand-1/3 在各自的对侧主题里会淡到接近不可读。
 */
function syncAccent() {
    const raw = getComputedStyle(document.documentElement).getPropertyValue("--vp-c-brand-2").trim();
    const hex = raw.replace("#", "");
    const full = hex.length === 3 ? hex.replace(/./g, (c) => c + c) : hex;
    const n = Number.parseInt(full.slice(0, 6), 16);
    if (Number.isFinite(n)) rgb = `${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}`;
}

function tint(alpha: number): string {
    return `rgba(${rgb}, ${alpha.toFixed(3)})`;
}

function seed() {
    const target = Math.round((width * height) / AREA_PER_BOX);
    const count = Math.max(6, Math.min(MAX_BOXES, target));
    const next: Box[] = [];
    for (let i = 0; i < count; i++) {
        const keep = boxes[i];
        next.push(
            keep ?? {
                x: Math.random() * width,
                y: Math.random() * height,
                w: 84 + Math.random() * 108,
                h: 34 + Math.random() * 42,
                dx: (Math.random() - 0.5) * 0.22,
                dy: (Math.random() - 0.5) * 0.22,
                ix: 0,
                iy: 0,
                label: LABELS[(Math.random() * LABELS.length) | 0]!,
                conf: 0.86 + Math.random() * 0.13,
                lock: 0,
                seed: Math.random(),
            },
        );
    }
    boxes = next;
}

function resize(el: HTMLCanvasElement) {
    if (!ctx) return;
    const dpr = Math.min(window.devicePixelRatio || 1, MAX_DPR);
    width = el.clientWidth;
    height = el.clientHeight;
    el.width = Math.round(width * dpr);
    el.height = Math.round(height * dpr);
    // 之后所有绘制都用 CSS 像素坐标，把缩放一次性交给 transform。
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    seed();
}

/** 环前扫到的框点亮一次：用“到环心的距离落在框上的投影”判断，比逐像素便宜得多。 */
function sweptBy(b: Box, cx: number, cy: number, radius: number): boolean {
    const halfW = b.w / 2;
    const halfH = b.h / 2;
    const nx = Math.max(b.x - halfW, Math.min(cx, b.x + halfW));
    const ny = Math.max(b.y - halfH, Math.min(cy, b.y + halfH));
    const d = Math.hypot(cx - nx, cy - ny);
    return Math.abs(d - radius) < 26;
}

function drawBox(b: Box, now: number) {
    if (!ctx) return;
    const halfW = b.w / 2;
    const halfH = b.h / 2;
    const l = b.lock;
    const arm = Math.min(15, halfW * 0.6, halfH);

    // 四角直角标：常态就只画这个，整页不会糊成一片框。
    ctx.beginPath();
    ctx.moveTo(b.x - halfW, b.y - halfH + arm);
    ctx.lineTo(b.x - halfW, b.y - halfH);
    ctx.lineTo(b.x - halfW + arm, b.y - halfH);
    ctx.moveTo(b.x + halfW - arm, b.y - halfH);
    ctx.lineTo(b.x + halfW, b.y - halfH);
    ctx.lineTo(b.x + halfW, b.y - halfH + arm);
    ctx.moveTo(b.x + halfW, b.y + halfH - arm);
    ctx.lineTo(b.x + halfW, b.y + halfH);
    ctx.lineTo(b.x + halfW - arm, b.y + halfH);
    ctx.moveTo(b.x - halfW + arm, b.y + halfH);
    ctx.lineTo(b.x - halfW, b.y + halfH);
    ctx.lineTo(b.x - halfW, b.y + halfH - arm);
    ctx.lineWidth = 1.2 + l * 0.6;
    ctx.strokeStyle = tint(0.44 + l * 0.44);
    ctx.stroke();

    if (l < 0.04) return;

    // 锁定后才补全边框和扫线，指针划过时框会“合上”。
    ctx.globalAlpha = l;
    ctx.strokeStyle = tint(0.42);
    ctx.strokeRect(b.x - halfW, b.y - halfH, b.w, b.h);

    const t = ((now / 1100 + b.seed) % 1) * b.h;
    const scanY = b.y - halfH + t;
    ctx.strokeStyle = tint(0.5);
    ctx.beginPath();
    ctx.moveTo(b.x - halfW + 2, scanY);
    ctx.lineTo(b.x + halfW - 2, scanY);
    ctx.stroke();
    ctx.globalAlpha = 1;
}

function drawLabel(b: Box) {
    if (!ctx) return;
    const l = b.lock;
    ctx.font = FONT;
    ctx.textBaseline = "bottom";
    ctx.fillStyle = tint(0.36 + l * 0.5);
    ctx.fillText(b.label, b.x - b.w / 2, b.y - b.h / 2 - 4);
    const conf = `${b.conf.toFixed(2)}`;
    ctx.fillStyle = tint(0.28 + l * 0.42);
    ctx.fillText(conf, b.x - b.w / 2 + ctx.measureText(`${b.label} `).width, b.y - b.h / 2 - 4);
}

function drawCrosshair() {
    if (!ctx || !pointer.inside) return;
    const {x, y} = pointer;
    ctx.lineWidth = 1;
    ctx.strokeStyle = tint(0.34);
    ctx.beginPath();
    ctx.moveTo(x - 11, y);
    ctx.lineTo(x - 4, y);
    ctx.moveTo(x + 4, y);
    ctx.lineTo(x + 11, y);
    ctx.moveTo(x, y - 11);
    ctx.lineTo(x, y - 4);
    ctx.moveTo(x, y + 4);
    ctx.lineTo(x, y + 11);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(x, y, 15, 0, Math.PI * 2);
    ctx.strokeStyle = tint(0.2);
    ctx.stroke();

    // 坐标读数按 720p 基准换算，和仓库里所有 ROI 的口径一致。
    ctx.font = FONT;
    ctx.textBaseline = "top";
    ctx.fillStyle = tint(0.3);
    ctx.fillText(`${Math.round((x / width) * 1280)},${Math.round((y / height) * 720)}`, x + 21, y + 6);
}

function frame(now: number) {
    raf = requestAnimationFrame(frame);
    if (!ctx) return;
    ctx.clearRect(0, 0, width, height);

    rings = rings.filter((r) => now - r.born < RING_LIFE);
    const radii = rings.map((r) => ({r, radius: (now - r.born) * RING_SPEED, cx: r.x, cy: r.y}));

    for (const b of boxes) {
        let target = 0;
        if (pointer.inside) {
            const ox = pointer.x - b.x;
            const oy = pointer.y - b.y;
            const d = Math.hypot(ox, oy) || 1;
            if (d < LOCK_DIST) target = 1 - d / LOCK_DIST;
            if (d < HOLLOW_RADIUS * 3) {
                const falloff = 1 - d / (HOLLOW_RADIUS * 3);
                b.ix -= (ox / d) * falloff * 0.5;
                b.iy -= (oy / d) * falloff * 0.5;
            }
        }
        for (const s of radii) if (sweptBy(b, s.cx, s.cy, s.radius)) target = 1;
        b.lock += (target - b.lock) * 0.12;

        b.ix *= 0.9;
        b.iy *= 0.9;
        b.x += b.dx + b.ix;
        b.y += b.dy + b.iy;

        const m = Math.max(b.w, b.h);
        if (b.x < -m) b.x = width + m;
        else if (b.x > width + m) b.x = -m;
        if (b.y < -m) b.y = height + m;
        else if (b.y > height + m) b.y = -m;
    }

    ctx.lineCap = "round";
    for (const b of boxes) drawBox(b, now);
    for (const b of boxes) drawLabel(b);
    drawCrosshair();

    for (const s of radii) {
        const t = (now - s.r.born) / RING_LIFE;
        ctx.strokeStyle = tint((1 - t) * (1 - t) * 0.42);
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(s.cx, s.cy, s.radius, 0, Math.PI * 2);
        ctx.stroke();
    }
}

function start() {
    if (running || !ctx) return;
    running = true;
    raf = requestAnimationFrame(frame);
}

function stop() {
    running = false;
    cancelAnimationFrame(raf);
}

/**
 * 有任何动静就重新跑起来，并把“静止 → 停绘”的倒计时推到 IDLE_MS 之后。
 * 卡片做成磨砂玻璃之后，这层每重绘一次，压在它上面的每一块 backdrop-filter 都要重算一次模糊；
 * 停下来，最后一帧留在画布上，整片是冻住而不是消失。
 */
function wake() {
    start();
    window.clearTimeout(idleTimer);
    idleTimer = window.setTimeout(stop, IDLE_MS);
}

function onPointerMove(e: PointerEvent) {
    // 触屏的 touch 事件也会合成 pointermove，但那种情况下组件根本没挂载，这里只兜一手笔输入。
    if (e.pointerType === "touch") return;
    pointer.x = e.clientX;
    pointer.y = e.clientY;
    pointer.inside = true;
    wake();
}

function onPointerLeave() {
    pointer.inside = false;
}

function onClick(e: MouseEvent) {
    rings.push({x: e.clientX, y: e.clientY, born: performance.now()});
    if (rings.length > 4) rings.shift();
    wake();
}

function onVisibility() {
    // 回到前台必须走 wake 而不是 start，否则一次切标签页就把循环永久叫醒、再也不睡了。
    if (document.hidden) {
        window.clearTimeout(idleTimer);
        stop();
    } else wake();
}

onMounted(() => {
    const el = canvas.value;
    // 只在有真正指针的桌面端挂载；触屏没有指针来驱动这层，不给它加一份每帧重绘。
    if (
        !el ||
        !window.matchMedia("(pointer: fine)").matches ||
        !window.matchMedia("(prefers-reduced-motion: no-preference)").matches
    )
        return;
    ctx = el.getContext("2d");
    if (!ctx) return;

    syncAccent();
    // 主题切换是属性变化，没有样式事件可挂，用 MutationObserver 跟着重取一次变量。
    observer = new MutationObserver(() => {
        const before = rgb;
        syncAccent();
        // 颜色真的变了才叫醒循环：class 属性在滚动/路由时也会动，每次都 wake 等于永远不睡。
        // 不重绘的话，换肤后画布上留的还是旧主题颜色的框，会一直挂在那儿。
        if (before !== rgb) wake();
    });
    observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: [
            "data-theme",
            "class",
        ],
    });

    resize(el);
    wake();

    window.addEventListener("resize", onResize);
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerdown", onClick);
    document.addEventListener("pointerleave", onPointerLeave);
    document.addEventListener("visibilitychange", onVisibility);
});

let resizeQueued = false;
function onResize() {
    // resize 事件在拖窗口时能一帧连发十几次，合并到下一个 rAF 再量一次。
    if (resizeQueued) return;
    resizeQueued = true;
    requestAnimationFrame(() => {
        resizeQueued = false;
        if (!canvas.value) return;
        resize(canvas.value);
        // 改 el.width 会把画布清空，这时如果循环正睡着，整层就彻底白了，所以必须重绘。
        wake();
    });
}

onBeforeUnmount(() => {
    window.clearTimeout(idleTimer);
    stop();
    observer?.disconnect();
    window.removeEventListener("resize", onResize);
    window.removeEventListener("pointermove", onPointerMove);
    window.removeEventListener("pointerdown", onClick);
    document.removeEventListener("pointerleave", onPointerLeave);
    document.removeEventListener("visibilitychange", onVisibility);
});
</script>

<template>
    <!-- 纯装饰层，读屏和命中测试都应该完全跳过它。 -->
    <canvas ref="canvas" class="home-pointer-field" aria-hidden="true"></canvas>
</template>

<style scoped>
/* 和网格层同一个栈叠上下文（.vp-home 是 z-index:0），同为 -1 时按 DOM 先后决定，
   本块排在 hero 之后，所以会压在网格之上、正文之下。 */
.home-pointer-field {
    position: fixed;
    inset: 0;
    z-index: -1;
    width: 100%;
    height: 100%;
    pointer-events: none;
    /* 顶栏是半透明加模糊的，框和标签从它后面透出来会和导航文字打架，底部同理会被裁字。
       淡出带要拉到能盖住“标签刚进屏”的那段：标签画在框上方约 20px，所以它比框本体更早进屏，
       112px 的斜坡走到导航底（60px）时已经有 0.54 强度，字就压在导航上了。168px 才够压到看不见。
       这里的 mask 是静态的、不会跟着跑：canvas 元素本身没有 transform，
       和之前 .vp-home::before 那个跟着动画平移的遮罩不是一回事。 */
    -webkit-mask-image: linear-gradient(transparent 0, #000 168px, #000 calc(100% - 120px), transparent 100%);
    mask-image: linear-gradient(transparent 0, #000 168px, #000 calc(100% - 120px), transparent 100%);
}
</style>
