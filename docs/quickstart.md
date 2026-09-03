# Quick Start Guide

Get the BioPAT® Spectro UV Server running and publishing live 201-wavelength data in under 2 minutes!

---

## 1. Start the Docker Stack

```bash
git clone https://github.com/Sir-Narwhal/biopat-spectrouv-server-1.git
cd biopat-spectrouv-server-1

docker compose up -d
```

Verify that all three containers are healthy:
```bash
docker compose ps
```

---

## 2. Test with Simulated Spectra (No Hardware Needed)

Launch the simulated UDP emitter:

```bash
python -m parselibrary.mock_udp_emitter
```

You will see output showing periodic cycles of Reference, Sample Intensity, and Absorbance packets being transmitted to port 20202:
```
[Mock Emitter] Broadcasting mock UDP spectral data to 127.0.0.1:20202...
[Mock Emitter] Cycle 1: Broadcasted sample, reference, and absorbance (201 wavelengths @ 190-390 nm)
```

---

## 3. Connect Your OPC UA Client

Connect to:
```
opc.tcp://localhost:4841
```

In your OPC UA client (such as [UaExpert](https://www.unified-automation.com/products/development-tools/uaexpert.html)):
1. Navigate to: `Root -> Objects -> spectrouv_1`.
2. Drag `absorbance_channel_1`, `sample_channel_1`, or `Wavelength` into the Data Access View.
3. Observe live array updates in real-time!
