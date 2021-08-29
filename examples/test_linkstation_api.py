"""Run an example against LinkStation API."""
import asyncio
import logging

from linkstation import LinkStation

logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

async def main() -> None:
    """Create the aiohttp session and run the example."""
    
    api = api = LinkStation("<YOUR_LINKSTATION_ADMIN_USERNAME>","<YOUR_LINKSTATION_ADMIN_PASSWORD>","<YOUR_LINKSTATION_NAME/IP>")

    # List all disks
    disks = await api.get_all_disks()
    for disk in disks: 
        _LOGGER.debug(disk)

    active_disks = await api.get_active_disks()
    for disk in active_disks: 
        _LOGGER.debug(disk)

    # Terminate API Session
    await api.close()


asyncio.run(main())