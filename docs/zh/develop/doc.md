---
order: 8
icon: jam:write-f
---

# 文档编写

本文说明如何为 MaaKEDR 文档站（VuePress Theme Plume）编写与修改文档。

## 目录约定

```text
docs/
├── README.md           # 语言选择首页
├── zh/                 # 简体中文
│   ├── README.md
│   ├── manual/         # 用户手册
│   ├── develop/        # 开发文档
│   └── protocol/       # 任务/资源协议
└── en/                 # English（结构与 zh 对齐）
```

- 路径与站内链接使用正斜杠
- 侧边栏在 `docs/.vuepress/config/navigation.ts` 的 `collections.sidebar` 中维护
- 新增页面后请同步修改 **中英文** sidebar（若有英文对照）

## 首页

两份首页（`docs/zh/README.md`、`docs/en/README.md`）用的是 Plume 的 `home` frontmatter，`config` 里的区块顺序就是页面顺序。

- 四个自定义区块在 `docs/.vuepress/components/`：`HomeDownload`（快捷下载）、`HomeStats`（项目规模）、`HomePointerField`（背景的识别框装饰层）、`HomeFX`（滚动进度条 + 卡片指针光斑 + 滚动进场）。必须先在同目录的 `client.ts` 里注册，`config` 中的 `type:` 才认得它们
- `HomeFX` 是纯增强层：它只在挂载后往 DOM 上打标记（`data-hp-reveal`、`data-hp-hero-away`、`is-revealed`）并挂一条进度条到 `body`，样式全在 `home-hero.css` 里按这些标记生效。没有 JS、用户开启「减少动效」、或指针不是精细指针时，页面只是少掉对应的动效，内容始终可见 —— 新增首页动效请沿用这个约定，不要把内容可见性交给 JS
- 首页专属样式只有 `docs/.vuepress/styles/home-hero.css` 一个文件，其中的**规则选择器**一律以 `.vp-home` 开头，以免漏到文档页上；只有 `--vp-home-*` 命名的 CSS 变量例外，它们必须声明在全局 `:root` / `html[data-theme="dark"]` 上才能被继承，靠命名前缀保证不与主题自带变量撞名
- `HomeDownload` 会在挂载后识别当前设备，只展示匹配的包，其余收进折叠入口。**架构只在有确凿证据时才表态**：Chromium 的高熵提示、UA 里明确写出的架构（含模拟器的 `sdk_gphone64_x86_64`）、macOS 的 WebGL 渲染器名；拿不到就置为「未知」而不是猜——猜错等于把用户送去一个跑不起来的包。三种收尾：macOS 架构未知时给「Apple 芯片 / Intel」两颗按钮；安卓 ABI 未知时按覆盖面推荐 arm64-v8a（没有就 universal）并标注「未能识别架构」；**桌面端本机架构没有对应包时，推荐卡会说明原因**（桌面不跨架构回退，只提示去完整列表选）。本机架构与推荐包不一致时另有一条「可能无法运行」警告（实际只会命中安卓覆盖面兜底——桌面永不跨架构回退）。识别结果只在客户端存在，SSR 产物始终是完整列表，不产生 hydration 失配
- **首页版本号与下载链接是自动的，不要手写**：`tools/gen-docs-downloads.mjs` 在每次构建时调用 GitHub Release API，取最新**正式版**（`/releases/latest` 会跳过 prerelease）的 tag、发布时间和资产清单，按 `MaaKEDR-<os>-<arch>-<tag>-<ui>.<ext>` 解析出平台/架构/界面版本。站点侧靠 `.github/workflows/deploy-docs.yml` 的两条触发保证及时刷新：`docs/**` 有改动，以及 **Release 工作流成功跑完后自动重建**（`workflow_run`）。另有 `workflow_dispatch` 可手动强制刷新
- 下载区已预留 **Android APK**：脚本认 `MaaKEDR-android-<universal|arm64-v8a|x86_64>-<tag>.apk` 这个命名（与 `android-build.yml` 的 Rename Release APK 步骤一致），APK 的 `ui` 字段固定为空串（安卓端只有一个壳，没有 MFAA/MXU 之分）。只要当前正式版的资产里带 APK，首页就会自动多出「Android」分组，安卓浏览器访问时推荐卡也会直接给对应 ABI 的 APK；资产里没有 APK 时（例如 Android 支持上线之前的旧版本）该分组整个不渲染，而不是留一个空分组
- 自动更新依赖 API 可用：脚本读 `GH_TOKEN` / `GITHUB_TOKEN` 给请求加认证（CI 里已传入），因为匿名配额只有 60 次/小时，撞上限后会静默回退到上一份数据、站点继续显示旧版本。改到新版本时构建日志会打印 `wrote N assets for vX.Y.Z`，没更新就查这行
- `docs/.vuepress/data/*.json` 是构建期生成的：`pnpm docs:build` / `docs:dev` 会先跑 `tools/gen-docs-downloads.mjs` 和 `tools/gen-docs-stats.mjs` 写出 release 资产和仓库规模统计。取不到数据（例如无网络的全新 clone）时脚本会写占位文件（空 assets / 全零），两个区块降级成一行提示而不是把构建带崩；上一次留下的文件如果解析不出、或缺了首页要用的字段，也会被占位覆盖而不是继续沿用。**不要手改**，改了也会被下次构建覆盖
- `HomePointerField` 里的节点名标签是从 `resource/base/pipeline/*.json` 抄来的一份静态快照，重命名或删除 pipeline 节点不会自动反映到首页

