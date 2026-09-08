# BioPAT® Spectro UV — Windows Tray Application Companion

> **Platform**: Windows only (.NET Framework 4.7.2)
> **Role**: Optional for short test runs; **mandatory for any session longer than ~6 hours** (see below). Not required just to bring the OPC UA server itself online.

---

## Overview

The `tray_app/` directory contains a Windows-native companion application, **MPT Guardian**, that automates the lifecycle of the **tec5 tecSaaS MPT** measurement session.

> **MPT Guardian, the tec5 tecSaaS MPT software, and the Docker Compose stack (`redisserver`, `udpparser`, `opcserver`, `udphelper`) all run on the same Windows PC** — the one physically connected to the spectrometer. Docker Desktop (WSL2 backend) hosts the Compose stack locally; MPT Guardian talks to Redis over `localhost`, and drives tecSaaS MPT via Windows UI Automation on that same desktop session. Nothing here is split across two machines. The only thing that reaches out over the network from this PC is the OPC UA server (port 4841), which remote SCADA/DCS clients connect to.

When the `udphelper` watchdog container detects stale spectral data in Redis, it writes a signal key (`mpt_refresh = "true"`) to Redis. The tray application continuously polls these keys and reacts by instructing the tecSaaS MPT UI to restart its measurement session — without any manual operator intervention.

This allows the spectrometer PC to autonomously recover from dropped measurement sessions.

> [!IMPORTANT]
> **MPT Guardian is mandatory for any measurement run longer than about 6 hours.** The tec5 tecSaaS MPT software intermittently stops transmitting UDP data on its own during long-running sessions, and without something running to detect and restart it, the Docker stack has no way to bring the spectrometer feed back — `absorbance_channel_1` simply stays stale and every downstream consumer (OPC UA, SCADA) sees dead data until a human intervenes. For short test/demo sessions this isn't an issue, but any production or extended run should have MPT Guardian running.

---

## Architecture

```
Spectrometer PC (Windows, single machine)
───────────────────────────────────────────────────────
 Docker Desktop (WSL2)
 ┌───────────┐   ┌───────────┐            MPT Guardian.exe
 │ udphelper ├──►│redisserver│◄───polls───┤ (native tray app)
 │ (detects  │   │(localhost:│   signals  │
 │  stale    │   │  6379)    ├───────────►│ issues UI automation
 │  data)    │   └───────────┘   mpt_*    │ commands to tecSaaS MPT
 └───────────┘                            └──────────┬─────────┘
                                                      ▼
                                            tecSaaS MPT (same PC)
```

Redis is the shared signal bus between `udphelper` and MPT Guardian — both connect to it over `localhost`, since they're on the same machine. No network hop, no firewall rule, no separate Redis host to configure.

---

## Components

| Project | Description |
|---|---|
| MPTGuardian/ | System tray GUI app (produces `MPT Guardian.exe`). Shows live measurement status (Running / Stopped / Error) in the Windows taskbar notification area. Runs `MPTLogic` and `SaveSpectrumUIHelper` in a background task loop. |
| MPTSaveSpectrumLibrary-code/ | Shared C# library (`SaveSpectrumUIHelper`) that performs UI automation against the tecSaaS MPT desktop application using Windows UI Automation APIs. |
| MPTGuardianInstaller/ | Visual Studio Installer (.vdproj) packaging MPT Guardian for one-click deployment (produces `setup.exe` / `install_MPTGuardian_v1.0.0.msi`). |

---

## Redis Signal Keys

The tray application reads and writes the following Redis keys:

| Key | Values | Description |
|---|---|---|
| mpt_refresh | "true" / "false" | Trigger a measurement session refresh (stop + restart monitoring) |
| mpt_restart | "true" / "false" | Trigger a full MPT program restart |
| mpt_start | "true" / "false" | Start monitoring measurement |
| mpt_stop | "true" / "false" | Stop monitoring measurement |
| mpt_start_state | "true" / "false" | State flag: measurement is currently running |
| mpt_stop_state | "true" / "false" | State flag: measurement is currently stopped |

---

## Build Requirements

- **Visual Studio 2019 or 2022** (Community edition is sufficient)
- **.NET Framework 4.7.2** (installed with Visual Studio)
- **StackExchange.Redis** NuGet package (auto-restored on build)
- The **tecSaaS MPT** application must be installed and licensed on the same Windows PC

---

## Installing MPT Guardian

Pre-built binaries are published as assets on the [GitHub Releases page](https://github.com/Sir-Narwhal/biopat-spectrouv-server/releases) (matching the corresponding server version) rather than committed to the repository. There are two ways to get MPT Guardian running on the Windows spectrometer PC — pick whichever fits your deployment:

1. **Run the installer** — download `setup.exe` and `install_MPTGuardian_v1.0.0.msi` from the release assets into the same folder and run `setup.exe`. It performs a normal Windows install: registers the app, adds an uninstall entry, and is the recommended option for a permanent, production spectrometer PC.
2. **Run the standalone `.exe` directly** — download `MPT_Guardian.exe` from the release assets (renamed with an underscore in place of the space in `MPT Guardian.exe`, since GitHub release assets can't contain spaces) and copy it to the spectrometer PC to run as-is, with no installation step. This is the quickest option for a test PC or a one-off long run, since it needs no admin rights and leaves nothing behind when you delete the folder.

Either way, MPT Guardian must be running (and left running) for the full duration of any measurement session over ~6 hours — see the note above.

---

## Build & Run (from source)

1. Open `MPTSaveSpectrumLibrary-code/MPTSaveSpectrumLibrary.sln` in Visual Studio (it includes the `MPTSaveSpectrumLibrary`, `MPTGuardian`, and `MPTGuardianInstaller` projects).
2. Restore NuGet packages (right-click solution → **Restore NuGet Packages**).
3. Build in **Release** configuration.
4. Run `MPT Guardian.exe` (or the installer output) on the Windows spectrometer PC. The tray icon will appear in the taskbar.

### Redis Connection

The application connects to `localhost:6379` by default, which is correct for the standard deployment — `redisserver` runs in Docker Desktop on this same PC, published to the host on port 6379. You'd only need to change this (in `RedisManager.cs`, before building) in a non-standard setup where Redis runs elsewhere.

---

## Status Indicators

The tray icon tooltip shows the current measurement state:

| Tooltip | Meaning |
|---|---|
| Status: Running | tecSaaS MPT measurement session is active |
| Status: Stopped | Measurement session is stopped |
| Status: Error | Redis connection lost or state keys missing |

---

## Limitations & Notes

- This component uses **Windows UI Automation** to control the tecSaaS MPT desktop application. It requires MPT to be running and visible on the Windows desktop session — it will not work in a headless/RDP-minimized session without additional configuration.
- This component is **independent** of the Docker stack. The Docker OPC UA server will start and run correctly without it — but on a session longer than ~6 hours, the spectrometer feed itself will silently die without it (see the mandatory-use note above).
- Full C# source is provided for transparency and auditing. Pre-built `.exe` and installer binaries are published on the [Releases page](https://github.com/Sir-Narwhal/biopat-spectrouv-server/releases) (see [Installing MPT Guardian](#installing-mpt-guardian)) so the tray app can be deployed without a Visual Studio toolchain on the spectrometer PC.
