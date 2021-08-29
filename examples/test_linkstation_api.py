"""Run an example against LinkStation API."""
import asyncio
import logging

from linkstation import LinkStation

logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

async def main() -> None:
    """Create the aiohttp session and run the example."""
    
    api = LinkStation("<YOUR_LINKSTATION_ADMIN_USERNAME>","<YOUR_LINKSTATION_ADMIN_PASSWORD>","<YOUR_LINKSTATION_NAME/IP>")

     # List all disks
    disks = await api.get_all_disks()
    for disk in disks: 
        _LOGGER.debug(disk + ': ' + await api.get_disk_status(disk))

    active_disks = await api.get_active_disks()
    for disk in active_disks: 
        diskCapacity = await api.get_disk_capacity(disk)
        diskUsed = await api.get_disk_amount_used(disk)
        diskUsedPct = await api.get_disk_pct_used(disk)
        _LOGGER.debug("disk %s: %s / %s GB", disk, diskUsed, diskCapacity)
        _LOGGER.debug("pct used %s%%", round(diskUsedPct, 2))


    # Terminate API Session
    await api.close()


asyncio.run(main())