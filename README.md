# LinkStation cli

This project create for handling Buffalo LinkStation NAS with original firmware. It's originally created to integrate with Home Assistant to display the current status of NAS such as online status, disk spaces used, and have ability to perform restart from within home-assistant. 

# Usage

```python
import asyncio

async def main() -> None:
    """Run!"""
    api = LinkStation("<YOUR_LINKSTATION_ADMIN_USERNAME>","<YOUR_LINKSTATION_ADMIN_PASSWORD>","<YOUR_LINKSTATION_NAME/IP>")

    disks = await api.get_all_disk()

asyncio.run(main())
```
