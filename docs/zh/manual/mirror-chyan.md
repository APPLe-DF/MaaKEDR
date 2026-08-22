---
order: 7
icon: ic:outline-fast-forward
---

# Mirror酱使用说明

Mirror酱（[官网](https://mirrorchyan.com/zh/projects?rid=MaaKEDR&source=maakedr-release)）是 MaaKEDR 的合作分发与更新平台，让开源应用的更新更简单，发布内容与官方渠道保持一致。用户付费使用，收益与开发者共享，Mirror酱本身也是开源的。

当您访问或使用该服务时，便表示您同意接受[Mirror酱服务条款](https://mirrorchyan.com/disclaimer.html)所有条款的约束。

> MaaKEDR 的官方发布渠道为 **GitHub Releases** 与 **Mirror酱** 双渠道，内容一致：源码、校验信息与历史版本发布在 [MaaKEDR Releases](https://github.com/APPLe-DF/MaaKEDR/releases)，Mirror酱 作为合作渠道与之一致同步（`mirrorchyan_rid: MaaKEDR`），两个渠道下载/更新的内容保持一致。

## 在图形界面中更新

部分 MaaFramework 图形界面（如 [MFAAvalonia](https://github.com/SweetSmellFox/MFAAvalonia)、[MXU](https://github.com/MaaXYZ/MXU)）内置了通过 Mirror酱 更新应用与资源的功能，在对应设置界面中开启即可（MaaKEDR 发布包已包含 `mirrorchyan_rid` 配置）。

## 在网页端使用

1. 打开 [Mirror酱官网](https://mirrorchyan.com/zh/projects?rid=MaaKEDR&source=maakedr-release)
2. 搜索 `MaaKEDR`
3. 可执行安装、更新、历史版本下载与捐赠等操作

## 常见问题

### 镜像更新后任务异常

Mirror酱 更新的是应用与资源文件，不会改动模拟器连接与分辨率设置。若更新后任务异常，请：

1. 检查分辨率是否仍为 1280×720（见 [正确设置分辨率](./newbie.md)）
2. 检查连接是否正常（见 [连接设置](./connection.md)）
3. 若仍异常，请到 [GitHub Issues](https://github.com/APPLe-DF/MaaKEDR/issues) 反馈，并附上运行日志（见 [Bug 排查](../develop/fix.md)）
