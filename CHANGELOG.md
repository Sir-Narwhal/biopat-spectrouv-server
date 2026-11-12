# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0](https://github.com/Sir-Narwhal/biopat-spectrouv-server/compare/v1.0.1...v1.1.0) (2026-11-12)


### Features

* support offline deployment from exported Docker image archives ([#26](https://github.com/Sir-Narwhal/biopat-spectrouv-server/issues/26)) ([b88a347](https://github.com/Sir-Narwhal/biopat-spectrouv-server/commit/b88a34737b869bcc9d7b5af2eb719060af568819))

## [Unreleased]

---

## [1.0.1] - 2026-09-30

### Added

- GitHub PR template (`.github/PULL_REQUEST_TEMPLATE.md`) and issue templates (`.github/ISSUE_TEMPLATE/`) for bug reports and feature requests.
- CI status badge in README.md.

### Changed

- MPT Guardian's installer (`setup.exe`, `install_MPTGuardian_v1.0.0.msi`) and standalone `.exe` are now distributed as GitHub Release assets instead of being committed to the repository. README.md and tray_app/README.md now link to the Releases page. These binaries are unchanged from v1.0.0 (the tray app itself was not modified) and are re-attached to this release so they're available from the latest release, not just v1.0.0.
- Bumped `deploy-docs.yml` workflow actions (`actions/checkout` to v4, `actions/setup-python` to v5, `peaceiris/actions-gh-pages` to v4) to match versions already used in `ci.yml`.

---

## [1.0.0] - 2026-09-03

### Added

- **UDP Parser service** (udp_parser.py): High-throughput UDP socket listener that unpacks 840-byte binary tec5/Sartorius BioPAT® Spectro UV datagrams into 201-wavelength float arrays and writes them to Redis with a 5-second auto-expiry TTL.
- **OPC UA Server service** (opcua_server.py): Asyncio-based OPC UA server (port 4841) exposing `Channel 1` and `Channel 2` nodes with 201-element float arrays for Sample Intensity, Reference Intensity, Absorbance, Transmission, Calibration, and Wavelength Axis.
- **Watchdog helper service** (spectrouv_helper.py): Background Redis watchdog that monitors Ch1 Absorbance freshness and sets an `mpt_refresh` flag when data is stale.
- **Mock UDP Emitter** (mock_udp_emitter.py): Synthetic tec5 packet broadcaster for full end-to-end testing without physical hardware. Generates realistic Gaussian absorbance profiles, lamp emission curves, and transmission data across 201 wavelengths.
- **4-container Docker Compose stack** (compose.yaml): Orchestrates `redisserver` (Redis 7 Alpine), `udpparser`, `opcserver`, and `udphelper` as a self-contained, production-ready microservices stack with `restart: always` policies.
- **Multi-stage Dockerfile** (app/Dockerfile): Alpine-based multi-stage image producing separate `udpparser`, `opcserver`, and `udphelper` build targets.
- **Environment configuration** (.env.example): Template for overriding all network, port, and Redis parameters via environment variables.
- **Windows tray application companion** (tray_app/): C#/.NET Framework Windows tray app for automating tec5 tecSaaS MPT session management via Redis signal keys.
- **MkDocs Material documentation site** (docs/): Full documentation including architecture overview, quickstart, setup & deployment, API reference, and troubleshooting guide.
- **GitHub Actions workflow** (.github/workflows/deploy-docs.yml): Automated deployment of the documentation site to GitHub Pages on push to `main`.
- **CITATION.cff**: Citation metadata for academic use.

### Supported Spectral Data Types

| Type | tec5 Packet ID | Description |
|---|---|---|
| Sample Intensity | 4 | Raw photon counts |
| Reference Intensity | 5 | Baseline lamp intensity |
| Transmission | 7 | Transmittance ratio |
| Absorbance | 9 | Optical absorbance (AU) |
| Calibration | 11 | Dark/factory calibration |

[Unreleased]: https://github.com/Sir-Narwhal/biopat-spectrouv-server/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/Sir-Narwhal/biopat-spectrouv-server/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/Sir-Narwhal/biopat-spectrouv-server/releases/tag/v1.0.0