### 改首页时的验收清单

首页的自定义组件（尤其 `HomeDownload`）混合了 SSR 降级、设备识别和条件渲染，**有几类缺陷能一路穿过现有防线**，改完请按下面这张表逐项确认：

| 缺陷类型                       | `pnpm check` | `docs:build` | 浏览器控制台 | 产物检查 |
| ------------------------------ | ------------ | ------------ | ------------ | -------- |
| 模板引用了未定义的绑定         | ❌           | ❌           | ❌           | ❌       |
| 控件条件永远为假（按钮不渲染） | ❌           | ❌           | ❌           | ❌       |
| 运行时异常                     | ❌           | ❌           | ⚠️ dev 才有  | ❌       |

前两类是本项目实际踩过的坑：模板里写了一个 script 中并不存在的变量，编译期不报错、构建照常成功；Vue 生产构建又会剥离「accessed but not defined」警告；而识别类卡片在 SSR 阶段因 `detected === null` 根本不渲染，产物里也看不到。于是「构建通过 + 控制台干净」这两条证据**覆盖不到它们**。

所以验收时除了看「推荐了哪个包」，还要**验证控件本身存在且可交互**：

```js
// 在浏览器控制台跑：确认控件数量符合预期，而不是只确认推荐结果正确
document.querySelectorAll(".picked-ui-btn").length; // 桌面应为 2（MFAA/MXU），为 0 说明有问题
document.querySelector(".picked-dl")?.href; // 应指向真实资产
```

条件渲染的分支要逐个覆盖：识别成功 / 识别失败 / 架构未知 / 本机无对应包。每种情况都问一句「这个分支该出现的元素出现了吗、该消失的消失了吗」。

> 长期方案是给 `.vue` 加 `vue-tsc --noEmit`（能静态发现未定义绑定）。当前没接，因为它需要一份 `@theme/*` 等虚拟模块的 shim 声明，并且要先修掉几处既有的类型错误；收益是防一类低频、后果温和的错误，暂不值得引入。如果以后自定义组件继续膨胀、或同类问题第二次出现，再考虑接入。

## Frontmatter

常用字段：

```yaml
---
order: 1
icon: ri:tools-fill
title: 可选标题
---
```

目录索引页可用：

```yaml
---
title: 开发文档
icon: ph:code-bold
dir:
    order: 1
---
```

## 提示容器

Plume 支持 `::: <类型>` 容器语法，本站以下类型全部可用。Markdown 扩展统一在 `docs/.vuepress/config.ts` 的 `plumeTheme({ markdown })` 里配置（写到 `plume.config.ts` 顶层不会生效），新增语法前先确认依赖已安装。

| 类型        | 用途     |
| ----------- | -------- |
| `note`      | 注释     |
| `info`      | 信息     |
| `tip`       | 提示     |
| `warning`   | 警告     |
| `caution`   | 危险     |
| `important` | 重要     |
| `details`   | 折叠详情 |

::: tip
容器内可以写任意 Markdown（列表、代码块、链接）。**不要嵌套容器**：多层嵌套可能渲染异常。
:::

::: details
折叠框默认收起，点击标题展开。
:::

### 自定义标题

在类型后加一个空格写标题：

```markdown
::: tip 小提示
这里是提示内容
:::
```

### GitHub 风格警告

也支持 GitHub 风格的 `> [!NOTE]` 写法，构建时会渲染为同样的提示容器：

```markdown
> [!NOTE]
> 说明文字
```

可用 `NOTE`、`TIP`、`IMPORTANT`、`WARNING`、`CAUTION`。

## 图片

图片放在 `docs/.vuepress/public/images/` 下，按用途分子目录、用小写字母与连字符命名（如 `pipeline-flow.png`），引用时写站点绝对路径：

```markdown
![Pipeline 执行流程](/images/develop/pipeline-flow.png)
```

本站的图片插件开启了 `figure` / `lazyload` / `mark` / `size`：

- 单独成段的图片会渲染为带说明的 `<figure>`，说明文字取自 alt
- 图片默认懒加载
- 用 `=宽x高` 控制显示尺寸：`![说明](/images/develop/a.png =640x360)`
- URL 以 `#light` / `#dark` 结尾时，图片只在对应主题下显示（用于浅色 / 深色两套截图）

