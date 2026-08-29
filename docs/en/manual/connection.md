---
order: 3
icon: mdi:plug
---

# Connection Settings

MaaKEDR connects to emulators and Android devices via ADB. Proper connection configuration is essential for task execution.

---

## Auto Detection

In most cases, keep only your target emulator running and MaaKEDR will detect it automatically. Click **Refresh** to rescan.

Once detected, the **connection status** indicator turns green.

---

## Manual Configuration

If auto-detection fails, click **Customize** to configure manually:

1. **ADB Path**: Usually auto-filled, no changes needed
2. **ADB Address**: `<IP>:<Port>` format, e.g. `127.0.0.1:16384`

Default ADB ports for popular emulators:

| Emulator     | ADB Address                                                                                     | Notes                  |
| :----------- | :---------------------------------------------------------------------------------------------- | :--------------------- |
| MuMu 12      | `127.0.0.1:16384` (multi-instance: `16416`/`16448`/`16480`/`16512`/`16544`/`16576`)             | Enable ADB in settings |
| BlueStacks 5 | `127.0.0.1:5555` (multi-instance: `5565`/`5575`/`5585`/`5595`)                                  | Enable ADB in settings |
| LDPlayer 9   | `127.0.0.1:5555` (multi-instance: `5557`/`5559`/`5561`) or `emulator-5554`/`5556`/`5558`/`5560` | Enabled by default     |
| NoxPlayer    | `127.0.0.1:62001` (multi-instance: `59865`)                                                     | Enabled by default     |
| MEmu         | `127.0.0.1:21503`                                                                               | Enable ADB in settings |

> [!TIP]
>
> Multi-instance ports listed above are common values; verify the actual port in your emulator's multi-instance manager. Check your emulator's settings for the ADB debugging toggle. MuMu 12: Settings → Other → ADB. BlueStacks: Settings → Advanced → Android Debug Bridge.

---

## Verify Connection

Run this command in a terminal to verify ADB connectivity:

```shell
adb devices
```

The output should list your device with a `device` status.

---

## Multiple Emulator Instances

When multiple emulator instances are running, MaaKEDR lists all detected devices. Select the correct target. It is recommended to keep only one emulator instance running while using MaaKEDR.

---

## Troubleshooting

See the [FAQ](./faq) for connection-related issues.
