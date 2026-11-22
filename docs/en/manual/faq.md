---
order: 2
icon: ph:question-fill
---

# FAQ

## Installation & Download

### What do the filenames mean?

Desktop builds are named as:

```text
MaaKEDR-<os>-<arch>-<version>-<frontend>.<ext>
```

For example, `MaaKEDR-win-x86_64-v1.0.2-MFAA.zip`:

- **OS**: `win` (Windows)
- **Arch**: `x86_64` (64-bit Intel/AMD)
- **Version**: `v1.0.2`
- **Frontend**: `MFAA` (GUI, requires .NET)
- **Extension**: `zip`

Android builds use a separate naming scheme and have **no frontend** (there is only one UI):

```text
MaaKEDR-android-<ABI>-<version>.apk
```

| ABI in filename | Target devices                                          | Size       |
| :-------------- | :------------------------------------------------------ | :--------- |
| `universal`     | Any Android device (contains both ABIs — the safe pick) | Largest    |
| `arm64-v8a`     | Most phones and tablets (64-bit ARM)                    | About half |
| `x86_64`        | Android emulators on a PC, rare x86 tablets             | About half |

> Not sure which to pick? Take `universal`. Want to save space on an ordinary phone? Take `arm64-v8a`.

### Slow download speed?

GitHub download speeds vary. Try:

