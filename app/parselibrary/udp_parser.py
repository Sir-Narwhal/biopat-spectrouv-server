import socket
import struct
import logging
import os
import json
from redis import Redis
from typing import List, Tuple, Dict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [UDP Parser] %(message)s'
)
logger = logging.getLogger(__name__)

UDP_IP = os.environ.get("UDP_IP", "0.0.0.0")
UDP_PORT = int(os.environ.get("UDP_PORT", 20202))
UDP_CHANNEL_NAME = os.environ.get("UDP_CHANNEL_NAME", "channel_1")
REDIS_IP = os.environ.get("REDIS_IP_ADDRESS", os.environ.get("REDIS_IP", os.environ.get("REDIS_HOST", "localhost")))
REDIS_PORT = int(os.environ.get("REDIS_PORT_NUMBER", os.environ.get("REDIS_PORT", 6379)))


def unpack_udp(binary_string: bytes) -> List[float]:
    """Unpack raw binary UDP packet into 201-element spectral float list."""
    # Collect Spectra Type For Mapping
    spectra_type = struct.unpack("<B", binary_string[16:17])[0]

    # Collect Wavelength Data
    wavelength_start = struct.unpack("<f", binary_string[20:24])[0]
    wavelength_end = struct.unpack("<f", binary_string[24:28])[0]
    wavelength_increment = struct.unpack("<f", binary_string[28:32])[0]

    # Collect Dataset Info
    length = struct.unpack("<I", binary_string[8:12])[0]
    i = struct.unpack("<2H", binary_string[32:36])[0]
    header = length - 4 * i  # bytes header
    unpacked_data = struct.unpack(f"<{i}f", binary_string[header:header + 4 * i])
    return list(unpacked_data)


def collect_mpt_spectra(udp: socket.socket) -> Dict[str, List[float]]:
    """Receive and group UDP datagrams into spectral data types."""
    bytes_data_list = []
    # Collect a batch of incoming datagrams
    while len(bytes_data_list) < 11:
        byte_data = udp.recvfrom(1060)
        if len(byte_data[0]) in [144, 72]:
            continue
        bytes_data_list.append(byte_data)

    spectra_mapping = {
        4: "sample",            # Sample Intensity
        5: "onlinereference",   # Reference Intensity
        7: "transmission",      # Transmission
        9: "absorbance",        # Absorbance
        11: "calibration",      # Calibration
    }

    spectra_data = {}

    for each_spectra, connection in bytes_data_list:
        if len(each_spectra) < 36:
            continue
        spectra_type = struct.unpack("<B", each_spectra[16:17])[0]
        if (spectra_type not in spectra_mapping) or (len(each_spectra) != 840):
            continue
        data_type_name = spectra_mapping[spectra_type]
        spectra_data[data_type_name] = unpack_udp(each_spectra)

    return spectra_data


def main_loop(r: Redis, udp: socket.socket):
    data = collect_mpt_spectra(udp)
    if not data:
        return
    for key, value in data.items():
        # Store primary key (e.g. absorbance_channel_1, sample_channel_1)
        r.set(f"{key}_{UDP_CHANNEL_NAME}", json.dumps(value), ex=5)

        # Store intuitive aliases for sample/reference
        if key == "sample":
            r.set(f"intensity_{UDP_CHANNEL_NAME}", json.dumps(value), ex=5)
        elif key == "onlinereference":
            r.set(f"reference_intensity_{UDP_CHANNEL_NAME}", json.dumps(value), ex=5)


if __name__ == "__main__":
    logger.info(f"Binding UDP listener on {UDP_IP}:{UDP_PORT} (Channel: {UDP_CHANNEL_NAME})...")
    udp_listener = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    udp_listener.bind((UDP_IP, UDP_PORT))
    udp_listener.settimeout(10)

    logger.info(f"Connecting to Redis at {REDIS_IP}:{REDIS_PORT}...")
    redis_client = Redis(host=REDIS_IP, port=REDIS_PORT, decode_responses=True)

    logger.info("UDP Parser Service started successfully.")

    try:
        while True:
            try:
                main_loop(redis_client, udp_listener)
            except socket.timeout:
                logger.debug("Socket timeout waiting for UDP broadcast; retrying...")
                continue
    except KeyboardInterrupt:
        logger.info("UDP Parser interrupted by user.")
    except Exception as ex:
        logger.fatal(f"Fatal error experienced: {ex}")
    finally:
        udp_listener.close()
        logger.info("UDP Parser closed.")
