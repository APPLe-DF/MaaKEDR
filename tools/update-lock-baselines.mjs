/**
 * 更新 maa-project.lock.json 中全部 managed-file 基线哈希。
 *
 * 用途：在 schema-sync 等自动任务改写 managed 文件后调用，避免
 * `pnpm check` 因 baseline 失配失败（与 tools/check-project.mjs 的
 * managedFileHash 逻辑保持一致）。
 */

import {createHash} from "node:crypto";
import {readFileSync, writeFileSync, existsSync} from "node:fs";

const LOCK_PATH = "maa-project.lock.json";

const lock = JSON.parse(readFileSync(LOCK_PATH, "utf8"));
const managedFiles = lock.managedFiles ?? {};
const updated = [];

for (const path of Object.keys(managedFiles)) {
    if (!existsSync(path)) continue;
    const hash = managedFileHash(path, readFileSync(path));
    if (hash !== managedFiles[path].hash) {
        managedFiles[path].hash = hash;
        updated.push(path);
    }
}

if (updated.length > 0) {
    writeFileSync(LOCK_PATH, JSON.stringify(lock, null, 4) + "\n", "utf8");
    console.log(`Updated ${updated.length} managed-file baseline(s):`);
    for (const path of updated) console.log(`  - ${path}`);
} else {
    console.log("No managed-file baseline drift.");
}

function managedFileHash(path, content) {
    if (isBinaryManagedPath(path)) {
        return sha256(content);
    }
    const text = content.toString();
    if (path === ".gitignore") {
        return sha256(normalizeManagedText(extractGitignoreBlock(text) ?? text));
    }
    return sha256(normalizeManagedText(text));
}

function normalizeManagedText(content) {
    return content.replace(/\r\n?/g, "\n");
}

function extractGitignoreBlock(content) {
    const start = content.indexOf("# BEGIN create-maa-project");
    if (start < 0) return undefined;
    const markerEnd = content.indexOf("# END create-maa-project", start);
    if (markerEnd < 0) return undefined;
    const endOfLine = content.indexOf("\n", markerEnd);
    return content.slice(start, endOfLine >= 0 ? endOfLine + 1 : content.length);
}

function isBinaryManagedPath(path) {
    return path.endsWith(".onnx");
}

function sha256(content) {
    return createHash("sha256").update(content).digest("hex");
}