- The [MirrorChyan direct link](https://mirrorchyan.com/en/projects?rid=MaaKEDR&source=maakedr-release) channel (same content as the official release, CDK required; see [MirrorChyan](./mirror-chyan))
- A proxy such as [ghproxy](https://ghproxy.com/)
- The MaaKEDR community group for backup links (see the `CONTACT` file)

---

## Crashes

### Missing DLL error (e.g. `VCRUNTIME140.dll`)

VCRedist is not installed. Download and install [vc_redist.x64.exe](https://aka.ms/vs/17/release/vc_redist.x64.exe).

### MFAA does not start or shows .NET errors

.NET Desktop Runtime is not installed. A message like this is the giveaway:

```plaintext
You must install .NET Desktop Runtime to run this application.
```

Download from the [.NET download page](https://dotnet.microsoft.com/download/dotnet) and install the matching version.

### Still crashing after installing the runtimes

If the runtimes are installed but the app still **crashes** and produces **no log file at all** (`debug/maafw.log`), the cause is usually something else — a missing dependency or a corrupted download:

- Make sure the archive came from an official channel and was fully extracted
- Extract it again, or delete the whole folder and download it fresh (back up `config/` first if you want to keep your settings)
- If it still will not start, report it on [GitHub Issues](https://github.com/APPLe-DF/MaaKEDR/issues)

### App crashes without an error message

Check `debug/maafw.log` for details. Common causes:

- Path contains non-ASCII characters or spaces → move to a plain English path
- Incomplete extraction → re-extract
- Antivirus deleted files → add an exclusion

### MXU is slow or shows a black screen

Update your GPU drivers. Try switching the rendering mode in MXU settings.

### "Failed to load resources"

This appears when resource files are missing or corrupted. Delete the whole MaaKEDR folder and download it again (**back up `config/` first if you want to keep your settings**).

---

## Connection

### Emulator not auto-detected

- Make sure ADB debugging is enabled in your emulator
- Ensure only one emulator instance is running
- Try clicking "Refresh"
- Try running MaaKEDR as administrator
- Confirm the resolution is set to 1280x720 (landscape)

### How to configure manually?

Click "Customize" in the connection panel to enter the ADB address by hand. Default ADB ports:

| Emulator     | Default ADB Address |
| :----------- | :------------------ |
| MuMu 12      | `127.0.0.1:16384`   |
| BlueStacks 5 | `127.0.0.1:5555`    |
| LDPlayer 9   | `127.0.0.1:5555`    |
| NoxPlayer    | `127.0.0.1:62001`   |

ADB path, multi-instance ports and touch modes are covered in [Connection Settings](./connection).

### Connection troubleshooting order

When you see "an error occurred while connecting to the emulator", there are many possible causes. Work through the steps below **one at a time**, in order:

1. **Verify the ADB path and address**: see [Connection Settings](./connection), and make sure you are not connecting to some other emulator or device
2. **Kill existing ADB processes**: close MaaKEDR, open `Task Manager` → `Details`, look for processes whose name contains `adb`, end them and retry
3. **Watch out for conflicting ADB versions**: when ADB versions differ, the newly started process shuts the old one down. If MAA, Android Studio or a phone assistant runs at the same time, keep their ADB versions identical
4. **Switch the input method or the ADB**: some emulators (BlueStacks China, NoxPlayer, …) ship an old ADB — try another ADB, or change the input method under **Customize**
5. **Avoid game accelerators**: some accelerators require restarting MaaKEDR, ADB and the emulator after starting or stopping acceleration
6. **Reboot your PC**: this resolves the vast majority of mysterious connection failures
7. **Switch emulators**: MuMu 12 or LDPlayer 9 are usually recommended; see the [MAA documentation](https://maa.plus/docs/zh-cn/manual/device/windows.html) for emulator support details

### Connected but tasks don't run

- Verify the game is installed and updated
- Confirm the correct resource type (Official/Bilibili/TapTap) is selected
- Check screenshots in `debug/` for recognition accuracy

---

## Task Execution

### Agent startup timeout or long unresponsive startup

First launch requires downloading Python dependencies, which may take a while. Do not click "Stop". If it times out repeatedly:

- Check your network connection
- Verify the mirror in `config/pip_config.json` is accessible

If there is **no reaction at all** for a long time, or the log shows an error like `...No such file or directory`, the package is usually incomplete — download the full archive again.

### Tasks not running as expected

- Confirm the task is enabled (checkbox checked)
- Read each task's description and configure options accordingly
- Ensure the game is on the correct screen (main menu or target feature)
- Review `debug/maafw.log` for details

### Yellow warnings in the log

Yellow (warning-level) lines may show up when a task starts. They mostly come from **optional** network requests that failed (update checks, announcement fetching, …) and **usually do not affect task execution** — you can ignore them.

Treat other yellow lines the same way; if they show up constantly and actually break a feature, report them with a log as described in "How do I report a problem?".

### Farm resources stage list is incomplete

Only preset stages are included. To add more stages, refer to the Pipeline guide in the developer documentation.

---

## Miscellaneous

### Where are the logs?

Logs: `debug/maafw.log`. Screenshots: the `debug/` directory; custom-module logs live in `debug/custom/`. Include these files when reporting issues.

### How to update MaaKEDR?

**MXU:** An Update section appears in Settings when `mirrorchyan_rid` is set in `interface.json`.  
Check for updates will try [MirrorChyan](https://mirrorchyan.com/en/projects?rid=MaaKEDR&source=maakedr-release) first; without a CDK or if the resource is not registered on Mirror, it usually falls back to **GitHub Releases** (network access required; optional GitHub Token helps with rate limits).

**MFAAvalonia:** Configure the update source in settings, then check for updates.

For manual updates: download the latest release, extract to a new directory, then copy your old `config/` folder to the new directory to keep your settings.

### How do I report a problem?

Once you have read this page and tried the fixes without success:

1. Open an issue on [GitHub Issues](https://github.com/APPLe-DF/MaaKEDR/issues) and **follow the template** — attach `debug/maafw.log`, the screenshots under `debug/`, and the steps to reproduce
2. Ask in the community group (the group number is in the `CONTACT` file)

---

## MFAA Tips

### Remembered Connection & Fingerprint Matching

If a remembered connection gets overwritten when you launch MFAA with an unremembered emulator running, go to **Settings → Connection Settings** and disable "Use fingerprint to match device" to prevent auto-switching.

### Multi-Instance Setup & Batch Launch

Only one MFAA instance can run per directory. To run multiple emulators simultaneously, create additional configurations from the main config panel. Each config can connect to a different emulator with its own task set. The second icon in the left sidebar shows real-time status for all configs.

::: tip
To auto-launch multiple configs on startup, enable "Batch launch on startup" in startup settings and select the configs to run.
:::

### Auto-Launch Game

MFAA can launch the game automatically when a task starts, with two methods:

1. **Custom Program**: Click "Add Task" in the task list, scroll to find "Custom Program", add it to the top of the list, and enter the game path in its settings.
2. **Connection Settings**: Enable "Launch game on connection failure", then set the game path in startup settings.

When using multiple emulator instances, ensure the multi-instance ID is correctly set in the additional commands field.

::: tip
Quick setup is available next to the additional commands field in startup settings.
:::
