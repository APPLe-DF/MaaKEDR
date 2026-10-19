---
title: "Android Packaging (MaaFwApp)"
order: 10
icon: "ri:android-fill"
---

# Android Packaging (MaaFwApp)

MaaKEDR's Android build is produced through [MaaFwApp](https://github.com/Aliothmoon/MaaFwApp),
a general-purpose Android GUI for MaaFramework. Resources are baked into the APK **at build
time**; at runtime the app spawns a privileged process via [Shizuku](https://shizuku.rikka.app/)
or root, and screencap / input go through the on-device native controller instead of adb.

Integration model (same as MAA1999/M9A and Saratoga-Official/MRA): MaaFwApp lives as a git
submodule at `Android/MaaFwApp`, and MaaKEDR ships a single packaging recipe
`Android/profile.yaml` (where the resources are, the package name and icon, how the agent is
launched). Changing resources = edit resources + rebuild; the shell itself is untouched.

> Resources are bound to the APK. No hot updates on Android; Mirror酱 CDN is not supported yet.

## Layout

```text
MaaKEDR/
├── Android/
│   ├── profile.yaml            # packaging recipe (in git, shared by local builds and CI)
│   └── MaaFwApp/               # shell submodule
├── agent-dist/                 # build_agent_bundle.py output (gitignored)
├── logo.png                    # make_android_icon.py output (gitignored)
└── …                           # the PI itself: interface.json, tasks/, resource/, agent/
```

MaaKEDR's PI is flat (`interface.json`, `tasks/`, `resource/`, `agent/` all at the repo root),
so the recipe's `assets: ..` points at the repo root directly and **no** staging script is
needed. Note that `agent/**` and `logo.png` are not in MaaFwApp's default include whitelist;
they are listed explicitly in the recipe.

## Requirements

- JDK 17 (compile baseline of AGP 9 / Gradle 9.4)
- Android SDK: platform-tools, platforms;android-37.0, build-tools;37.0.0
- Python 3 (downloads the MaaFramework artifacts and assembles the agent runtime; Pillow is
  additionally needed to generate the icon)

## Version alignment

On Android, the `maa` Python bindings and the MaaFramework behind them both come from the agent
core [MaaAgentCoreAndroid](https://github.com/Aliothmoon/MaaAgentCoreAndroid). The client-side
MaaFramework `.so` inside the APK must match the core version, otherwise the two ends disagree.
The pins are written at the top of `Android/profile.yaml`:

| Component          | Version                                                                              |
| :----------------- | :----------------------------------------------------------------------------------- |
| Agent core         | `3.13.15-maafw5.14.2` (`build_agent_bundle.py --core-tag`)                           |
| MaaFramework `.so` | `v5.14.2` (`setup_maa_framework.py --tag`)                                           |
| Desktop pin        | `maafw==5.14.2` (requirements.txt; the core ships the same maa source, auto-skipped) |

Change all three together when upgrading. The desktop `maafw` entry in `requirements.txt` is
dropped by `build_agent_bundle.py` (no Android wheel on public indexes), which does not affect
Android.

## Local build

Ship with the **release** variant for everyday distribution: R8 code shrinking
(dex 75.5M -> 6.7M) and no debug-only Perfetto tracing, which is less than half the
size of debug (measured 151.5M -> ~70M). Use debug only for development.

```bash
# 1. Submodule (for already-cloned repos)
git submodule update --init --recursive

# 2. Icon (logo.ico -> logo.png, rerun whenever the logo changes)
python tools/make_android_icon.py

# 3. Lay down the MaaFramework Android .so and the agent runtime
cd Android/MaaFwApp
python scripts/setup_maa_framework.py --abi arm64-v8a --tag v5.14.2
python scripts/build_agent_bundle.py --out ../agent-dist \
    --core-tag 3.13.15-maafw5.14.2 --abi arm64-v8a \
    --requirements ../../requirements.txt

# 4. Trim the agent runtime: drop only the unused sqlite3 libs (neither maa nor
#    the agent imports sqlite3). Do NOT drop numpy's BLAS (libopenblas):
#    numpy's _core/_multiarray_umath and linalg hard-link it via ELF DT_NEEDED,
#    so removing it breaks `import numpy` (hit on a real device); see
#    tools/trim_agent_bundle.py header.
python ../../tools/trim_agent_bundle.py

# 5. SDK, recipe, ABI and signing (Android/MaaFwApp/local.properties, not in git)
cat > local.properties <<EOF
sdk.dir=<your Android SDK path>
pi.profile=<absolute path to MaaKEDR>/Android/profile.yaml
build.debugAbi=arm64-v8a
build.releaseAbi=arm64-v8a   # must be explicit: leave it out and the release
#                            defaults to dual ABI (incl. x86_64) while agent-dist and
#                            jniLibs only ship arm64-v8a, producing an APK missing
#                            the MaaFramework .so for x86_64
KEYSTORE_PATH=<keystore path>
KEYSTORE_PASSWORD=<store password>
KEY_ALIAS=<alias>
KEY_PASSWORD=<key password>
EOF

# 6. Build the release APK (unsigned when no keystore is configured)
./gradlew :app:assembleRelease

# 7. Recompress dex: AGP 9 stores dex uncompressed by default; this step deflates
#    it, re-aligns and re-signs, saving about 3.4M more (same keystore as step 5)
python ../../tools/shrink_apk.py app/build/outputs/apk/release/app-release.apk

# 8. Collect into dist/package-maafwapp/ with a build-date suffix so successive
#    builds stay distinguishable
python ../../tools/collect_android_apk.py release
```

The APK lands in `Android/MaaFwApp/app/build/outputs/apk/release/`. Without a keystore
the release stays unsigned. For local testing you can use the debug keystore
(`~/.android/debug.keystore`, store/key password `android`, alias `androiddebugkey`) —
same signature as the debug build, so the two can overwrite each other. Use a proper
keystore for real distribution.

Rerun steps 2-4 after changing `agent/`, `requirements.txt`, or the icon; after changing
`tasks/` or `resource/`, just rebuild. If the device keeps showing old content after a
reinstall, clear the app data.

> **Incremental build size trap**: the shell updates `assets/pi.zip` inside the APK in place.
> The replaced old pi.zip can survive as orphaned data (listed by neither the central directory
> nor the installer; installs fine but doubles the file size over successive builds). When the
> APK grows unexpectedly, delete the previous artifact and rebuild for a compact package:
>
> ```bash
> rm Android/MaaFwApp/app/build/outputs/apk/release/app-release.apk
> ./gradlew :app:assembleRelease
> ```

### Release builds and signing

Signing is configured in step 5 above (`local.properties` or environment variables). For a
dual-ABI release (arm64-v8a + x86_64), add `--abi x86_64` to both `setup_maa_framework.py`
and `build_agent_bundle.py`, and set `build.releaseAbi=arm64-v8a,x86_64` in
`local.properties`.

## CI builds (GitHub Actions)

The eight local steps are wrapped in a reusable pipeline, `.github/workflows/android-build.yml`,
driven by two callers:

| Caller        | Trigger                                            | Artifacts                                             |
| :------------ | :------------------------------------------------- | :---------------------------------------------------- |
| `android.yml` | push/PR touching Android paths, or manual dispatch | debug APK (release optional)                          |
| `release.yml` | `v*` tag                                           | three release APKs, shipped with the desktop packages |

### Three parallel pipelines

```text
library-resources  -- JDK + SDK only; runs verifyReleaseResources (20 min)
build              -- universal APK: one ABI for debug, arm64-v8a + x86_64 for release
abi-split          -- release only: matrix [arm64-v8a, x86_64], one APK per ABI (~half size)
```

A release produces `MaaKEDR-android-universal-<tag>.apk` plus two `MaaKEDR-android-<abi>-<tag>.apk`.
**Do not rename them casually**: in-app updates pick the asset by name
(`GitHubUpdate.selectAsset`), and an ABI marker on the universal package bypasses the fallback path.

### Version resolver (do not pin versions by hand)

`tools/android-packaging.mjs` reads `maafw==X` from `requirements.txt`, then finds the matching
kernel release (`*-maafwX`) in
[MaaAgentCoreAndroid](https://github.com/AliothMoon/MaaAgentCoreAndroid) and exports `core_tag`,
`maafw_tag`, `chaquopy_pins` and friends:

```bash
node tools/android-packaging.mjs
# agent core tag   : 3.13.15-maafw5.14.2
# client MaaFW tag : v5.14.2
# has agent        : true
```

When the kernel has not published the matching pair yet, the resolver **degrades to the highest
pair not above the pinned version** and emits a warning. Client and binding stay on the same
version inside the APK; only the distance to `requirements.txt` grows. The degradation disappears
once upstream ships, **without touching the workflow**.

### Required secrets

| Secret              | Purpose                        | When missing                                               |
| :------------------ | :----------------------------- | :--------------------------------------------------------- |
| `KEYSTORE_BASE64`   | base64 of the signing keystore | PR/dispatch yields an unsigned APK; **tags fail outright** |
| `KEYSTORE_PASSWORD` | store password                 | same                                                       |
| `KEY_ALIAS`         | key alias                      | same                                                       |
| `KEY_PASSWORD`      | key password                   | same                                                       |
| `GITHUB_TOKEN`      | resolve versions, download     | built in, nothing to configure                             |

Generate the base64 on Windows:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\path\to\release.jks"))
```

> A tag release without signing material fails on purpose: an unsigned APK can neither be installed
> over an existing one nor enter in-app updates.

### What CI does beyond the local steps

Three things the manual flow tends to miss:

1. **Generates the icon**: `logo.png` is gitignored (it is derived from `logo.ico`), so CI runs
   `make_android_icon.py` and installs Pillow. Skip it locally and the shell fails on the missing icon.
2. **Syncs OCR models**: `resource/base/model/ocr/` comes from the MaaCommonAssets submodule and is
   not committed; CI runs `pnpm dlx create-maa-project@latest --update ocr-models`.
3. **Checks native libraries**: after packaging, `unzip -Z1` + `grep -Fx` verify
   `libMaaFramework.so`, `libMaaUtils.so` and `libMaaAndroidNativeControlUnit.so` per ABI (plus
   `libMaaAgentServer.so` for agent projects). A missing `.so` does not fail the build — it fails on
   the device.

### Reproducing a CI build locally

```bash
node tools/android-packaging.mjs          # see the resolved versions first
# then follow "Local build" above, keeping the three differences in mind
```

### MirrorChyan distribution (Android RID must be requested)

Android APKs **cannot reuse the desktop `mirrorchyan_rid`**. They are different product entries:

|          | Desktop (MFAA / MXU)                       | Android APK                      |
| :------- | :----------------------------------------- | :------------------------------- |
| Contents | resources only; the user already has a GUI | GUI + Python runtime + resources |
| RID      | `MaaKEDR` / `MaaKEDR-MXU`                  | must be requested                |
| Update   | hot-swap resources                         | full package reinstall           |

> **Status: pending.** The RID is not registered on MirrorChyan yet, and the `mirrorchyan_android`
> job is not triggered by default (`android` input defaults to false). Once granted, two places
> need updating:
>
> 1. `mirrorchyan_rid` in `.github/workflows/mirrorchyan_release.yml` (currently the placeholder
>    `MaaKEDR-Android-PENDING`)
> 2. `update.mirrorchyanRid` in `Android/profile.yaml` — it **overrides** the PI's
>    `mirrorchyan_rid`, leaving desktop builds untouched:
>
>     ```yaml
>     update:
>         mirrorchyanRid: <granted rid>
>     ```
>
> Do **not** hardcode a RID before activation: the app queries `/api/resources/<rid>/latest`, so an
> unknown RID fails every update check (not fatal, but noisy). MirrorChyan downloads also require a
> CDK; without one `resolve` returns `CDK_REQUIRED`, while a plain "is there a newer version" check
> still works.

Uploads run in the `mirrorchyan_android` job of `mirrorchyan_release.yml`; `release.yml` dispatches
it after creating the Release (`client_payload.android=true`), so desktop and Android upload in one
go. A manual run only needs the `android` input checked.

## Agent entrypoint

MaaFwApp launches the agent via the recipe's `runtimes` and ignores the PI's `child_exec` /
`child_args`. This project always uses `agent/main.py`, never `agent/bootstrap.py`: bootstrap
targets the desktop uv workflow, its Linux venv branch misfires on Android
(`sys.platform == "android"`), and pip install is impossible on device.
`agent/maafw_paths.py` detects the app-injected `MAAFW_BINARY_PATH` (pointing at the APK's
nativeLibraryDir) and reuses it directly, so the desktop `runtimes/` layout logic never kicks
in.

## Runtime modes

MaaKEDR's ROIs, coordinates and template images are authored for 1280x720 (16:9), and the
agent enforces the ratio at task start (`agent/custom/sink/aspect_ratio.py`). The Android
package therefore **ships background mode only**: the virtual display is fixed at
720P@240dpi, which is 16:9 out of the box.

Foreground mode is disabled in the packaging profile (`display.foreground: false` in
`Android/profile.yaml`). The physical screen (e.g. 1260x2800) is not 16:9, so tasks are
stopped deliberately — keeping the switch would only mislead. With it off, the home screen
no longer renders the mode toggle, and any stored foreground setting falls back to
background.

**Trade-off**: with only the virtual display left, `BackgroundModePrecheck` blocks outright
below API 29, so the app requires **Android 10 (API 29) or newer**.

## Troubleshooting

| Symptom                                                   | Cause                                                                                             |
| :-------------------------------------------------------- | :------------------------------------------------------------------------------------------------ |
| Installs fine, but native load fails when starting a task | `setup_maa_framework.py` was not run, or the ABI differs from `build.debugAbi`                    |
| "Agent startup failed" when starting a task               | See `MaaRunner: prepare failed: agent[0]:` in `adb logcat -s MaaFw`                               |
| Agent protocol errors                                     | Client-side `.so` version differs from the agent core's MaaFramework; see Version alignment       |
| Icon missing                                              | `logo.png` not generated by `tools/make_android_icon.py`, or not listed in the recipe's `include` |
| Stale content after reinstalling                          | The unpacked cache may survive when the version is unchanged; clear app data                      |
