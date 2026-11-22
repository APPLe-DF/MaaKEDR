---
order: 1
icon: ri:guide-fill
---

<!-- markdownlint-disable MD033 -->

# Getting Started

## Prerequisites

### 1. Check Your System

<div align="center">

|             |   Windows   |      macOS      |               Linux               |               Android                |
| :---------: | :---------: | :-------------: | :-------------------------------: | :----------------------------------: |
|  Required   | Windows 10+ | Try at own risk |          Try at own risk          |             Android 10+              |
| Environment |     Yes     |       Yes       |                Yes                |                  No                  |
|  Emulator   |     Yes     |       Yes       | Emulator or containerized Android |                  No                  |
|    Usage    | GUI or CLI  |   GUI or CLI    |            GUI or CLI             |                 GUI                  |
| Also needs  |    None     |      None       |               None                | Shizuku or root (see the note below) |

| Notes                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Windows: Most users should download the **x86_64** build                                                                                                                                                                                                                                                                                                                                                                                    |
| Mac: MaaKEDR supports both Apple Silicon and Intel Macs<br>Intel Mac users are advised to install Windows via Boot Camp<br>and use the Windows version of MaaKEDR with an emulator                                                                                                                                                                                                                                                          |
| Android: MaaKEDR ships an Android client (see [Releases](https://github.com/APPLe-DF/MaaKEDR/releases); `MaaKEDR-android-arm64-v8a-<version>.apk` for phones, `MaaKEDR-android-x86_64-<version>.apk` for x86 emulators)<br>Requires Android 10+ (background mode only; the system virtual display needs API 29); grant notification permission and add the app to the battery allowlist on first launch, then authorize via Shizuku or root |

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
        <td colspan="4"><div align="center">Bundled — no action needed</div></td>
        <td colspan="2"><div align="center">Python 3.13 required</div></td>
    </tr>
  </tbody>
</table>

</div>

#### VCRedist x64

Windows users **must install VCRedist x64**. This is required to run MaaKEDR (regardless of launcher choice).

::: details Installation details

- Direct download: click [vc_redist.x64](https://aka.ms/vs/17/release/vc_redist.x64.exe) and install
- `winget` (admin terminal):

```powershell
winget install Microsoft.VCRedist.2017.x64
```

:::

#### .NET

If you use the **MFAA** GUI, you need to install **.NET 10**. On Windows that means the **.NET Desktop Runtime**; on macOS and Linux it is the plain **.NET Runtime** (not the desktop one) — pick the matching build on the same download page.

::: details Installation details

- Download from the [.NET official download page](https://dotnet.microsoft.com/en-us/download/dotnet/10.0) — choose the .NET 10 Desktop Runtime for your system.
- (Windows only) `winget` (admin terminal):

```powershell
winget install Microsoft.DotNet.DesktopRuntime.10
```

:::

#### Python

Python is bundled in the Windows and macOS release packages &mdash; no separate installation required. The Linux release does **not** bundle Python; install **Python 3.13** manually.

---

### 3. Download the Right Version

Download MaaKEDR from the [GitHub Releases page](https://github.com/APPLe-DF/MaaKEDR/releases). Users who have a MirrorChyan CDK can also download directly from the [MirrorChyan direct link](https://mirrorchyan.com/en/projects?rid=MaaKEDR&source=maakedr-release) (same content as GitHub). Each release provides two GUI frontends — download only one:

> [!TIP]
>
> **Trust only the official channels**: MaaKEDR is released through GitHub Releases and [Mirror酱](https://mirrorchyan.com/en/projects?rid=MaaKEDR&source=maakedr-release) (a partner channel with content identical to the official one); some GUIs support in-app updates via Mirror酱. Downloads from other unofficial sources (lookalike sites, file-hosting reshare) carry security risks — verify the app identifier before installing.

<div align="center">

| Frontend | Suffix  | Description                                          |
| :------: | :-----: | :--------------------------------------------------- |
| **MFAA** | `-MFAA` | GUI, requires .NET Desktop Runtime, richer interface |
| **MXU**  | `-MXU`  | GUI (Tauri + React), no additional dependencies      |

</div>

<div align="center">

|      Platform       | Download                                                 |
| :-----------------: | :------------------------------------------------------- |
|   Windows x86_64    | `MaaKEDR-win-x86_64-v*-MFAA.zip` or `-MXU.zip`           |
|    Windows ARM64    | `MaaKEDR-win-aarch64-v*-MFAA.zip` or `-MXU.zip`          |
|     macOS Intel     | `MaaKEDR-macos-x86_64-v*-MFAA.tar.gz` or `-MXU.tar.gz`   |
| macOS Apple Silicon | `MaaKEDR-macos-aarch64-v*-MFAA.tar.gz` or `-MXU.tar.gz`  |
|    Linux x86_64     | `MaaKEDR-linux-x86_64-v*-MFAA.tar.gz` or `-MXU.tar.gz`   |
|     Linux ARM64     | `MaaKEDR-linux-aarch64-v*-MFAA.tar.gz` or `-MXU.tar.gz`  |
|  Android universal  | `MaaKEDR-android-universal-v*.apk` (pick this if unsure) |
|  Android arm64-v8a  | `MaaKEDR-android-arm64-v8a-v*.apk` (most phones)         |
|   Android x86_64    | `MaaKEDR-android-x86_64-v*.apk` (emulators on PC)        |

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

|                  |     Windows      |      macOS       | Linux | Android |
| :--------------: | :--------------: | :--------------: | :---: | :-----: |
|     Emulator     | Yes (major ones) | Yes (major ones) |  DIY  |   N/A   |
|   ADB required   |       Yes        |       Yes        |  Yes  |   No    |
| Shizuku required |        No        |        No        |  No   |   Yes   |

</div>

MaaKEDR connects to emulators/devices via ADB. Recommended emulators:

- MuMu 12
- BlueStacks 5
- LDPlayer 9
- NoxPlayer

Refer to the MAA documentation for emulator and device support details:

- [Windows emulators](https://maa.plus/docs/en-us/manual/device/windows.html)
- [macOS emulators](https://maa.plus/docs/en-us/manual/device/macos.html)
- [Linux emulators and containers](https://maa.plus/docs/en-us/manual/device/linux.html)

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

1. Open Terminal and extract (extracting into your home directory needs no `sudo`):

    ```shell
    mkdir -p ~/MaaKEDR
    tar -xzf ~/Downloads/MaaKEDR-macos-*.tar.gz -C ~/MaaKEDR
    ```

2. Enter the directory and launch:

    ```shell
    cd ~/MaaKEDR
    ./maakedr
    ```

> [!TIP]
>
> To install into a system directory (e.g. `/usr/local/bin/MaaKEDR`), prefix the `mkdir` and `tar` commands with `sudo`; replace the paths in the commands below accordingly and prefix them with `sudo` too.

**Gatekeeper warning:**

On macOS 10.15+ you may see "cannot be opened because the developer cannot be verified". Use any one of the following:

```shell
# Option 1: remove the quarantine attribute (recommended)
xattr -rd com.apple.quarantine ~/MaaKEDR/maakedr

# Option 2: add to the Gatekeeper allowlist
spctl --add ~/MaaKEDR/maakedr

# Option 3: handle the whole directory at once
xattr -rd com.apple.quarantine ~/MaaKEDR/*
```

  </blockquote>
</details>

#### Linux

Same as macOS — extract the appropriate archive and run `./maakedr`.

#### Android

The Android build is a **separate thing**: no PC, no emulator, no extraction — just install the APK.

Download the APK matching your architecture from [Releases](https://github.com/APPLe-DF/MaaKEDR/releases): `arm64-v8a` for phones, `x86_64` for x86 emulators, `universal` if unsure.

1. On first launch, grant **notification permission** and add the app to the **battery allowlist**. Background idling, scheduled starts and progress notifications all depend on them.
2. Authorize with **Shizuku or root** and wait for the service to connect. Shizuku must be installed and started separately:
    - Android 11+: start it on-device via **wireless debugging**, no PC needed
    - Older versions without root: start it from a PC over ADB
    - See the [Shizuku documentation](https://shizuku.rikka.app/)
3. The task resources are unpacked automatically on first launch.
4. Pick a server, tick the tasks you want and start — **no ADB connection to configure**.

> [!NOTE]
>
> Configuration is essentially the same as on desktop, but **resources are bundled into the APK**. There is no hot update and no MirrorChyan delta update — switching versions means downloading and installing the APK again. If the device still shows old content, clear MaaKEDR's app data and reopen it.

> [!WARNING]
>
> Without Shizuku or root the APK installs but **cannot run tasks** (it has no permission to capture the screen or tap). In that case use the desktop build instead.

---

### 7. Configure MaaKEDR

#### First Launch

On first launch, MaaKEDR automatically initializes and creates the `config/` directory. The main window has panels for **Resource Type**, **Task List**, **Task Settings**, **Task Description**, **Connection** and **Log** (MXU lays them out and names them slightly differently). Wait for "AgentServer started" in the log panel, and do not click "Stop" until "All tasks completed" appears.

#### Settings

Two sections of the GUI **Settings** matter most day to day:

- **Update settings**: choose the source used when checking for updates. MirrorChyan users fill in a CDK (CDK and download entry: [MirrorChyan direct link](https://mirrorchyan.com/en/projects?rid=MaaKEDR&source=maakedr-release)); GitHub users can fill in a Token to raise the API rate limit. See [MirrorChyan](./mirror-chyan).
- **Startup settings**: the emulator executable path and its launch arguments. `Additional commands` is normally only used for the emulator multi-instance ID together with "Auto-Launch Game"; a wrong value here means MaaKEDR cannot start the emulator correctly. See "MFAA Tips" in the [FAQ](./faq).

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

| Task                    | Description                                                                         |
| ----------------------- | ----------------------------------------------------------------------------------- |
| Launch Game             | From launcher to main menu                                                          |
| Claim Rewards           | Daily check-in, weekly, battle pass, mail, dispatch                                 |
| Claim Remaining Rewards | Supplementary claim at the tail of the chain (PVP rewards usually land in the mail) |
| Farm Resources          | Auto-battle with stamina management                                                 |
| Remaining Stamina       | Fixed stamina-drain mode to use up leftover stamina                                 |
| Event Stage             | Event stage sweeps (3/day, no stamina cost)                                         |
| Event Shop              | Auto-buy fixed-guarantee items in the event shop                                    |
| PVP                     | Arena auto-battle                                                                   |
| Stamina Info            | Read home-screen stamina and report refill time                                     |
| Send Gift               | Gift friends in the friend list until the daily quota is used up                    |

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
