---
title: "安卓打包（MaaFwApp）"
order: 10
icon: "ri:android-fill"
---

# 安卓打包（MaaFwApp）

MaaKEDR 的安卓版通过 [MaaFwApp](https://github.com/Aliothmoon/MaaFwApp) 出包。MaaFwApp 是
MaaFramework 的通用 Android GUI，在**构建期**把一份 Project Interface V2 资源打进 APK，运行时
通过 [Shizuku](https://shizuku.rikka.app/) 或 root 拉起特权进程，截屏与点击走本机 native
controller，不经过 adb。

接入模型（与 MAA1999/M9A、Saratoga-Official/MRA 相同）：MaaFwApp 以 git 子模块形式放在
`Android/MaaFwApp`，MaaKEDR 只提供打包配方 `Android/profile.yaml`（指明资源在哪、包名与
图标、agent 怎么拉起）。换资源 = 改资源 + 重新出包，不改外壳代码。

> 资源随 APK 绑定，Android 端不支持热更新，暂不支持 Mirror酱 CDN。

## 目录约定

```text
MaaKEDR/
├── Android/
│   ├── profile.yaml            # 打包配方（进 git，本地与 CI 共用）
│   └── MaaFwApp/               # 外壳子模块
├── agent-dist/                 # build_agent_bundle.py 产物（gitignore）
├── logo.png                    # make_android_icon.py 产物（gitignore）
└── …                           # PI 本体：interface.json、tasks/、resource/、agent/
```

MaaKEDR 的 PI 是扁平布局（`interface.json`、`tasks/`、`resource/`、`agent/` 均在仓库根），
配方的 `assets: ..` 直接引用，**不需要** staging 脚本；`agent/**` 与 `logo.png` 不在 MaaFwApp
的默认 include 白名单里，已在配方中显式列出。

## 环境要求

- JDK 17（AGP 9 / Gradle 9.4 的编译基线）
- Android SDK：platform-tools、platforms;android-37.0、build-tools;37.0.0
- Python 3（下载 MaaFramework 产物、组装 agent 运行时），生成图标还需 Pillow

## 版本对齐

安卓上 agent 用的 `maa` Python 绑定和它背后的 MaaFramework 都来自 agent 内核
[MaaAgentCoreAndroid](https://github.com/Aliothmoon/MaaAgentCoreAndroid)，APK 里 client 侧的
MaaFramework `.so` 必须与内核同版本，否则前后端协议不一致。本项目的钉法写死在
`Android/profile.yaml` 顶部注释里：

| 组件               | 版本                                                                       |
| :----------------- | :------------------------------------------------------------------------- |
| Agent 内核         | `3.13.15-maafw5.14.2`（`build_agent_bundle.py --core-tag`）                |
| MaaFramework `.so` | `v5.14.2`（`setup_maa_framework.py --tag`）                                |
| 桌面端 pin         | `maafw==5.14.2`（requirements.txt，内核自带同版本 maa 源码，会被自动跳过） |

升级时三处一起改。`requirements.txt` 里桌面端的 `maafw` 条目会被
`build_agent_bundle.py` 丢弃（公开索引没有 Android 版轮子），不影响安卓。

## 本地出包

日常分发用 **release** 变体：R8 代码收缩（dex 75.5M → 6.7M）、不带 debug 专属的 Perfetto
tracing，比 debug 小一半以上（实测 151.5M → 约 70M）。debug 变体仅用于开发期排障。

```bash
# 1. 子模块（已 clone 过的仓库执行）
git submodule update --init --recursive

# 2. 图标（logo.ico → logo.png，每次构建前跑一次即可）
python tools/make_android_icon.py

# 3. 铺 MaaFramework 的 Android .so 与 agent 运行时
cd Android/MaaFwApp
python scripts/setup_maa_framework.py --abi arm64-v8a --tag v5.14.2
python scripts/build_agent_bundle.py --out ../agent-dist \
    --core-tag 3.13.15-maafw5.14.2 --abi arm64-v8a \
    --requirements ../../requirements.txt

# 4. agent 运行时瘦身：只删无用的 sqlite3（maa 与 agent 均不 import）。
#    注意：不要删 numpy 的 BLAS（libopenblas）——numpy 的
#    _core/_multiarray_umath 与 linalg 经 ELF DT_NEEDED 硬链接它，删了
#    import numpy 直接失败（真机踩过）；见 tools/trim_agent_bundle.py 头注释。
python ../../tools/trim_agent_bundle.py

# 5. 指定 SDK、配方、ABI 与签名（Android/MaaFwApp/local.properties，不进 git）
cat > local.properties <<EOF
sdk.dir=<你的 Android SDK 路径>
pi.profile=<MaaKEDR 仓库绝对路径>/Android/profile.yaml
build.debugAbi=arm64-v8a
build.releaseAbi=arm64-v8a   # release 必须写明——不写默认双 ABI（含 x86_64），
#                             而 agent-dist 与 jniLibs 只有 arm64-v8a，会打出缺 MaaFramework.so 的 APK
KEYSTORE_PATH=<keystore 路径>
KEYSTORE_PASSWORD=<store 密码>
KEY_ALIAS=<别名>
KEY_PASSWORD=<key 密码>
EOF

# 6. 出 release 包（未配签名时产物为未签名包，装不上）
./gradlew :app:assembleRelease

# 7. dex 重压缩：AGP 9 默认 dex 以 STORED 写入，本步改 deflate 再 zipalign + 重签名，
#    整包再省约 3.4M（签名沿用第 5 步的 keystore）
python ../../tools/shrink_apk.py app/build/outputs/apk/release/app-release.apk

# 8. 收集到 dist/package-maafwapp/，文件名带构建日期后缀便于区分多次构建
python ../../tools/collect_android_apk.py release
```

产物在 `Android/MaaFwApp/app/build/outputs/apk/release/`。签名缺省时 `assembleRelease`
出未签名包；本地测试可直接用 debug keystore（`~/.android/debug.keystore`，store/key 密码
均为 `android`，别名 `androiddebugkey`）——与 debug 包同签名，可互相覆盖安装。正式分发
应换正式 keystore。

改了 `agent/`、`requirements.txt` 或图标后重跑第 2-4 步；改 `tasks/`、`resource/` 直接重新
出包即可。换了资源重装后设备仍是旧内容时，清一下应用数据。

> **增量构建的体积陷阱**：外壳打包时会就地更新 APK 内的 `assets/pi.zip`，被替换掉的旧
> pi.zip 数据会成为孤儿条目留在文件里（中央目录只登记新条目，能正常安装，但体积会翻倍
> 累积）。发现 APK 异常变大时，删掉旧产物再重新出包即可得到紧凑的包：
>
> ```bash
> rm Android/MaaFwApp/app/build/outputs/apk/release/app-release.apk
> ./gradlew :app:assembleRelease
> ```

### Release 包与签名

签名配置见上文第 5 步（`local.properties` 或环境变量）。release 出双 ABI
（arm64-v8a + x86_64）时，`setup_maa_framework.py` 与 `build_agent_bundle.py` 都要加
`--abi x86_64`，并在 `local.properties` 写 `build.releaseAbi=arm64-v8a,x86_64`。

## CI 出包（GitHub Actions）

本地 8 步流程已固化为可复用流水线 `.github/workflows/android-build.yml`，由两个调用方驱动：

| 调用方        | 触发                                           | 产物                                 |
| :------------ | :--------------------------------------------- | :----------------------------------- |
| `android.yml` | push/PR 命中 Android 相关路径、或手动 dispatch | debug 包（手动可选 release）         |
| `release.yml` | `v*` tag                                       | release 三包，与桌面包一起进 Release |

### 三条并行流水线

```text
library-resources  ── JDK + SDK，跑 verifyReleaseResources（库模块资源校验，20 min）
build              ── universal 包：debug 时单 ABI，release 时 arm64-v8a + x86_64
abi-split          ── 仅 release：矩阵 [arm64-v8a, x86_64]，各出单 ABI 包（体积约一半）
```

release 产出三个 APK：`MaaKEDR-android-universal-<tag>.apk` 与两个 `MaaKEDR-android-<abi>-<tag>.apk`。
**命名不能随意改**：应用内更新按 asset 名选包（`GitHubUpdate.selectAsset`），universal 包一旦带上
ABI 标记就会绕过回退逻辑。

### 版本解析器（不要手工钉版本）

`tools/android-packaging.mjs` 从 `requirements.txt` 的 `maafw==X` 解析版本，再去
[MaaAgentCoreAndroid](https://github.com/AliothMoon/MaaAgentCoreAndroid) 找 `*-maafwX` 配对的内核
release，输出 `core_tag` / `maafw_tag` / `chaquopy_pins` 等给后续步骤：

```bash
node tools/android-packaging.mjs
# agent core tag   : 3.13.15-maafw5.14.2
# client MaaFW tag : v5.14.2
# has agent        : true
```

内核还没出配对版本时会**降级到不高于固定版本的最近配对**并打 warning——APK 内前后端仍同版本，
只是比 `requirements.txt` 固定的旧。上游发版后降级自动消失，**不需要改工作流**。

### 必需的 Secrets

| Secret              | 用途                    | 缺失时                                     |
| :------------------ | :---------------------- | :----------------------------------------- |
| `KEYSTORE_BASE64`   | 签名 keystore 的 base64 | PR/dispatch 出未签名包；**tag 上直接失败** |
| `KEYSTORE_PASSWORD` | store 密码              | 同上                                       |
| `KEY_ALIAS`         | 别名                    | 同上                                       |
| `KEY_PASSWORD`      | key 密码                | 同上                                       |
| `GITHUB_TOKEN`      | 解析版本、下载产物      | 内置，无需配置                             |

生成 base64（Windows）：

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\path\to\release.jks"))
```

> tag 发版缺签名材料会**当场失败**而不是出一个装不上的包——这是刻意的：未签名 APK 进不了应用内更新。

### CI 与本地流程的差异

CI 比本地多做了三件事，本地手工出包时容易漏：

1. **生成图标**：`logo.png` 在 `.gitignore` 里（是 `logo.ico` 的转换产物），CI 显式跑
   `make_android_icon.py` 并装 Pillow。本地忘了跑，外壳会因图标缺失报错。
2. **同步 OCR 模型**：`resource/base/model/ocr/` 来自 MaaCommonAssets 子模块、不进 git，CI 用
   `pnpm dlx create-maa-project@latest --update ocr-models` 铺。
3. **native 库自检**：出包后用 `unzip -Z1` + `grep -Fx` 逐 ABI 校验
   `libMaaFramework.so` / `libMaaUtils.so` / `libMaaAndroidNativeControlUnit.so`（agent 项目再加
   `libMaaAgentServer.so`）。少铺一个 .so 不会让打包失败，要到设备上才发现起不来。

### 本地复现 CI 出包

```bash
node tools/android-packaging.mjs          # 先看解析出的版本
# 其余步骤同「本地出包」，注意上面三处差异
```

### Mirror酱 分发（需单独申请 Android rid）

Android 包**不能复用桌面的 `mirrorchyan_rid`**。两者是 Mirror酱 上的不同产品条目：

|          | 桌面包（MFAA / MXU）      | Android APK                     |
| :------- | :------------------------ | :------------------------------ |
| 内容     | 只有资源，用户已有 GUI    | 自带 GUI + Python 运行时 + 资源 |
| rid      | `MaaKEDR` / `MaaKEDR-MXU` | 需单独申请                      |
| 更新方式 | 资源热替换                | 整包覆盖安装                    |

> **状态：待申请。** 该 rid 尚未在 Mirror酱 后台登记，`mirrorchyan_android` job 默认不会被触发
> （`android` 输入默认 false）。申请到之后需要改两处：
>
> 1. `.github/workflows/mirrorchyan_release.yml` 的 `mirrorchyan_rid`（当前是占位
>    `MaaKEDR-Android-PENDING`）
> 2. `Android/profile.yaml` 加 `update.mirrorchyanRid`——它**压过** PI 的 `mirrorchyan_rid`，
>    桌面端不受影响：
>
>     ```yaml
>     update:
>         mirrorchyanRid: <申请的 rid>
>     ```
>
> 未开通前**不要**写死 rid：App 的更新检查会拿它去查 `/api/resources/<rid>/latest`，rid 不存在
> 就是一次失败（不致命，但每次检查都会报错）。另外 Mirror酱 下载需要 CDK，无 CDK 时
> `resolve` 会直接返回 `CDK_REQUIRED`，只做「检查有无新版本」不受影响。

上传由 `mirrorchyan_release.yml` 的 `mirrorchyan_android` job 负责，`release.yml` 建完 Release
后统一派发（`client_payload.android=true`），桌面与 Android 一次传完。手动触发时勾选
`android` 输入即可单独跑。

## agent 入口约定

MaaFwApp 拉起 agent 时使用配方的 `runtimes`，忽略 PI 的 `child_exec` / `child_args`。本项目
入口固定为 `agent/main.py` 而非 `agent/bootstrap.py`：bootstrap 面向桌面 uv 工作流，其
Linux venv 分支会在 Android（`sys.platform == "android"`）误触发，且设备上无法 pip install。
`agent/maafw_paths.py` 检测到 App 注入的 `MAAFW_BINARY_PATH`（指向 APK 的
nativeLibraryDir）后直接沿用，桌面 `runtimes/` 布局逻辑不会介入。

## 运行要求与模式

MaaKEDR 的 ROI / 坐标 / 模板图以 1280x720（16:9）为基准，agent 启动任务时会强制校验
分辨率（`agent/custom/sink/aspect_ratio.py`）。因此：

- **后台模式**（虚拟屏，720P/1080P）分辨率即 16:9，直接可用，也是推荐用法；
- **前台模式**用的是手机物理屏（如 1260x2800），非 16:9，任务会被主动拦停并提示。

## 常见问题

| 现象                               | 原因                                                                            |
| :--------------------------------- | :------------------------------------------------------------------------------ |
| 能安装，一点开始就 native 加载失败 | `setup_maa_framework.py` 未跑，或 ABI 与 `build.debugAbi` 不一致                |
| 开始任务提示「Agent 启动失败」     | 具体原因在 `adb logcat -s MaaFw` 的 `MaaRunner: prepare failed: agent[0]:` 一行 |
| 报 agent 协议错误                  | client 侧 `.so` 与 agent 内核的 MaaFramework 版本不一致，见「版本对齐」         |
| 图标不显示                         | `logo.png` 没跑 `tools/make_android_icon.py` 生成，或不在配方 `include` 里      |
| 换了资源重装还是旧内容             | 版本号未变时可能沿用旧解包，清应用数据                                          |
