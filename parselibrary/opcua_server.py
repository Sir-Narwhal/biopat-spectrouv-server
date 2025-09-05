import os 
import logging 
import redis
import asyncio

from asyncua import Server, ua 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

REDIS_IP_ADDRESS = os.environ.get("REDIS_IP_ADDRESS")
REDIS_PORT_NUMBER = os.environ.get("REDIS_PORT_NUMBER") 
OPC_IP_ADDRESS = os.environ.get("OPC_IP_ADDRESS") 
OPC_PORT_NUMBER = os.environ.get("OPC_PORT_NUMBER") 

async def opcua_loop(redis_server): 
    '''
    Aysnc Function:         opcua_loop 

    @author:        Joel Baarbe / ChatGPT 
    @date:          04/10/2025 
    
    '''

    server = Server() 
    await server.init() 
    server.set_endpoint(f'opc.tcp://{OPC_IP_ADDRESS}:{OPC_PORT_NUMBER}') 
    
    idx = await server.register_namespace('http://McMasterUniversityBioprocessAutomationLab//BioPATSpectroUV//Channel02') 
    obj = await server.nodes.objects.add_object(idx, 'SpectroUV_Channel02') 

    val_node_abs = await obj.add_variable(idx, 'Absorbance', [0.0]*201)
    val_node_time = await obj.add_variable(idx, 'Time', ua.Variant("", ua.VariantType.String)) 
    val_node_wavelength = await obj.add_variable(idx, 'Wavelength', [0.0])

    await val_node_abs.set_writable() 
    await val_node_time.set_writable()
    await val_node_wavelength.set_writable()

    wavelengths = [190.0 + i for i in range(202)]

    async with server: 

        logger.info(f"[OPC UA] Server Started") 

        while True: 
            
            try: 
                spectral_data_encoded = redis_server.json().get("spectral_data") 
                data = spectral_data_encoded #.decode('utf-8')  
                
                await val_node_abs.write_value(data.get('spectrumdata', [0.0]*201))
                await val_node_time.write_value("0.0")
                await val_node_wavelength.write_value(wavelengths)

                await asyncio.sleep(0.5) 

            except Exception as ex:
                logger.warning(f"[OPC UA] Error Experienced: {ex}") 
                await asyncio.sleep(0.5) 

if __name__ == "__main__": 

    redis_server = redis.Redis(host=REDIS_IP_ADDRESS, port=REDIS_PORT_NUMBER, decode_responses=True) 
    asyncio.run(opcua_loop(redis_server))