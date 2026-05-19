# BioPal SpectraUV Documentation

Welcome to the BioPal SpectraUV system documentation! This site provides comprehensive guides for operators, system administrators, and developers working with the spectroscopy data acquisition and publication platform.

## What is SpectraUV?

SpectraUV is a Python-based system that:

- **Acquires UV-Vis spectral data** from binary spectrum files
- **Parses spectral absorption values** across the UV range (190-391 nm)
- **Publishes data via OPC UA** for integration with industrial SCADA systems
- **Manages data persistence** through Redis for inter-process communication

The system is designed for high-performance, real-time spectroscopy measurement workflows in industrial environments.

## Quick Links

- **[Architecture](architecture.md)** — Understand the system design and components
- **[Setup & Installation](setup.md)** — Get started with installation and configuration
- **[Quick Start](quickstart.md)** — Run the system locally in minutes
- **[User Guide](guide.md)** — Detailed guides for common tasks
- **[API Reference](#)** — Auto-generated API documentation from source code

## Key Components

### Spectral Parser (`parsing_spectra.py`)
Parses binary `.bin` files containing UV-Vis absorption spectra. Validates file integrity and extracts 201 floating-point absorption values.

### OPC UA Server (`opcua_server.py`)
Exposes parsed spectral data as OPC UA variables for real-time access by SCADA systems and industrial clients. Supports two spectrometer channels with five data types each.

## System Requirements

- Python 3.8+
- Redis server (for inter-process communication)
- OPC UA client (to consume published data)
- Linux or Windows with .NET support (for full system)

## Support

For issues or questions:

1. Check the [Troubleshooting](troubleshooting.md) guide
2. Review the [API Reference](#)
3. Check the project GitHub repository

---

**Last Updated:** 2026-05-19  
**Version:** 1.0.0
