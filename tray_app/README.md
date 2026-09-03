# BioPAT® Spectro UV — Windows Tray Application Companion

> **Platform**: Windows only (.NET Framework 4.x)
> **Role**: Optional companion to the main Docker stack. Not required to use the OPC UA server.

---

## Overview

The 	ray_app/ directory contains a Windows-native companion application that automates the lifecycle of the **tec5 tecSaaS MPT** measurement session running on the Windows spectrometer PC.

When the main Docker stack detects stale spectral data in Redis (via the watchdog service), it writes a signal key (mpt_refresh = "true") to Redis. The tray application continuously polls these keys and reacts by instructing the tecSaaS MPT UI to restart its measurement session — without any manual operator intervention.

This allows the Linux Docker server to autonomously recover from dropped measurement sessions.

---

## Architecture

`
Linux Docker Stack                         Windows Spectrometer PC
─────────────────                          ───────────────────────
spectrouv_helper.py  ──[Redis key]──►  MPTTrayApplication.exe
  (detects stale data,                   (polls Redis, issues
   sets mpt_refresh=true)                 UI automation commands
                                          to tecSaaS MPT)
`

Redis is the shared signal bus between the two systems. The Windows PC must have network access to the Redis instance (port 6379).

---

## Components

| Project | Description |
|---|---|
| MPTTrayApplication/ | System tray GUI app. Shows live measurement status (Running / Stopped / Error) in the Windows taskbar notification area. Runs MPTLogic and SaveSpectrumUIHelper in a background task loop. |
| MPTControlService/ | Windows NT Service variant of the same logic (for service-mode operation without a logged-in user). |
| MPTSaveSpectrumLibrary-code/ | Shared C# library (SaveSpectrumUIHelper) that performs UI automation against the tecSaaS MPT desktop application using Windows UI Automation APIs. |
| MPTHelperApplication-Installer/ | Visual Studio Installer (.vdproj) packaging the tray application for one-click deployment. |

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
- **.NET Framework 4.x** (installed with Visual Studio)
- **StackExchange.Redis** NuGet package (auto-restored on build)
- The **tecSaaS MPT** application must be installed and licensed on the same Windows PC

---

## Build & Run

1. Open MPTSaveSpectrumLibrary-code/MPTSaveSpectrumLibrary.sln in Visual Studio.
2. Restore NuGet packages (right-click solution → **Restore NuGet Packages**).
3. Build in **Release** configuration.
4. Run MPTTrayApplication.exe on the Windows spectrometer PC. The tray icon will appear in the taskbar.

### Redis Connection

By default the application connects to localhost:6379. To point it at a remote Redis server, update RedisManager.cs with the appropriate connection string before building.

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
- This component is **independent** of the Docker stack. The Docker OPC UA server will function correctly without it; the tray app only adds automated session recovery.
- Source code is provided as-is for transparency. Pre-built binaries are not distributed in this repository.
