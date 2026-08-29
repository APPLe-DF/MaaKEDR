---
order: 1
icon: ri:guide-fill
---

<!-- markdownlint-disable MD033 -->

# 新手上路

## 前置准备

### 1. 确认版本系统

<div align="center">

|              |      Windows      |      macOS       |       Linux        | Android |
| :----------: | :---------------: | :--------------: | :----------------: | :-----: |
|   系统要求   | Windows 10 及以上 |     自行尝试     |      自行尝试      | 不推荐  |
| 需要配置环境 |        是         |        是        |         是         |   是    |
|  需要模拟器  |        是         |        是        | 模拟器或容器化安卓 |   否    |
|   使用方式   | 图形界面或命令行  | 图形界面或命令行 |  图形界面或命令行  | 命令行  |

|              | 备注                                                                                                                                                                     |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Windows 用户 | 绝大部分情况请下载 x86_64 架构                                                                                                                                           |
| Mac 用户     | MaaKEDR 同时支持搭载 Apple Silicon 和 Intel 芯片的 Mac 电脑<br>但更推荐搭载 Intel 芯片的 Mac 电脑使用 Mac 自带的多系统安装 Windows<br>并使用 Windows 版 MaaKEDR 和模拟器 |
| Android 用户 | 请前往 [MaaFramework](https://github.com/MaaXYZ/MaaFramework/) 自行查看<br>此方法较为复杂且具有一定风险，不推荐入门玩家使用此方法                                        |

</div>

---

### 2. 安装运行环境

> [!NOTE]
>
> 用户可跳过这节，在下一步下载解压后运行依赖库安装脚本，脚本自动安装失败后再看这节

<div align="center">

<table>
  <thead>
    <tr>
        <th rowspan="2"><div align="center">启动方式</div></th>
        <th colspan="2"><div align="center">Windows</div></th>
        <th colspan="2"><div align="center">macOS</div></th>
        <th colspan="2"><div align="center">Linux</div></th>
    </tr>
    <tr>
        <th><div align="center">MFAA</div></th>
        <th><div align="center">MXU</div></th>
        <th><div align="center">MFAA</div></th>
        <th><div align="center">MXU</div></th>
        <th><div align="center">MFAA</div></th>
        <th><div align="center">MXU</div></th>
    </tr>
  </thead>
  <tbody>
    <tr>
        <td><div align="center">需安装 VCRedist</div></td>
        <td colspan="2"><div align="center">点击 <a href="https://aka.ms/vs/17/release/vc_redist.x64.exe" target="_blank">vc_redist.x64</a> 下载</div></td>
        <td colspan="4"><div align="center">否</div></td>
    </tr>
    <tr>
        <td><div align="center">需安装 .NET</div></td>
        <td><div align="center">是</div></td>
        <td><div align="center">否</div></td>
        <td><div align="center">是</div></td>
        <td><div align="center">否</div></td>
        <td><div align="center">是</div></td>
        <td><div align="center">否</div></td>
    </tr>
    <tr>
       <td><div align="center">需安装 Python</div></td>
        <td colspan="4"><div align="center">压缩包自带，无需其他操作</div></td>
        <td colspan="2"><div align="center">需要 Python 3.13</div></td>
    </tr>
  </tbody>
</table>

</div>

#### VCRedist x64

Windows 用户**必须安装 VCRedist x64**：这是运行 MaaKEDR（无论哪种启动方式）的基础需求。

<details>
  <summary>详细安装方式</summary>
  <p></p>
  <blockquote>
    <ul>
      <li>
        直接下载：点击
        <a href="https://aka.ms/vs/17/release/vc_redist.x64.exe" target="_blank">vc_redist.x64</a>
        下载并安装
      </li>
      <li>
        <code>winget</code> 安装（管理员终端）：
        <pre><code>winget install Microsoft.VCRedist.2017.x64</code></pre>
      </li>
    </ul>
  </blockquote>
</details>

#### .NET

使用 **MFAA** 图形界面的用户需要自行安装 **.NET 10** 桌面运行时。

<details>
  <summary>详细安装方式</summary>
  <p></p>
  <blockquote>
    <ul>
      <li>
        自行下载：点击
        <a href="https://dotnet.microsoft.com/zh-cn/download/dotnet/10.0" target="_blank">.NET 官方下载页面</a>
        ，选择您系统对应的 .NET 10 桌面运行时版本下载并安装。
      </li>
      <li>
        （仅 Windows 用户）<code>winget</code> 安装（管理员终端）：
        <pre><code>winget install Microsoft.DotNet.DesktopRuntime.10</code></pre>
      </li>
    </ul>
  </blockquote>
</details>

#### Python

Windows 与 macOS 压缩包已内置 Python 运行环境，无需单独安装。Linux 压缩包不内置 Python，需自行安装 **Python 3.13**。

---

### 3. 下载正确的版本

MaaKEDR 下载地址：[GitHub 发布页](https://github.com/APPLe-DF/MaaKEDR/releases)。点击链接后，在 `Assets` 处选择适配您系统的最新版压缩包下载。

> [!TIP]
>
> **认准官方渠道**：MaaKEDR 通过 GitHub Releases 与 [Mirror酱](https://mirrorchyan.com/zh/projects?rid=MaaKEDR&source=maakedr-release)（合作渠道，内容与官方一致）双渠道发布，部分图形界面支持通过 Mirror酱 界面内自动更新。从其他非官方渠道（仿冒网站、网盘转发等）下载存在安全风险，安装前请核对应用标识。

每个版本提供两种图形前端，按需下载其一即可：

<div align="center">

|   前端   |  后缀   | 说明                                         |
| :------: | :-----: | :------------------------------------------- |
| **MFAA** | `-MFAA` | 图形界面，需安装 .NET 桌面运行时，界面更丰富 |
| **MXU**  | `-MXU`  | 图形界面（Unity 版），无需额外依赖           |

</div>

<div align="center">

|        系统         | 下载文件                                                |
| :-----------------: | :------------------------------------------------------ |
|   Windows x86_64    | `MaaKEDR-win-x86_64-v*-MFAA.zip` 或 `-MXU.zip`          |
|    Windows ARM64    | `MaaKEDR-win-aarch64-v*-MFAA.zip` 或 `-MXU.zip`         |
|     macOS Intel     | `MaaKEDR-macos-x86_64-v*-MFAA.tar.gz` 或 `-MXU.tar.gz`  |
| macOS Apple Silicon | `MaaKEDR-macos-aarch64-v*-MFAA.tar.gz` 或 `-MXU.tar.gz` |
|    Linux x86_64     | `MaaKEDR-linux-x86_64-v*-MFAA.tar.gz` 或 `-MXU.tar.gz`  |
|     Linux ARM64     | `MaaKEDR-linux-aarch64-v*-MFAA.tar.gz` 或 `-MXU.tar.gz` |

</div>

<details>
  <summary>Mac 用户查看处理器架构方法</summary>
  <p></p>
  <blockquote>
    <ol>
      <li>点击屏幕左上角的苹果标志。</li>
      <li>选择"关于本机"。</li>
      <li>在弹出的窗口中，你可以看到处理器的信息。</li>
    </ol>
    <ul>
      <li>若使用 Intel 处理器，请下载 <code>-macos-x86_64-</code> 版本</li>
      <li>若使用 Apple Silicon（如 M1、M2 等），请下载 <code>-macos-aarch64-</code> 版本</li>
    </ul>
  </blockquote>
</details>

---

### 4. 确认模拟器和设备支持

<div align="center">

|            |    Windows     |     macOS      |  Linux   | Android |
| :--------: | :------------: | :------------: | :------: | :-----: |
| 模拟器支持 | 支持主流模拟器 | 支持主流模拟器 | 自行尝试 |    /    |
|  需要 ADB  |       是       |       是       |    是    |   是    |

</div>

MaaKEDR 通过 ADB 连接模拟器或设备。推荐使用以下模拟器：

- MuMu 模拟器 12
- BlueStacks 5
- LDPlayer 9
- 夜神模拟器

模拟器支持详情可参阅 [MAA 文档](https://maa.plus/docs/zh-cn/manual/device/windows.html)。

---

### 5. 正确设置分辨率

MaaKEDR 支持主流模拟器，但您需要设置模拟器分辨率以达到运行要求。
分辨率应为 **横屏 16:9 比例**，推荐（以及最低）分辨率为 **1280x720**，不符合要求造成的运行报错将不会被解决。

> [!WARNING]
>
> 注意修改分辨率后模拟器主页应该是横屏（平板版），不要选成竖屏（手机版）了！

---

### 6. 开始使用

> [!IMPORTANT]
> 不要在压缩软件中直接运行程序！

确认解压完整，并确保将 MaaKEDR 解压到一个独立的文件夹中。推荐解压路径如 `D:\MaaKEDR`。请勿将程序解压到如 `C:\`、`C:\Program Files\` 等需要 UAC 权限的路径。

#### Windows

解压后运行 `maakedr.exe` 即可。

#### macOS

<details>
  <summary>详情</summary>
  <p></p>
  <blockquote>

1. 打开终端，解压压缩包：

    ```shell
    mkdir -p ~/MaaKEDR
    tar -xzf ~/Downloads/MaaKEDR-macos-*.tar.gz -C ~/MaaKEDR
    ```

2. 进入解压目录并运行程序：

    ```shell
    cd ~/MaaKEDR
    ./maakedr
    ```

**Gatekeeper 安全提示：**

macOS 10.15（Catalina）及更高版本可能会阻止运行未签名的应用程序。如果遇到"无法打开，因为无法验证开发者"等错误：

```shell
sudo xattr -rd com.apple.quarantine ~/MaaKEDR/maakedr
```

  </blockquote>
</details>

#### Linux

同 macOS，下载对应版本的压缩包，解压后运行 `maakedr` 即可。

---

### 7. 配置 MaaKEDR

#### 首次启动

首次启动 MaaKEDR 后，程序会自动初始化并创建 `config/` 配置目录。在 **日志** 板块显示"AgentServer 启动"后，直到看见"任务已全部完成"前，请不要点击停止任务。

#### 资源类型

需选择模拟器中安装的《雪松》区服。目前支持：

- **官服**（base）
- **B 服**（bilibili）
- **TapTap 服**（taptap）

#### 连接

MaaKEDR 需正确的 ADB 连接才能在目标模拟器执行任务。绝大多数情况下，您只需保持有且仅有目标模拟器启动，点击"刷新"即可完成连接。

- **刷新**：重新检测所有已启动模拟器
- **自定义**：修改 ADB 参数（一般无需手动修改）
- **重新连接**：重新连接已选定模拟器

#### 任务列表

MaaKEDR 提供以下自动化任务：

| 任务         | 功能                                             |
| ------------ | ------------------------------------------------ |
| 启动游戏     | 从启动到登录至主界面                             |
| 领取奖励     | 日常签到、周常奖励、战令奖励、邮件奖励、派遣奖励 |
| 资源刷取     | 指定关卡自动刷资源，支持体力管理                 |
| 剩余体力刷取 | 固定清空体力模式，榨干剩余体力                   |
| 活动关卡刷取 | 活动关卡扫荡（每日 3 次，不消耗体力）            |
| 活动商店兑换 | 活动商店定额保障商品自动购买                     |
| PVP          | 竞技场自动战斗                                   |
| 体力信息     | 读取主界面体力并输出回满时间                     |

> [!IMPORTANT]
>
> 大部分任务需在使用前正确配置。启用任务前，请确保您已阅读并理解了该任务的**任务说明**，并结合实际情况对**任务设置**进行配置。

#### 配置文件

MaaKEDR 首次运行时会自动在 `config/` 目录下生成配置文件，您可以用文本编辑器手动修改。

<details>
  <summary>config/pip_config.json</summary>
  <p></p>
  <blockquote>

pip 安装相关设置。一般情况下，您无需修改此文件，除非您有特殊需求。

```jsonc
{
    "enable_pip_install": true, // 是否启用 pip 安装，默认 true
    "mirror": "https://pypi.tuna.tsinghua.edu.cn/simple", // 镜像源
    "backup_mirror": "https://mirrors.ustc.edu.cn/pypi/simple", // 备用镜像源
}
```

  </blockquote>
</details>

---

## 常见问题

### 无法连接模拟器

- 确认模拟器的 ADB 调试已开启
- 尝试使用 `adb devices` 命令检测设备是否正常连接
- 检查模拟器 ADB 端口：MuMu 为 `127.0.0.1:16384`，BlueStacks 为 `127.0.0.1:5555`

### 任务执行异常

- 确认游戏处于正确的界面（如在主菜单或对应功能页面）
- 查看 `debug/` 目录下的截图，确认识别区域是否正确
- 查看 `maafw.log` 日志文件（项目根目录）定位问题
