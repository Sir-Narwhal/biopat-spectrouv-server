# BioPAT® Spectro UV Server Documentation

Welcome to the **BioPAT® Spectro UV Server** documentation! This system provides real-time 201-wavelength UV-Vis spectroscopy acquisition and industrial OPC UA publication for Sartorius BioPAT® Spectro UV / tec5 spectrometers.

---

## What is BioPAT Spectro UV Server?

In industrial biomanufacturing and laboratory bioprocess monitoring, UV-Vis spectrometers capture continuous absorption curves across hundreds of wavelengths. However, standard automation setups usually constrain operators to extracting only 1 to 4 fixed wavelengths for DCS/SCADA historians.

**BioPAT Spectro UV Server unlocks 201 simultaneous wavelengths (190 nm to 390 nm in 1 nm increments)**:
- **Direct UDP Ingestion**: Captures high-frequency 840-byte UDP broadcasts from the tec5 tecSaaS MPT software (the vendor control application driving the spectrometer) — 5 datagrams per cycle, one per data type.
- **Microservices Architecture**: Runs as a 4-container Docker stack (`udpparser`, `redisserver`, `opcserver`, `udphelper`).
- **Industrial Standards Compliance**: Publishes full spectral arrays over OPC UA (`opc.tcp://<host>:4841`) to SCADA, DeltaV, Ignition, or OSIsoft PI.
- **Hardware-Free Testing**: Includes a mock UDP emitter to simulate full UV-Vis spectra with zero hardware attached.
- **Automated Recovery**: A Redis watchdog (`udphelper`) flags stale spectral data so the optional Windows tray companion can restart the spectrometer's measurement session automatically.

---

## System Quick Links

- **[Architecture](architecture.md)** — Understand the 4-container design and UDP protocol format
- **[Quick Start](quickstart.md)** — Spin up the Docker stack in under 2 minutes
- **[Setup & Deployment](setup.md)** — Container configuration and environment variables
- **[User Guide](guide.md)** — SCADA and OPC UA client integration
- **[API Reference](api/udp-parser.md)** — Detailed module documentation, including the [Watchdog service](api/watchdog.md)
- **[Troubleshooting](troubleshooting.md)** — Solutions for network and port issues

---

## Quick Command Reference

```bash
# Clone and start the stack
git clone https://github.com/Sir-Narwhal/biopat-spectrouv-server-1.git
cd biopat-spectrouv-server-1
docker compose up -d

# Run simulated spectra test
python -m parselibrary.mock_udp_emitter
```
