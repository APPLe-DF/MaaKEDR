---
order: 3
icon: mdi:plug
---

# Connection Settings

MaaKEDR connects to emulators and Android devices via ADB. Proper connection configuration is essential for task execution.

> [!NOTE]
>
> **Readers using the Android APK can skip this page.** The Android build does not go through ADB — Shizuku or root grants screen-capture and tap permissions directly, so there is no connection to configure. This page is for the **desktop build running against an emulator**.

---

## Auto Detection

In most cases, keep only your target emulator running and MaaKEDR will detect it automatically. Click **Refresh** to rescan.

Once detected, the **connection status** indicator turns green.

If auto-detection fails, try the following in order:

1. Make sure **ADB debugging** is enabled in the emulator (see [Emulator Documentation](#emulator-documentation) below for where the toggle lives)
2. Close other emulator instances and keep only the target one
3. Run MaaKEDR **as administrator**, then click **Refresh** again
4. If it still fails, click **Customize** and fill the fields manually — see the next section

---

## Manual Configuration

A complete connection setup consists of **ADB Path** and **ADB Address**. Some GUIs also expose advanced items such as the screencap method and the input method (touch mode) — **leave them at their defaults**.

### ADB Path

ADB Path points to the `adb` executable MaaKEDR uses to talk to the emulator. It is usually shipped with the emulator, but you can also use the official Google ADB.

#### Using the Emulator's Own ADB

1. Start the emulator, open Task Manager, right-click the emulator process → **Open file location**
2. Look for an `.exe` whose name contains `adb`, either in that folder or one level down
3. Select it in **ADB Path**

Common filenames: `adb.exe`, `HD-adb.exe`, `adb_server.exe`, `nox_adb.exe`.

#### Using the Official Google ADB

Download and extract [platform-tools](https://dl.google.com/android/repository/platform-tools-latest-windows.zip), then select the `adb.exe` inside.

> [!TIP]
>
> Extracting platform-tools into the MaaKEDR folder is recommended: **ADB Path** can then be the relative path `.\platform-tools\adb.exe`, and it moves together with the MaaKEDR folder.

### ADB Address

A local emulator address looks like `127.0.0.1:<port>` or `emulator-<4 digits>`.

Default ADB ports for popular emulators:

| Emulator     | ADB Address                                                                                     | Notes                  |
| :----------- | :---------------------------------------------------------------------------------------------- | :--------------------- |
| MuMu 12      | `127.0.0.1:16384` (multi-instance: `16416`/`16448`/`16480`/`16512`/`16544`/`16576`)             | Enable ADB in settings |
| BlueStacks 5 | `127.0.0.1:5555` (multi-instance: `5554`/`5556`/`5565`/`5575`/`5585`/`5595`)                    | Enable ADB in settings |
| LDPlayer 9   | `127.0.0.1:5555` (multi-instance: `5557`/`5559`/`5561`) or `emulator-5554`/`5556`/`5558`/`5560` | Enabled by default     |
| NoxPlayer    | `127.0.0.1:62001` (multi-instance: `59865`)                                                     | Enabled by default     |
| MEmu         | `127.0.0.1:21503`                                                                               | Enable ADB in settings |

> [!TIP]
>
> Multi-instance ports listed above are common values; verify the actual port in your emulator's multi-instance manager. Check your emulator's settings for the ADB debugging toggle. MuMu 12: Settings → Other → ADB. BlueStacks: Settings → Advanced → Android Debug Bridge.
>
> The `/` in the table means **or** — pick the one that matches your setup, do not copy the whole list.

#### Emulator Documentation

- [MuMu 12](https://mumu.163.com/help/20230214/35047_1073151.html) `127.0.0.1:16384`
- [BlueStacks 5](https://support.bluestacks.com/hc/zh-tw/articles/360061342631) `127.0.0.1:5555`
- [LDPlayer 9](https://help.ldmnq.com/docs/LD9adbserver) `emulator-5554`
- [NoxPlayer](https://support.yeshen.com/zh-CN/qt/ml) `127.0.0.1:62001`
- [MEmu](https://bbs.xyaz.cn/forum.php?mod=viewthread&tid=365537) `127.0.0.1:21503`

For other emulators, see this [blog post on ADB ports](https://www.cnblogs.com/zhaoqingqing/p/15238464.html).

#### Getting the Multi-Instance Port

- **MuMu 12**: the port of each running instance is shown in the top-right corner of the multi-instance manager
- **BlueStacks 5**: the current multi-instance port is shown in the emulator settings

If the GUI does not show it, query it with ADB:

1. Start **one** emulator only, and make sure no other Android device is connected to this machine
2. Open a terminal in the folder that contains `adb` and run:

    ```shell
    # Windows Command Prompt
    adb devices
    # Windows PowerShell
    .\adb devices
    ```

3. Sample output:

    ```text
    List of devices attached
    127.0.0.1:16384  device
    emulator-5554    device
    ```

4. Put the `127.0.0.1:<port>` or `emulator-<4 digits>` value into **ADB Address**

> [!TIP]
>
> Alternatively, open Windows **Resource Monitor** → **Network** tab, find the emulator process (e.g. `HD-Player.exe`) under **Listening Ports**, then find `adb.exe` under **TCP Connections** — the remote port that matches the listening port is the debug port.

### Touch Mode

MaaFramework detects the available screencap and input methods automatically, so **you normally do not need to choose one manually**. It only matters when the connection succeeds but taps do not land.

MaaFramework's input methods fall into three families:

1. **Minitouch**: a C touch-event injector that drives `evdev` devices directly, and is fast. Since Android 10 it is no longer usable while SELinux is in `Enforcing` mode.
2. **MaaTouch**: MAA's Java reimplementation of Minitouch, built on Android's native `InputDevice` with extra features. Availability on newer Android versions should be verified on your own device.
3. **Adb Input**: calls ADB's `input` command directly — the most compatible and the slowest.

If taps do not register with the current method (common on emulators shipping an old ADB), switch the input method under **Customize**, or try a different ADB.

### Running Multiple Emulators at Once

One MaaKEDR instance drives one emulator at a time. To run several at once, see "Multi-Instance Setup & Batch Launch" in the [FAQ](./faq).

---

## Verify Connection

Run this command in a terminal to verify ADB connectivity:

```shell
adb devices
```

The output should list your device with a `device` status:

```text
List of devices attached
127.0.0.1:16384  device
```

If the status is `offline`, `unauthorized`, or the list is empty, re-check the ADB path and address above.

---

## Multiple Emulator Instances

When multiple emulator instances are running, MaaKEDR lists all detected devices. Select the correct target. It is recommended to keep only one emulator instance running while using MaaKEDR.

---

## Troubleshooting

See the [FAQ](./faq) for connection-related issues.
