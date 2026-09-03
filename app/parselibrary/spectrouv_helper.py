import json
import asyncio
import logging
import os
from datetime import datetime, timezone
from redis import Redis

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [Watchdog] %(message)s'
)
logger = logging.getLogger(__name__)

REDIS_IP = os.environ.get("REDIS_IP_ADDRESS", os.environ.get("REDIS_IP", os.environ.get("REDIS_HOST", "localhost")))
REDIS_PORT = int(os.environ.get("REDIS_PORT_NUMBER", os.environ.get("REDIS_PORT", 6379)))


async def watchdog_cycle(r_spectrouv: Redis, set_mptrefresh: bool) -> bool:
    ch1absorbance = r_spectrouv.get("absorbance_channel_1")
    if ch1absorbance is None and not set_mptrefresh:
        logger.warning("[Watchdog] Ch1 Absorbance missing in Redis; requesting MPT refresh")
        r_spectrouv.set("mpt_refresh", "true")
        set_mptrefresh = True
        logger.info(f"[Watchdog] MPT Refresh set to True @ {datetime.now(timezone.utc)}")
    elif ch1absorbance is not None:
        set_mptrefresh = False
        data_len = len(json.loads(ch1absorbance))
        logger.debug(f"[Watchdog] Ch1 Absorbance healthy ({data_len} points)")
    await asyncio.sleep(1.0)
    return set_mptrefresh


def main():
    logger.info(f"Starting SpectroUV Watchdog connected to Redis at {REDIS_IP}:{REDIS_PORT}...")
    r_spectrouv = Redis(host=REDIS_IP, port=REDIS_PORT, decode_responses=True)
    set_mptrefresh = False

    while True:
        try:
            set_mptrefresh = asyncio.run(watchdog_cycle(r_spectrouv, set_mptrefresh))
        except Exception as e:
            logger.error(f"[Watchdog] Error: {e}")
            asyncio.run(asyncio.sleep(2.0))


if __name__ == "__main__":
    main()
