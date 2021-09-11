import json
import logging
import aiohttp
from expiringdict import ExpiringDict

from .const import (
    DEFAULT_DATA_CACHE_SECONDS,
    DEFAULT_NAS_LANGUAGE,
    DEFAULT_PROTOCOL,
    LINKSTATION_API_ACTION_PARAM_NAME,
    LINKSTATION_API_AUTH_REPONSE_PAGEMODE,
    LINKSTATION_API_AUTH_REPONSE_SID,
    LINKSTATION_API_GETALLDISK_FUNC_NAME,
    LINKSTATION_API_GETSETTINGS_FUNC_NAME,
    LINKSTATION_API_LOGIN_FUNC_NAME,
    LINKSTATION_API_REBOOT_ACTION_NAME,
    LINKSTATION_API_REBOOT_FUNC_NAME,
    LINKSTATION_API_PARAM_PASSWORD,
    LINKSTATION_API_PARAM_USERNAME,
    LINKSTATION_API_ENDPOINT,
    LINKSTATION_API_FUNCTION_PARAM_NAME,
    LINKSTATION_API_REPONSE_DATA_DISK_AMOUNT_USED,
    LINKSTATION_API_REPONSE_DATA_DISK_CAPACITY,
    LINKSTATION_API_REPONSE_DATA_DISK_ELEMENT,
    LINKSTATION_API_REPONSE_DATA_DISK_PCT_USED,
    LINKSTATION_API_REPONSE_DATA_DISK_STATUS,
    LINKSTATION_API_REPONSE_DATA_DISK_STATUS_DISCONNECT,
    LINKSTATION_API_REPONSE_DATA_DISK_STATUS_REMOVE,
    LINKSTATION_API_REPONSE_DATA_DISK_UNITNAME,
    LINKSTATION_API_REPONSE_DATA_GENERALINFO_ELEMENT,
    LINKSTATION_API_REPONSE_DATA_ELEMENT,
    LINKSTATION_API_REPONSE_SUCCESS_STATUS,
    LINKSTATION_COOKIE_PREFIX,
    LINKSTATION_COOKIE_SEPARATOR,
)


_LOGGER = logging.getLogger(__name__)


