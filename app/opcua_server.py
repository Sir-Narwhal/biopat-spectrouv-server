"""
opcua_server.py

OPC UA Server Service for Sartorius BioPAT(R) Spectro UV.
Reads real-time 201-wavelength spectral data (intensity/sample, reference, absorbance,
transmission, calibration) from Redis and publishes them over standard OPC UA
(opc.tcp://0.0.0.0:4841) to SCADA, DCS, and bioreactor control systems.
"""

import os
import sys
import json
import signal
import logging
import asyncio
from typing import Dict, Any

import redis
from asyncua import Server

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [OPC UA Server] %(message)s'
)
logger = logging.getLogger(__name__)

# Network and Redis configuration
REDIS_HOST = os.environ.get("REDIS_IP_ADDRESS", os.environ.get("REDIS_IP", os.environ.get("REDIS_HOST", "localhost")))
REDIS_PORT = int(os.environ.get("REDIS_PORT_NUMBER", os.environ.get("REDIS_PORT", 6379)))
OPC_IP = os.environ.get("OPC_IP_ADDRESS", os.environ.get("OPC_IP", "0.0.0.0"))
OPC_PORT = int(os.environ.get("OPC_PORT_NUMBER", os.environ.get("OPC_PORT", 4841)))


async def opcua_loop(redis_client: redis.Redis) -> None:
    server = Server()
    await server.init()
    endpoint = f"opc.tcp://{OPC_IP}:{OPC_PORT}"
    server.set_endpoint(endpoint)
    server.set_server_name("BioPAT Spectro UV OPC UA Server")

    # Register namespace for BioPAT Spectro UV
    idx = await server.register_namespace("http://biopat/spectrouv")

    channels = ["channel_1", "channel_2"]
    datatypes = ['transmission', 'absorbance', 'onlinereference', 'sample', 'calibration']

    # 201 wavelengths from 190.0 to 390.0 nm (1.0 nm increments)
    wavelengths = [190.0 + i for i in range(201)]

    nodes: Dict[str, Dict[str, Any]] = {}

    for ch in channels:
        nodes[ch] = {}
        ch_num = ch.split("_")[1]
        obj = await server.nodes.objects.add_object(idx, f"spectrouv_{ch_num}")

        # Wavelength axis node (read-only reference array)
        wl_node = await obj.add_variable(idx, "Wavelength", wavelengths)
        nodes[ch]["wavelengths"] = wl_node

        # Spectral data variables (201 floats each)
        for dt in datatypes:
            node = await obj.add_variable(idx, f"{dt}_{ch}", [0.0] * 201)
            await node.set_writable()
            nodes[ch][dt] = node

        # Modern aliases for intuitive SCADA tag browsing
        intensity_node = await obj.add_variable(idx, f"intensity_{ch}", [0.0] * 201)
        await intensity_node.set_writable()
        nodes[ch]["intensity"] = intensity_node

        ref_node = await obj.add_variable(idx, f"reference_intensity_{ch}", [0.0] * 201)
        await ref_node.set_writable()
        nodes[ch]["reference_intensity"] = ref_node

    async with server:
        logger.info(f"[OPC UA Server] Started listening on {endpoint}")
        logger.info(f"[OPC UA Server] Exposing 201 wavelengths for channels: {channels}")

        while True:
            try:
                for dt in datatypes:
                    for key in redis_client.scan_iter(f"{dt}*"):
                        raw_data = redis_client.get(key)
                        if not raw_data:
                            continue
                        data = json.loads(raw_data)
                        ch = "channel_1" if "channel_1" in key else "channel_2" if "channel_2" in key else None
                        if ch and ch in nodes and dt in nodes[ch]:
                            await nodes[ch][dt].write_value(data)
                            if dt == "sample":
                                await nodes[ch]["intensity"].write_value(data)
                            elif dt == "onlinereference":
                                await nodes[ch]["reference_intensity"].write_value(data)

            except Exception as ex:
                logger.warning(f"[OPC UA Server] Error updating nodes: {ex}")

            await asyncio.sleep(1.0)


def main():
    def shutdown_handler(signum, frame):
        logger.info("Shutting down OPC UA server...")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    logger.info(f"Connecting to Redis at {REDIS_HOST}:{REDIS_PORT}...")
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    try:
        r.ping()
        logger.info("Connected to Redis successfully.")
    except Exception as e:
        logger.error(f"Cannot connect to Redis: {e}")
        sys.exit(1)

    asyncio.run(opcua_loop(r))


if __name__ == "__main__":
    main()
