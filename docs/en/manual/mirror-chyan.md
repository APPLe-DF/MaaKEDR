---
order: 7
icon: ic:outline-fast-forward
---

# Mirror酱 Usage

Mirror酱 ([website](https://mirrorchyan.com/zh/projects?rid=MaaKEDR&source=maakedr-release)) is MaaKEDR's partner distribution and update platform, making updates to open source apps easier, with content kept in sync with the official channels. It is paid for by users, shares revenue with developers, and is itself open source.

By accessing or using the service you agree to be bound by the [Mirror酱 Terms of Service](https://mirrorchyan.com/disclaimer.html).

> MaaKEDR is released through two official channels with identical content: **GitHub Releases** and **Mirror酱**. Source code, checksums, and release history are published on [MaaKEDR Releases](https://github.com/APPLe-DF/MaaKEDR/releases), and Mirror酱, as a partner channel, stays in sync with it (`mirrorchyan_rid: MaaKEDR`) — both channels deliver identical content.

## Updating from the GUI

Some MaaFramework GUIs (such as [MFAAvalonia](https://github.com/SweetSmellFox/MFAAvalonia) and [MXU](https://github.com/MaaXYZ/MXU)) have built-in support for updating the app and its resources via Mirror酱. Enable it in the corresponding settings screen (the MaaKEDR release package already includes the `mirrorchyan_rid` configuration).

## Using the Website

1. Open the [Mirror酱 website](https://mirrorchyan.com/zh/projects?rid=MaaKEDR&source=maakedr-release)
2. Search for `MaaKEDR`
3. You can install, update, download previous versions, and donate

## FAQ

### Tasks fail after a Mirror update

Mirror酱 only updates the app and resource files; it does not change emulator connection or resolution settings. If tasks fail after an update:

1. Check that the resolution is still 1280×720 (see [Getting Started](./newbie.md))
2. Check the connection (see [Connection Settings](./connection.md))
3. If the issue persists, report it on [GitHub Issues](https://github.com/APPLe-DF/MaaKEDR/issues) with the runtime logs (see [Troubleshooting](../develop/fix.md))
