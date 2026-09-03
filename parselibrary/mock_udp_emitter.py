"""
mock_udp_emitter.py

Test utility that generates and broadcasts synthetic 840-byte UDP spectral packets
(intensity, reference intensity, and absorbance across 201 wavelengths from 190 to 390 nm)
matching the exact tec5 protocol to test the complete stack without physical hardware.
"""

import time
import math
import struct
import socket
import logging
import argparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [Mock Emitter] %(message)s'
)
logger = logging.getLogger(__name__)


def build_tec5_packet(spec_type: int, channel: int = 1, t_offset: float = 0.0) -> bytes:
    """Construct an authentic 840-byte tec5 UDP datagram (36 bytes header + 201 floats)."""
    w_start = 190.0
    w_end = 390.0
    w_step = 1.0
    num_pts = 201
    payload_len = 840

    values = []
    for i in range(num_pts):
        wl = w_start + i * w_step
        if spec_type == 5:
            # Reference intensity: baseline lamp emission curve
            val = 8000.0 + 3000.0 * math.sin((wl - 190.0) / 100.0)
        elif spec_type == 4:
            # Sample intensity: attenuated by UV-absorbing peak at 280 nm
            ref_val = 8000.0 + 3000.0 * math.sin((wl - 190.0) / 100.0)
            peak = 0.8 * math.exp(-((wl - 280.0) ** 2) / (2 * (15.0 ** 2)))
            noise = 0.02 * math.sin(t_offset + wl)
            val = ref_val * (10.0 ** (-(peak + noise)))
        elif spec_type == 9:
            # Absorbance: typical UV-Vis protein absorbance profile
            val = 0.8 * math.exp(-((wl - 280.0) ** 2) / (2 * (15.0 ** 2))) + 0.05 * math.sin(t_offset)
        elif spec_type == 7:
            # Transmission
            val = 0.85
        elif spec_type == 11:
            # Calibration
            val = 1.0
        else:
            val = 1000.0
        values.append(float(val))

    # 36-byte header
    header = struct.pack(
        '<4sIIHHHHfffI',
        b'\x00\x00\x20\x08',
        0x00001010,
        payload_len,
        0, 0,
        spec_type,
        channel | (1 << 8),
        w_start, w_end, w_step,
        num_pts
    )

    data = struct.pack(f'<{num_pts}f', *values)
    return header + data


def main():
    parser = argparse.ArgumentParser(description="Emit mock tec5 UDP spectral packets.")
    parser.add_argument("--host", default="127.0.0.1", help="Target UDP host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=20202, help="Target UDP port (default: 20202)")
    parser.add_argument("--interval", type=float, default=1.0, help="Interval in seconds (default: 1.0)")
    parser.add_argument("--channel", type=int, default=1, help="Channel index (default: 1)")
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    logger.info(f"Broadcasting mock UDP spectral data to {args.host}:{args.port}...")

    step = 0
    try:
        while True:
            t = step * 0.1
            # Broadcast Reference (5), Sample (4), and Absorbance (9)
            sock.sendto(build_tec5_packet(5, channel=args.channel, t_offset=t), (args.host, args.port))
            sock.sendto(build_tec5_packet(4, channel=args.channel, t_offset=t), (args.host, args.port))
            sock.sendto(build_tec5_packet(9, channel=args.channel, t_offset=t), (args.host, args.port))

            step += 1
            if step % 5 == 1:
                logger.info(f"Cycle {step}: Broadcasted sample, reference, and absorbance (201 wavelengths @ 190-390 nm)")

            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("Mock emitter stopped.")
    finally:
        sock.close()


if __name__ == '__main__':
    main()