::: warning
图片必须放进 `docs/.vuepress/public/`（或用相对本文档的路径），并随文档一起提交。指向仓库外路径的图片不会出现在构建产物里。
:::

## 代码块

用三个反引号包裹代码并标注语言，行号默认开启。

### 行号与行高亮

在语言标识后加 `{行号,行号范围}` 高亮指定行，`{1,3-5}` 表示第 1 行与第 3 至 5 行：

````markdown
```json {2,5-7}
{
    "FarmResources.Start": {
        "recognition": "DirectHit"
    }
}
```
````

个别代码块不需要行号时，在语言标识后加 `:no-line-numbers`。

### 代码块标题

用 `title="..."` 给代码块加标题，通常写文件名：

````markdown
```json title="tasks/farm_resources.json"
{
    "FarmResources.ExitStageConfirm": {}
}
```
````

## 选项卡

用 `::: tabs` 容器组织并列的方案或示例，`@tab` 后跟标签名：

::: tabs
@tab 方案一
这是方案一的内容，可以写列表、链接等任意 Markdown。

@tab 方案二
这是方案二的内容，两个标签页在页面上切换显示。
:::

只在标签页之间对比代码时，用 `::: code-tabs`，`@tab` 后写文件名，标题会自动带上文件类型图标。

## 文件树

用 `::: file-tree` 容器展示目录结构，列表用 2 空格缩进表示层级：

```text
::: file-tree title="docs/"

- docs/
  - zh/
    - develop/
      - pipeline.md
  - en/
- resource/

:::
```

## 数学公式

本站用 KaTeX 渲染数学公式。行内公式用 `$...$`，块级公式用 `$$...$$`：

```markdown
行内：$E = mc^2$

$$
\Delta = b^2 - 4ac
$$
```

## 其他容器

`::: steps` 用来展示带序号的步骤流程：

```markdown
::: steps

1. 截图并测量 ROI
2. 编写 Pipeline 节点
3. 绑定任务并运行验证

:::
```

::: warning
本站**没有**启用图表（Mermaid / Chart.js / ECharts）、时间线（`::: timeline`）和折叠块（`::: collapse`）插件。需要这些效果时先与维护者确认依赖，不要直接写进文档。
:::

## MarkdownLint 规范

文档需符合 **MarkdownLint** 规范，配置见 `docs/.markdownlint.yaml`（规则覆盖、关闭项及原因均在其中注明）。

- 规则说明请参考 [MarkdownLint 规则](https://github.com/DavidAnson/markdownlint/blob/master/docs/RULES.md)
- 可使用 [VSCode 插件](https://github.com/DavidAnson/vscode-markdownlint) 实时提示（自动读取 `.markdownlint.yaml`）
- 仓库目前**没有**把 MarkdownLint 接进 `pnpm check` 或 CI，也没有装相关依赖 —— 它靠编辑器插件在本地生效，所以不要期待有一条失败的 CI 来提醒你
- 与 Prettier 的分工：**Prettier 负责格式**（缩进、换行、表格对齐），**MarkdownLint 负责规范**（标题层级、列表正确性、链接有效性等）。两者不冲突：`.markdownlint.yaml` 中已关闭与 Prettier 无关的噪音规则（如 MD013 行长）

## 写作要求

- 用户手册：步骤可操作，选项与 `tasks/*.json` 一致
- 开发文档：路径、命令与仓库现状一致；命令必须是 `package.json` 里真实存在的脚本；避免写已废弃的 CLI/工具
- 协议文档：描述约定与节点关系，细节以 JSON 为准并给文件路径
- 发版相关：`interface.json` 的 `version` / `title` 需手动改（见 AGENTS.md Release Guidelines）
- **中英同步**：`docs/zh/<路径>.md` 与 `docs/en/<路径>.md` 一一对应，标题层级、代码块和信息量保持一致；改完中文要顺手改英文

## 本地预览

```bash
pnpm docs:dev
pnpm docs:build
```

构建产物在 `docs/.vuepress/dist`（已 gitignore）。

- `pnpm docs:preview` 目前和站点的 `base: /MaaKEDR/` 对不上，直接开根路径会 404；要看效果请用 `pnpm docs:dev`
- 绕开 pnpm 直接跑 `vuepress dev docs` 会跳过数据生成，`docs/.vuepress/data/` 不存在时首页两个区块会直接构建失败
- `pnpm docs:build` 带 `--clean-cache --clean-temp`，会顺手清掉正在跑的 dev server，两者不要同时开

## 参考

- [VuePress Theme Plume](https://theme-plume.vuejs.press/)
- [MaaFramework 文档](https://maafw.com/docs/1.1-QuickStarted)
