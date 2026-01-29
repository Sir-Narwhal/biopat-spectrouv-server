import os 
import logging 
import redis
import asyncio
import json

from asyncua import Server, ua 

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

REDIS_IP_ADDRESS = os.environ.get("REDIS_IP_ADDRESS", "10.20.20.11")
REDIS_PORT_NUMBER = os.environ.get("REDIS_PORT_NUMBER", 6379) 
OPC_IP_ADDRESS = os.environ.get("OPC_IP_ADDRESS", "0.0.0.0") 
OPC_PORT_NUMBER = os.environ.get("OPC_PORT_NUMBER", 4841) 

async def opcua_loop(redis_server): 
    '''
    Aysnc Function:         opcua_loop 

    @author:        Joel Baarbe / ChatGPT 
    @date:          04/10/2025 
    
    '''

    server = Server() 
    await server.init() 
    server.set_endpoint(f'opc.tcp://{OPC_IP_ADDRESS}:{OPC_PORT_NUMBER}') 
    
    idx = await server.register_namespace('http://biopal//biopatspectrouv') 
    print(idx) 
    _node_id = lambda name: f"ns={idx};s={name}"

    obj_01 = await server.nodes.objects.add_object(idx, 'spectrouv_1') 
    obj_02 = await server.nodes.objects.add_object(idx, 'spectrouv_2')

    
    datatype_list = ['transmission', 'absorbance', 'onlinereference', 'sample', 'calibration']
    wavelengths = [190.0 + i for i in range(201)]

    val_nodes_dict = {}

    for obj, channel in zip([obj_01, obj_02], ["channel_1", "channel_2"]):
        val_nodes_dict[channel] = {}
        for datatype in datatype_list: 
            node = await obj.add_variable(idx, f"{datatype}_{channel}", [0.0]*201)
            node.set_writable()
            val_nodes_dict[channel][datatype] = node
        node = await obj.add_variable(idx, 'Wavelength', wavelengths)
        val_nodes_dict[channel]['wavelengths'] = node
    
    async with server: 
        logger.info(f"[OPC UA] Server Started") 
        while True: 
            try:
                for datatype in datatype_list: 
                    for key in redis_server.scan_iter(f"{datatype}*"): 
                        print(key)
                        data = json.loads(redis_server.get(key))
                        if "channel_1" in key: 
                            node = val_nodes_dict['channel_1'][datatype] 
                        elif "channel_2" in key: 
                            node = val_nodes_dict['channel_2'][datatype] 
                        else: 
                            logging.warning(f"NO Channel DATA found in REDIS!") 
                            raise Exception(f"REDIS: NO key '{key}' found")
                        await node.write_value(data) 
                        
            except Exception as ex:
                logger.warning(f"[OPC UA] Error Experienced: {ex}") 

            await asyncio.sleep(1.0) 

if __name__ == "__main__": 

    redis_server = redis.Redis(host=REDIS_IP_ADDRESS, port=REDIS_PORT_NUMBER, decode_responses=True) 
    asyncio.run(opcua_loop(redis_server))