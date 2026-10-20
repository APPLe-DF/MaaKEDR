# Android 客户端

MaaKEDR 的 Android 版通过 [MaaFwApp](https://github.com/Aliothmoon/MaaFwApp) 出包。外壳以 git
子模块形式放在 `MaaFwApp/`，本目录只放打包配方 `profile.yaml`：它指明资源在哪、包名与图标、
agent 怎么拉起。换资源 = 改资源 + 重新出包，不改外壳代码。

> 本文件只做目录入口。**出包步骤、版本对齐、签名、CI 与 Mirror酱分发以开发文档为准**，
> 避免这里的内容随流程变化而过期。

## 目录内容

```text
Android/
├── profile.yaml    # 打包配方（进 git，本地与 CI 共用）
├── MaaFwApp/       # 外壳子模块，见 .gitmodules
├── agent-dist/     # build_agent_bundle.py 产物（gitignore，需本地生成）
└── README.md       # 本文件
```

仓库根另有 `logo.png`，由 `tools/make_android_icon.py` 生成（gitignore），配方的
`app.icon` 指向它。

## 从这里开始

- [安卓打包（MaaFwApp）](../docs/zh/develop/android.md) — 目录约定、环境要求、本地出包、
  三条并行流水线、版本解析器、必需的 Secrets、Mirror酱分发（rid `MaaKEDR_exec`）
- [Android packaging (MaaFwApp)](../docs/en/develop/android.md) — 英文版
- [Android/profile.yaml](./profile.yaml) — 配方本体，含版本对齐与运行屏配置的注释

## 首次使用

子模块未初始化时先拉取：

```bash
git submodule update --init --recursive Android/MaaFwApp
```

后续出包步骤见上述开发文档的「本地复现 CI 出包」一节。