class LinkStation:
    """A class for manage LinkStation instance."""

    def __init__(
        self,
        username,
        password,
        address,
        session=None,
        language=DEFAULT_NAS_LANGUAGE,
        protocol=DEFAULT_PROTOCOL,
        cache_age=DEFAULT_DATA_CACHE_SECONDS,
    ) -> None:

        self._username = username
        self._password = password
        self._address = address
        self._language = language
        self._protocol = protocol
        self._session = session
        self._api = None
        self._cache = ExpiringDict(max_len=10, max_age_seconds=cache_age)

    async def get_data_with_cache_async(self):
        data = None

        if self._cache.get(LINKSTATION_API_REPONSE_DATA_ELEMENT) is not None:
            data = self._cache.get(LINKSTATION_API_REPONSE_DATA_ELEMENT)
        else:
            _LOGGER.debug("Data key{%s} missing from cache", LINKSTATION_API_REPONSE_DATA_ELEMENT)
            data = await self.get_disks_info_async()

        return data

    async def connect_async(self):

        self._api = "{}://{}/{}".format(
            self._protocol, self._address, LINKSTATION_API_ENDPOINT
        )
        formdata = aiohttp.FormData()
        formdata.add_field(
            LINKSTATION_API_FUNCTION_PARAM_NAME, LINKSTATION_API_LOGIN_FUNC_NAME
        )
        formdata.add_field(LINKSTATION_API_PARAM_USERNAME, self._username)
        formdata.add_field(LINKSTATION_API_PARAM_PASSWORD, self._password)

        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        async with self._session.post(self._api, data=formdata) as authresp:
            _LOGGER.debug(await authresp.text())
            authData = json.loads(await authresp.text())

            if self._is_success(authData):
                self._sid = self._get_user_sid(authData)
                self._pagemode = self._get_pagemode(authData)
                self._cookies = self._create_authentication_cookie()
            else:
                _LOGGER.error("Authentication failed")

    def _is_success(self, authresponsejson):
        return authresponsejson[LINKSTATION_API_REPONSE_SUCCESS_STATUS]

    def _get_user_sid(self, authresponsejson):
        return authresponsejson[LINKSTATION_API_REPONSE_DATA_ELEMENT][0][
            LINKSTATION_API_AUTH_REPONSE_SID
        ]

    def _get_pagemode(self, authresponsejson):
        return authresponsejson[LINKSTATION_API_REPONSE_DATA_ELEMENT][0][
            LINKSTATION_API_AUTH_REPONSE_PAGEMODE
        ]

    def _create_authentication_cookie(self):
        return {
            LINKSTATION_COOKIE_PREFIX
            + self._username: self._sid
            + LINKSTATION_COOKIE_SEPARATOR
            + self._language
            + LINKSTATION_COOKIE_SEPARATOR
            + str(self._pagemode)
        }

    async def _get_settings_info(self):

        if self._session == None:
            await self.connect_async()

        params = {
            LINKSTATION_API_FUNCTION_PARAM_NAME: LINKSTATION_API_GETSETTINGS_FUNC_NAME
        }

        async with self._session.get(
            self._api, params=params, cookies=self._cookies
        ) as settingresp:
            settingInfo = json.loads(await settingresp.text())

            if self._is_success(settingInfo):
                _LOGGER.debug(await settingresp.text())
                self._cache['settingInfo'] = settingInfo
                return settingInfo
            return None

    async def get_spaces_info_desc_async(self):
        return await self._get_settingsinfo_field_async("r_storage")

    async def get_linkstation_name_async(self):
        return await self._get_settingsinfo_field_async("r_hostname")

    async def get_linkstation_ipaddress_async(self):
        return await self._get_settingsinfo_field_async("r_ipAddr:1")

    async def get_linkstation_firmware_version_async(self):
        return await self._get_settingsinfo_field_async("r_version")

    async def _get_settingsinfo_field_async(self, fieldname):
        if self._cache.get("settingInfo") == None:
            _LOGGER.debug("Setting Info {%s} missing from cache", fieldname)
            settingInfo = await self._get_settings_info()
        else:
            settingInfo = self._cache.get("settingInfo")


        for data in settingInfo[LINKSTATION_API_REPONSE_DATA_ELEMENT][0][
            LINKSTATION_API_REPONSE_DATA_GENERALINFO_ELEMENT
        ]:
            if data["name"] == fieldname:
                _LOGGER.debug(fieldname + ": " + data["value"])
                return data["value"]

    async def restart_async(self):
        if self._session == None:
            await self.connect_async()

        formdata = aiohttp.FormData()
        formdata.add_field(
            LINKSTATION_API_FUNCTION_PARAM_NAME, LINKSTATION_API_REBOOT_FUNC_NAME
        )
        formdata.add_field(
            LINKSTATION_API_ACTION_PARAM_NAME, LINKSTATION_API_REBOOT_ACTION_NAME
        )

        async with self._session.post(
            self._api, data=formdata, cookies=self._cookies
        ) as rebootresp:
            rebootInfo = json.loads(await rebootresp.text())
            _LOGGER.debug(await rebootresp.text())
            if self._is_success(rebootInfo):
                _LOGGER.info("LinkStation restarting ... ")

    async def get_disks_info_with_cache_async(self):
        if self._cache[LINKSTATION_API_REPONSE_DATA_ELEMENT]:
            return self._cache[LINKSTATION_API_REPONSE_DATA_ELEMENT]

        return await self.get_disks_info_async()

    async def get_disks_info_async(self):
        if self._session == None or self._session.closed:
            await self.connect_async()

        formdata = aiohttp.FormData()
        formdata.add_field(
            LINKSTATION_API_FUNCTION_PARAM_NAME, LINKSTATION_API_GETALLDISK_FUNC_NAME
        )

        async with self._session.post(
            self._api, data=formdata, cookies=self._cookies
        ) as getdisksresp:
            getdisksinfo = json.loads(await getdisksresp.text())
            _LOGGER.debug(await getdisksresp.text())

            if self._is_success(getdisksinfo):
                self._cache[LINKSTATION_API_REPONSE_DATA_ELEMENT] = getdisksinfo[LINKSTATION_API_REPONSE_DATA_ELEMENT]
                return getdisksinfo[LINKSTATION_API_REPONSE_DATA_ELEMENT]
            else:
                return None

    async def get_all_disks_async(self):

        diskInfo = await self.get_data_with_cache_async()

        disk_list = []

        for dataelement in diskInfo:
            disk_list.append(dataelement[LINKSTATION_API_REPONSE_DATA_DISK_ELEMENT])

        return disk_list

    async def get_active_disks_async(self):
        disk_list = await self.get_all_disks_async()
        active_list = []
        for disk in disk_list:
            if await self.get_disk_status_async(disk) not in (
                LINKSTATION_API_REPONSE_DATA_DISK_STATUS_REMOVE,
                LINKSTATION_API_REPONSE_DATA_DISK_STATUS_DISCONNECT,
            ):
                active_list.append(disk)

        return active_list

    async def get_disk_status_async(self, diskName):
        diskInfo = await self.get_data_with_cache_async()

        for data in diskInfo:
            if data[LINKSTATION_API_REPONSE_DATA_DISK_ELEMENT] == diskName:
                return data[LINKSTATION_API_REPONSE_DATA_DISK_STATUS]

        return None
    
    def get_disk_status(self, diskName):
        diskInfo = self._cache.get(LINKSTATION_API_REPONSE_DATA_ELEMENT)

        for data in diskInfo:
            if data[LINKSTATION_API_REPONSE_DATA_DISK_ELEMENT] == diskName:
                return data[LINKSTATION_API_REPONSE_DATA_DISK_STATUS]

        return None

    async def get_disk_data_async(self, diskName):
        diskInfo = await self.get_data_with_cache_async()

        for data in diskInfo:
            if data[LINKSTATION_API_REPONSE_DATA_DISK_ELEMENT] == diskName:
                return data

        return None
    
    def get_disk_data(self, diskName):
        diskInfo = self._cache.get(LINKSTATION_API_REPONSE_DATA_ELEMENT)

        for data in diskInfo:
            if data[LINKSTATION_API_REPONSE_DATA_DISK_ELEMENT] == diskName:
                return data

        return None

    async def get_disk_capacity_async(self, diskName) -> int:
        """Get disk capacity, data return in GB"""
        diskInfo = await self.get_data_with_cache_async()

        for data in diskInfo:
            if data[LINKSTATION_API_REPONSE_DATA_DISK_ELEMENT] == diskName:
                return self._format_disk_space(
                    data[LINKSTATION_API_REPONSE_DATA_DISK_CAPACITY]
                )

        return None

    def get_disk_capacity(self, diskName) -> int:
        """Get disk capacity, data return in GB"""
        diskInfo = self._cache.get(LINKSTATION_API_REPONSE_DATA_ELEMENT)

        for data in diskInfo:
            if data[LINKSTATION_API_REPONSE_DATA_DISK_ELEMENT] == diskName:
                return self._format_disk_space(
                    data[LINKSTATION_API_REPONSE_DATA_DISK_CAPACITY]
                )

        return None

    async def get_disk_amount_used_async(self, diskName) -> int:
        """Get disk spaces used, data return in GB"""
        diskInfo = await self.get_data_with_cache_async()

        for data in diskInfo:
            if data[LINKSTATION_API_REPONSE_DATA_DISK_ELEMENT] == diskName:
                return self._format_disk_space(
                    data[LINKSTATION_API_REPONSE_DATA_DISK_AMOUNT_USED]
                )

        return None

    def get_disk_amount_used(self, diskName) -> int:
        """Get disk spaces used, data return in GB"""
        diskInfo = self._cache.get(LINKSTATION_API_REPONSE_DATA_ELEMENT)

        for data in diskInfo:
            if data[LINKSTATION_API_REPONSE_DATA_DISK_ELEMENT] == diskName:
                return self._format_disk_space(
                    data[LINKSTATION_API_REPONSE_DATA_DISK_AMOUNT_USED]
                )

        return None

    def _format_disk_space(self, diskSpaceStr: str) -> int:
        number = diskSpaceStr.removesuffix(" KB").replace(",", "")
        return round(int(number) / 1024 / 1024)

    def _format_disk_pct(self, diskPct: str) -> float:
        percentUsed = diskPct.removesuffix(" %")
        return float(percentUsed)

    async def get_disk_pct_used_async(self, diskName) -> float:
        """Get disk space used, data return in percentage"""
        diskInfo = await self.get_data_with_cache_async()

        for data in diskInfo:
            if data[LINKSTATION_API_REPONSE_DATA_DISK_ELEMENT] == diskName:
                return self._format_disk_pct(
                    data[LINKSTATION_API_REPONSE_DATA_DISK_PCT_USED]
                )

        return None

    def get_disk_pct_used(self, diskName) -> float:
        """Get disk space used, data return in percentage"""
        diskInfo = self._cache.get(LINKSTATION_API_REPONSE_DATA_ELEMENT)

        for data in diskInfo:
            if data[LINKSTATION_API_REPONSE_DATA_DISK_ELEMENT] == diskName:
                return self._format_disk_pct(
                    data[LINKSTATION_API_REPONSE_DATA_DISK_PCT_USED]
                )

        return None

    async def get_disk_free_async(self, diskName) -> int:
        """Get disk space used, data return in percentage"""
        diskInfo = await self.get_data_with_cache_async()

        for data in diskInfo:
            if data[LINKSTATION_API_REPONSE_DATA_DISK_ELEMENT] == diskName:
                return self._format_disk_space(
                    data[LINKSTATION_API_REPONSE_DATA_DISK_CAPACITY]
                ) - self._format_disk_space(
                    data[LINKSTATION_API_REPONSE_DATA_DISK_AMOUNT_USED]
                )

        return None

    def get_disk_free(self, diskName) -> int:
        """Get disk space used, data return in percentage"""
        diskInfo = diskInfo = self._cache.get(LINKSTATION_API_REPONSE_DATA_ELEMENT)

        for data in diskInfo:
            if data[LINKSTATION_API_REPONSE_DATA_DISK_ELEMENT] == diskName:
                return self._format_disk_space(
                    data[LINKSTATION_API_REPONSE_DATA_DISK_CAPACITY]
                ) - self._format_disk_space(
                    data[LINKSTATION_API_REPONSE_DATA_DISK_AMOUNT_USED]
                )

        return None

    async def get_disk_unit_name_async(self, diskName):
        """Get HDD manufacturing info."""
        diskInfo = await self.get_data_with_cache_async()

        for data in diskInfo:
            if data[LINKSTATION_API_REPONSE_DATA_DISK_ELEMENT] == diskName:
                return data[LINKSTATION_API_REPONSE_DATA_DISK_UNITNAME].strip()

        return None

    def get_disk_unit_name(self, diskName):
        """Get HDD manufacturing info."""
        diskInfo = self._cache.get(LINKSTATION_API_REPONSE_DATA_ELEMENT)

        for data in diskInfo:
            if data[LINKSTATION_API_REPONSE_DATA_DISK_ELEMENT] == diskName:
                return data[LINKSTATION_API_REPONSE_DATA_DISK_UNITNAME].strip()

        return None

    async def close(self):
        if self._session:
            await self._session.close()
