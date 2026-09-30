import {mkdirSync, readFileSync, writeFileSync, readdirSync, existsSync} from "node:fs";
import {dirname, join, resolve} from "node:path";
import {fileURLToPath} from "node:url";
import {parse} from "jsonc-parser";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");
const OUT = resolve(ROOT, "docs", ".vuepress", "data", "project-stats.json");

function walk(dir, acc = []) {
    if (!existsSync(dir)) return acc;
    for (const entry of readdirSync(dir, {withFileTypes: true})) {
        const p = join(dir, entry.name);
        if (entry.isDirectory()) walk(p, acc);
        else acc.push(p);
    }
    return acc;
}

function readJson(p) {
    // resource/base/default_pipeline.json 这类文件带注释，裸 JSON.parse 会直接抛。
    return parse(readFileSync(p, "utf8")) ?? {};
}

function countTasks() {
    let tasks = 0;
    for (const file of walk(join(ROOT, "tasks"))) {
        if (!file.endsWith(".json") || file.includes(join("tasks", "preset"))) continue;
        const body = JSON.parse(readFileSync(file, "utf8"));
        tasks += Array.isArray(body.task) ? body.task.length : 0;
    }
    return tasks;
}

function countPipeline() {
    let files = 0;
    let nodes = 0;
    for (const set of [
        "base",
        "bilibili",
        "taptap",
    ]) {
        for (const file of walk(join(ROOT, "resource", set, "pipeline"))) {
            if (!file.endsWith(".json")) continue;
            files += 1;
            // pipeline 协议里每个顶层键就是一个节点名，没有别的语义键。
            nodes += Object.keys(readJson(file)).length;
        }
    }
    return {files, nodes};
}

function countCustom() {
    const out = {};
    for (const kind of [
        "action",
        "recognition",
    ]) {
        let n = 0;
        for (const file of walk(join(ROOT, "agent", "custom", kind))) {
            if (!file.endsWith(".py") || file.endsWith("__init__.py")) continue;
            const src = readFileSync(file, "utf8");
            for (const _ of src.matchAll(/^class\s+\w+\s*\(\s*Custom(?:Action|Recognition)\b/gm)) n += 1;
        }
        out[kind === "action" ? "customActions" : "customRecognitions"] = n;
    }
    return out;
}

function countTemplateImages() {
    let n = 0;
    for (const set of [
        "base",
        "bilibili",
        "taptap",
    ]) {
        for (const file of walk(join(ROOT, "resource", set, "image"))) {
            if (/\.(png|jpe?g|webp)$/i.test(file)) n += 1;
        }
    }
    return n;
}

function countDocs() {
    const per = {};
    for (const loc of [
        "zh",
        "en",
    ]) {
        per[loc] = walk(join(ROOT, "docs", loc)).filter((f) => f.endsWith(".md")).length;
    }
    return per;
}

function main() {
    const pipeline = countPipeline();
    const docs = countDocs();
    return {
        generatedAt: new Date().toISOString(),
        tasks: countTasks(),
        pipelineFiles: pipeline.files,
        pipelineNodes: pipeline.nodes,
        ...countCustom(),
        templateImages: countTemplateImages(),
        docPagesZh: docs.zh,
        docPagesEn: docs.en,
    };
}

let stats;
try {
    stats = main();
} catch (error) {
    // 和 gen-docs-downloads 一样：统计出问题不能把文档构建带崩，留着上一次的结果。
    console.warn(
        `[gen-docs-stats] ${error instanceof Error ? error.message : error} — keeping the previously generated file`,
    );
    // 全新 clone 没有上一次的结果，组件的静态 import 会失败，所以补一份全零占位、由首页降级显示。
    try {
        readFileSync(OUT);
    } catch {
        mkdirSync(dirname(OUT), {recursive: true});
        writeFileSync(
            OUT,
            `${JSON.stringify({generatedAt: null, tasks: 0, pipelineFiles: 0, pipelineNodes: 0, customActions: 0, customRecognitions: 0, templateImages: 0, docPagesZh: 0, docPagesEn: 0}, null, 4)}\n`,
            "utf8",
        );
        console.warn("[gen-docs-stats] wrote a zeroed placeholder so the docs build still resolves");
    }
    process.exit(0);
}

const next = `${JSON.stringify(stats, null, 4)}\n`;
let previous = null;
try {
    previous = readFileSync(OUT, "utf8");
} catch {
    /* first run */
}

if (next === previous) {
    console.log(`[gen-docs-stats] ${stats.pipelineNodes} nodes across ${stats.tasks} tasks — unchanged`);
} else {
    mkdirSync(dirname(OUT), {recursive: true});
    writeFileSync(OUT, next, "utf8");
    console.log(
        `[gen-docs-stats] wrote ${Object.keys(stats).length - 1} figures to docs/.vuepress/data/project-stats.json`,
    );
}
