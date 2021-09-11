[![CI](https://github.com/iKaew/linkstation/actions/workflows/python-app.yml/badge.svg)](https://github.com/iKaew/linkstation/actions/workflows/python-app.yml)

# LinkStation client

This project create for handling Buffalo LinkStation NAS with original firmware. It's originally created to integrate with Home Assistant to display the current status of NAS such as online status, disk spaces used, and have ability to perform restart from within home-assistant. 

# Usage

```python
import asyncio
from linkstation import LinkStation

async def main() -> None:
    """Run!"""
    api = LinkStation("<LINKSTATION_ADMIN_USERNAME>","<LINKSTATION_ADMIN_PASSWORD>","<LINKSTATION_HOSTNAME/IP>")

    # List all disks
    disks = await api.get_all_disks_async()
    for disk in disks: 
        _LOGGER.debug(disk + ': ' + await api.get_disk_status_async(disk))

    active_disks = await api.get_active_disks_async()
    for disk in active_disks: 
        # Get disk capacity in GB
        diskCapacity = await api.get_disk_capacity_async(disk)
        
        # Get current used disk space in GB
        diskUsed = await api.get_disk_amount_used_async(disk)
        
        # Get current used disk space in percentage (provided by LinkStation)
        diskUsedPct = await api.get_disk_pct_used_async(disk)

asyncio.run(main())
```


# Notes
All api testing based on Buffalo LinkStation Duo LS-WXL
