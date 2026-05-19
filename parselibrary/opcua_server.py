import os
import logging
import redis
import asyncio
import json
from typing import Dict, List, Any

from asyncua import Server, ua

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

REDIS_IP_ADDRESS = os.environ.get("REDIS_IP_ADDRESS", "10.20.20.11")
REDIS_PORT_NUMBER = int(os.environ.get("REDIS_PORT_NUMBER", 6379))
OPC_IP_ADDRESS = os.environ.get("OPC_IP_ADDRESS", "0.0.0.0")
OPC_PORT_NUMBER = int(os.environ.get("OPC_PORT_NUMBER", 4841))

async def opcua_loop(redis_server: redis.Redis) -> None:
    """Run the OPC UA server and continuously publish spectral data to SCADA systems.

    Sets up an OPC UA server that creates a namespace with two spectrometer channels
    (spectrouv_1 and spectrouv_2). Each channel publishes five data types (transmission,
    absorbance, reference, sample, calibration) with 201 absorption values spanning
    190-391 nm, plus a wavelength axis array. Data is polled from Redis every 1 second
    and published to connected OPC UA clients.

    The function runs indefinitely, continuously reading spectral data from Redis and
    writing it to OPC UA variables. This allows SCADA systems and industrial clients to
    subscribe to real-time spectral measurement updates.

    Args:
        redis_server: A connected redis.Redis instance for retrieving spectral data.
                      Keys should follow pattern: "{datatype}_{channel}" (e.g., "transmission_channel_1")
                      Values should be JSON-encoded lists of floats.

    Returns:
        None. Function runs indefinitely until process is terminated.

    Raises:
        Exception: If Redis key patterns cannot be found or if OPC UA node writes fail.
                   Exceptions are caught and logged; server continues operating.

    Example:
        >>> redis_client = redis.Redis(host="localhost", port=6379)
        >>> asyncio.run(opcua_loop(redis_client))
    """

    server = Server()
    await server.init()
    server.set_endpoint(f'opc.tcp://{OPC_IP_ADDRESS}:{OPC_PORT_NUMBER}')

    # Register custom namespace for BioPal SpectraUV device
    idx = await server.register_namespace('http://biopal//biopatspectrouv')
    print(idx)

    # Create OPC UA objects for two spectrometer channels
    obj_01 = await server.nodes.objects.add_object(idx, 'spectrouv_1')
    obj_02 = await server.nodes.objects.add_object(idx, 'spectrouv_2')

    # Data types published by each channel: different processing modes of spectral data
    datatype_list = ['transmission', 'absorbance', 'onlinereference', 'sample', 'calibration']
    # Wavelength array: 201 points from 190 nm to 390 nm (1 nm steps)
    wavelengths = [190.0 + i for i in range(201)]

    # Dictionary to store OPC UA node references for fast updates: {channel: {datatype: node}}
    val_nodes_dict: Dict[str, Dict[str, Any]] = {}

    for obj, channel in zip([obj_01, obj_02], ["channel_1", "channel_2"]):
        val_nodes_dict[channel] = {}
        for datatype in datatype_list:
            # Create writable variable node with 201 absorption values (one per wavelength)
            node = await obj.add_variable(idx, f"{datatype}_{channel}", [0.0]*201)
            node.set_writable()
            val_nodes_dict[channel][datatype] = node
        # Add wavelength axis as a read-only reference variable
        node = await obj.add_variable(idx, 'Wavelength', wavelengths)
        val_nodes_dict[channel]['wavelengths'] = node

    async with server:
        logger.info(f"[OPC UA] Server Started")
        while True:
            try:
                # Poll Redis for spectral data updates every 1 second
                for datatype in datatype_list:
                    # Scan Redis for keys matching "{datatype}*" (e.g., "transmission_channel_1")
                    for key in redis_server.scan_iter(f"{datatype}*"):
                        print(key)
                        data = json.loads(redis_server.get(key))
                        # Route data to correct channel node based on key name
                        if "channel_1" in key:
                            node = val_nodes_dict['channel_1'][datatype]
                        elif "channel_2" in key:
                            node = val_nodes_dict['channel_2'][datatype]
                        else:
                            logging.warning(f"NO Channel DATA found in REDIS!")
                            raise Exception(f"REDIS: NO key '{key}' found")
                        # Update OPC UA node with latest Redis value
                        await node.write_value(data)

            except Exception as ex:
                logger.warning(f"[OPC UA] Error Experienced: {ex}")

            # Poll interval: update clients at 1 Hz
            await asyncio.sleep(1.0)

if __name__ == "__main__":

    redis_server = redis.Redis(host=REDIS_IP_ADDRESS, port=REDIS_PORT_NUMBER, decode_responses=True)
    asyncio.run(opcua_loop(redis_server))