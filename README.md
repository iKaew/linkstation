[![CI](https://github.com/iKaew/linkstation/actions/workflows/python-app.yml/badge.svg)](https://github.com/iKaew/linkstation/actions/workflows/python-app.yml)

# LinkStation cli

This project create for handling Buffalo LinkStation NAS with original firmware. It's originally created to integrate with Home Assistant to display the current status of NAS such as online status, disk spaces used, and have ability to perform restart from within home-assistant. 

# Usage

```python
import asyncio

async def main() -> None:
    """Run!"""
    api = LinkStation("<YOUR_LINKSTATION_ADMIN_USERNAME>","<YOUR_LINKSTATION_ADMIN_PASSWORD>","<YOUR_LINKSTATION_NAME/IP>")

    disks = await api.get_all_disk()
    await api.close()

asyncio.run(main())
```


# Notes
All api testing based on Buffalo LinkStation Duo LS-WXL