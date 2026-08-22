---
order: 1
icon: ri:guide-fill
---

<!-- markdownlint-disable MD033 -->

# Getting Started

## Prerequisites

### 1. Check Your System

<div align="center">

|             |   Windows   |      macOS      |               Linux               |     Android     |
| :---------: | :---------: | :-------------: | :-------------------------------: | :-------------: |
|  Required   | Windows 10+ | Try at own risk |          Try at own risk          | Not recommended |
| Environment |     Yes     |       Yes       |                Yes                |       Yes       |
|  Emulator   |     Yes     |       Yes       | Emulator or containerized Android |       No        |
|    Usage    | GUI or CLI  |   GUI or CLI    |            GUI or CLI             |       CLI       |

| Notes                                                                                                                                                                              |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Windows: Most users should download the **x86_64** build                                                                                                                           |
| Mac: MaaKEDR supports both Apple Silicon and Intel Macs<br>Intel Mac users are advised to install Windows via Boot Camp<br>and use the Windows version of MaaKEDR with an emulator |
| Android: See [MaaFramework](https://github.com/MaaXYZ/MaaFramework/) for details<br>This method is complex and risky — not recommended for beginners                               |

</div>

---

### 2. Install Runtime Dependencies

> [!NOTE]
>
> You can skip this section for now. After downloading and extracting MaaKEDR, run the dependency installer script first. Only come back here if the script fails.

<div align="center">

<table>
  <thead>
    <tr>
        <th rowspan="2"><div align="center">Launcher</div></th>
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
        <td><div align="center">VCRedist</div></td>
        <td colspan="2"><div align="center">Download <a href="https://aka.ms/vs/17/release/vc_redist.x64.exe" target="_blank">vc_redist.x64</a></div></td>
        <td colspan="4"><div align="center">No</div></td>
    </tr>
    <tr>
        <td><div align="center">.NET</div></td>
        <td><div align="center">Yes</div></td>
        <td><div align="center">No</div></td>
        <td><div align="center">Yes</div></td>
        <td><div align="center">No</div></td>
        <td><div align="center">Yes</div></td>
        <td><div align="center">No</div></td>
    </tr>
    <tr>
       <td><div align="center">Python</div></td>
        <td colspan="6"><div align="center">Bundled — no action needed</div></td>
    </tr>
  </tbody>
</table>

</div>

#### VCRedist x64

Windows users **must install VCRedist x64**. This is required to run MaaKEDR (regardless of launcher choice).

<details>
  <summary>Installation details</summary>
  <p></p>
  <blockquote>
    <ul>
      <li>
        Direct download: click
        <a href="https://aka.ms/vs/17/release/vc_redist.x64.exe" target="_blank">vc_redist.x64</a>
        and install
      </li>
      <li>
        <code>winget</code> (admin terminal):
        <pre><code>winget install Microsoft.VCRedist.2017.x64</code></pre>
      </li>
    </ul>
  </blockquote>
</details>

#### .NET

If you use the **MFAA** GUI, you need to install .NET Desktop Runtime.

<details>
  <summary>Installation details</summary>
  <p></p>
  <blockquote>
    <ul>
      <li>
        Download from the
        <a href="https://dotnet.microsoft.com/download/dotnet" target="_blank">.NET official download page</a>
        — choose the .NET Desktop Runtime for your system.
      </li>
      <li>
        (Windows only) <code>winget</code> (admin terminal):
        <pre><code>winget install Microsoft.DotNet.DesktopRuntime.10</code></pre>
      </li>
    </ul>
  </blockquote>
</details>

#### Python

Python is bundled in the release package &mdash; no separate installation required. Linux users who prefer to manage Python themselves (not recommended) should ensure Python 3.10+ is available.

---

### 3. Download the Right Version

Download MaaKEDR from the [GitHub Releases page](https://github.com/APPLe-DF/MaaKEDR/releases). Each release provides two GUI frontends — download only one:

> [!TIP]
>
> **Trust only the official channels**: MaaKEDR is released through GitHub Releases and [Mirror酱](https://mirrorchyan.com/zh/projects?rid=MaaKEDR&source=maakedr-release) (a partner channel with content identical to the official one); some GUIs support in-app updates via Mirror酱. Downloads from other unofficial sources (lookalike sites, file-hosting reshare) carry security risks — verify the app identifier before installing.

<div align="center">

| Frontend | Suffix  | Description                                          |
| :------: | :-----: | :--------------------------------------------------- |
| **MFAA** | `-MFAA` | GUI, requires .NET Desktop Runtime, richer interface |
| **MXU**  | `-MXU`  | GUI (Unity), no additional dependencies              |

</div>

<div align="center">

|      Platform       | Download                                                |
| :-----------------: | :------------------------------------------------------ |
|   Windows x86_64    | `MaaKEDR-win-x86_64-v*-MFAA.zip` or `-MXU.zip`          |
|    Windows ARM64    | `MaaKEDR-win-aarch64-v*-MFAA.zip` or `-MXU.zip`         |
|     macOS Intel     | `MaaKEDR-macos-x86_64-v*-MFAA.tar.gz` or `-MXU.tar.gz`  |
| macOS Apple Silicon | `MaaKEDR-macos-aarch64-v*-MFAA.tar.gz` or `-MXU.tar.gz` |
|    Linux x86_64     | `MaaKEDR-linux-x86_64-v*-MFAA.tar.gz` or `-MXU.tar.gz`  |
|     Linux ARM64     | `MaaKEDR-linux-aarch64-v*-MFAA.tar.gz` or `-MXU.tar.gz` |

</div>

<details>
  <summary>How to check your Mac processor architecture</summary>
  <p></p>
  <blockquote>
    <ol>
      <li>Click the Apple logo in the top-left corner.</li>
      <li>Select "About This Mac".</li>
      <li>Check the processor information.</li>
    </ol>
    <ul>
      <li>Intel processor → download <code>-macos-x86_64-</code></li>
      <li>Apple Silicon (M1, M2, etc.) → download <code>-macos-aarch64-</code></li>
    </ul>
  </blockquote>
</details>

---

### 4. Emulator & Device Support

<div align="center">

|              |     Windows      |      macOS       | Linux | Android |
| :----------: | :--------------: | :--------------: | :---: | :-----: |
|   Emulator   | Yes (major ones) | Yes (major ones) |  DIY  |   N/A   |
| ADB required |       Yes        |       Yes        |  Yes  |   Yes   |

</div>

MaaKEDR connects to emulators/devices via ADB. Recommended emulators:

- MuMu 12
- BlueStacks 5
- LDPlayer 9
- NoxPlayer

Refer to the [MAA documentation](https://maa.plus/docs/en-us/manual/device/windows.html) for emulator compatibility details.

---

### 5. Set the Correct Resolution

MaaKEDR requires a **16:9 landscape** resolution. The recommended (and minimum) resolution is **1280x720**. Issues caused by incorrect resolution will not be addressed.

> [!WARNING]
>
> Make sure your emulator is in landscape (tablet) mode, not portrait (phone) mode!

---

### 6. Getting Started

> [!IMPORTANT]
> Do not run the program directly from within the archive!

Extract the archive to a dedicated folder. Recommended path: `D:\MaaKEDR` (Windows) or `~/MaaKEDR` (macOS/Linux). Avoid paths that require administrator privileges (e.g. `C:\Program Files\`).

#### Windows

Extract and run `maakedr.exe`.

#### macOS

<details>
  <summary>Details</summary>
  <p></p>
  <blockquote>

1. Open Terminal and extract:

    ```shell
    mkdir -p ~/MaaKEDR
    tar -xzf ~/Downloads/MaaKEDR-macos-*.tar.gz -C ~/MaaKEDR
    ```

2. Enter the directory and launch:

    ```shell
    cd ~/MaaKEDR
    ./maakedr
    ```

**Gatekeeper warning:**

On macOS 10.15+ you may see "cannot be opened because the developer cannot be verified". To bypass:

```shell
sudo xattr -rd com.apple.quarantine ~/MaaKEDR/maakedr
```

  </blockquote>
</details>

#### Linux

Same as macOS — extract the appropriate archive and run `./maakedr`.

---

### 7. Configure MaaKEDR

#### First Launch

On first launch, MaaKEDR automatically initializes and creates the `config/` directory. Wait for "AgentServer started" in the log panel, and do not click "Stop" until "All tasks completed" appears.

#### Resource Type

Select the server version of _雪松 (KEDR)_ installed in your emulator:

- **Official** (`base`)
- **Bilibili** (`bilibili`)
- **TapTap** (`taptap`)

#### Connection

MaaKEDR needs a correct ADB connection to your target emulator. In most cases, just keep your target emulator running and click "Refresh".

- **Refresh**: Rescan all running emulators
- **Custom**: Modify ADB parameters (usually not needed)
- **Reconnect**: Reconnect to the selected emulator

#### Task List

MaaKEDR provides these automation tasks:

| Task           | Description                                         |
| -------------- | --------------------------------------------------- |
| Launch Game    | From launcher to main menu                          |
| Claim Rewards  | Daily check-in, weekly, battle pass, mail, dispatch |
| Farm Resources | Auto-battle with stamina management                 |
| PVP            | Arena auto-battle                                   |

> [!IMPORTANT]
>
> Most tasks require proper configuration before use. Read each task's **description** carefully and adjust **settings** according to your needs.

#### Configuration Files

On first launch, MaaKEDR generates configuration files in the `config/` directory. You can edit these with a text editor.

<details>
  <summary>config/pip_config.json</summary>
  <p></p>
  <blockquote>

pip installation settings. In most cases, no changes are needed.

```jsonc
{
    "enable_pip_install": true, // Enable pip install, default true
    "mirror": "https://pypi.tuna.tsinghua.edu.cn/simple", // PyPI mirror
    "backup_mirror": "https://mirrors.ustc.edu.cn/pypi/simple", // Backup mirror
}
```

  </blockquote>
</details>

---

## FAQ

### Cannot connect to emulator

- Make sure ADB debugging is enabled in your emulator
- Try `adb devices` to verify the connection
- Check the ADB port: MuMu uses `127.0.0.1:16384`, BlueStacks uses `127.0.0.1:5555`

### Tasks fail during execution

- Ensure the game is on the correct screen (main menu or target feature page)
- Check screenshots in the `debug/` directory to verify recognition accuracy
- Review `debug/maafw.log` for error details
