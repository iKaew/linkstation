
import json
import logging
import aiohttp

from const import DEFAULT_NAS_LANGUAGE, DEFAULT_PROTOCOL, LINKSTATION_API_ACTION_PARAM_NAME, LINKSTATION_API_GETALLDISK_FUNC_NAME, LINKSTATION_API_GETSETTINGS_FUNC_NAME, LINKSTATION_API_LOGIN_FUNC_NAME, LINKSTATION_API_REBOOT_ACTION_NAME, LINKSTATION_API_REBOOT_FUNC_NAME, LINKSTATION_API_PARAM_PASSWORD, LINKSTATION_API_PARAM_USERNAME, LINKSTATION_API_ENDPOINT, LINKSTATION_API_FUNCTION_PARAM_NAME, LINKSTATION_API_REPONSE_DATA_NAME


_LOGGER = logging.getLogger(__name__)

class LinkStation: 
    """A class for handling Link Station services"""

    def __init__(self, 
        username, 
        password, 
        address, 
        language = DEFAULT_NAS_LANGUAGE,
        protocol = DEFAULT_PROTOCOL) -> None:

        self._username = username
        self._password = password
        self._address = address
        self._language = language
        self._protocol = protocol
        self._session = None
        self._api = None      
        self._settingInfo = None

    async def connect(self):

        self._api = '{}://{}/{}'.format(self._protocol, self._address, LINKSTATION_API_ENDPOINT)
        formdata = aiohttp.FormData()
        formdata.add_field(LINKSTATION_API_FUNCTION_PARAM_NAME, LINKSTATION_API_LOGIN_FUNC_NAME)
        formdata.add_field(LINKSTATION_API_PARAM_USERNAME, self._username)
        formdata.add_field(LINKSTATION_API_PARAM_PASSWORD, self._password)

        self._session = aiohttp.ClientSession()
        async with self._session.post(self._api, data=formdata) as authresp:
            _LOGGER.debug(await authresp.text())
            authData = json.loads(await authresp.text())

            if (self._is_success(authData)) :
                self._sid = self._get_user_sid(authData)
                self._pagemode = self._get_pagemode(authData)                
                self._cookies = self._create_authentication_cookie()
            else:
                _LOGGER.error('Authentication failed')
                
                        
    def _is_success(self, authresponsejson) :
        return authresponsejson['success']

    def _get_user_sid(self, authresponsejson) :
        return authresponsejson[LINKSTATION_API_REPONSE_DATA_NAME][0]['sid']

    def _get_pagemode(self, authresponsejson) :
        return authresponsejson[LINKSTATION_API_REPONSE_DATA_NAME][0]['pageMode']

    def _create_authentication_cookie(self) :    
        return { 'webui_session_' + self._username : self._sid + '_' + self._language + '_' + str(self._pagemode) }

    async def _get_settings_info(self):
        
        if (self._session == None):
            await self.connect()

        params = { LINKSTATION_API_FUNCTION_PARAM_NAME : LINKSTATION_API_GETSETTINGS_FUNC_NAME}

        async with self._session.get(self._api, params=params, cookies=self._cookies) as settingresp: 
            settingInfo = json.loads(await settingresp.text())

            if (self._is_success(settingInfo)) :
                _LOGGER.debug(await settingresp.text())
                self._settingInfo = settingInfo
                        
    async def get_spaces_info_desc(self):
        return await self._get_settingsinfo_field('r_storage')

    async def get_linkstation_name(self):
        return await self._get_settingsinfo_field('r_hostname')

    async def get_linkstation_ipaddress(self):
        return await self._get_settingsinfo_field('r_ipAddr:1')

    async def get_linkstation_firmware_version(self):
        return await self._get_settingsinfo_field('r_version')

    async def _get_settingsinfo_field(self, fieldname):
        if (self._settingInfo == None):
            await self._get_settings_info()

        for data in self._settingInfo[LINKSTATION_API_REPONSE_DATA_NAME][0]['generalInfo'] :
            if (data['name'] == fieldname) :      
                _LOGGER.debug(fieldname + ': ' + data['value'])                        
                return data['value']
    
    async def restart(self):
        if (self._session == None):
            await self.connect()

        formdata = aiohttp.FormData()
        formdata.add_field(LINKSTATION_API_FUNCTION_PARAM_NAME, LINKSTATION_API_REBOOT_FUNC_NAME)
        formdata.add_field(LINKSTATION_API_ACTION_PARAM_NAME, LINKSTATION_API_REBOOT_ACTION_NAME)

        async with self._session.post(self._api, data=formdata, cookies=self._cookies) as rebootresp:
            rebootInfo = json.loads(await rebootresp.text())
            _LOGGER.debug(await rebootresp.text())
            if (self._is_success(rebootInfo)) :               
                _LOGGER.debug('LinkStation restarting ... ')

    async def get_disks_info(self):
        if (self._session == None):
            await self.connect()

        formdata = aiohttp.FormData()
        formdata.add_field(LINKSTATION_API_FUNCTION_PARAM_NAME, LINKSTATION_API_GETALLDISK_FUNC_NAME)

        async with self._session.post(self._api, data=formdata, cookies=self._cookies) as getdisksresp:
            getdisksinfo = json.loads(await getdisksresp.text())
            _LOGGER.debug(await getdisksresp.text())
            if (self._is_success(getdisksinfo)) :               
                for data in getdisksinfo[LINKSTATION_API_REPONSE_DATA_NAME] :
                    _LOGGER.debug('disk: ' + (data['disk'] or '').strip())
                    _LOGGER.debug('unitName: ' + (data['unitName'] or '').strip())
                    _LOGGER.debug('status: ' + (data['status'] or '').strip())
                    _LOGGER.debug('amountUsed: ' + (data['amountUsed'] or '').strip())
                    _LOGGER.debug('capacity: ' + (data['capacity'] or '').strip())
                    _LOGGER.debug('percentUsed: ' + (data['percentUsed'] or '').strip())
                return getdisksinfo[LINKSTATION_API_REPONSE_DATA_NAME]
    
    async def close(self):
        if (self._session):
            await self._session.close()