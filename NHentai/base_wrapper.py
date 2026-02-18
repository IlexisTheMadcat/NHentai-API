from asyncio import get_event_loop
from asyncio import AbstractEventLoop
from json import JSONDecodeError
from urllib.parse import urljoin
from typing import Union

from bs4 import BeautifulSoup
from aiohttp import ClientSession, ContentTypeError
import requests
from seleniumbase import SB

class BaseWrapper:

    _BASE_URL = 'https://nhentai.net/'
    _API_URL = 'https://nhentai.net/api/'
    _IMAGE_BASE_URL = 'https://i1.nhentai.net/galleries/'
    _TINY_IMAGE_BASE_URL = 'https://t1.nhentai.net/galleries/'

    _event_loop = get_event_loop()

    def __init__(self, cache_size: int=100):
        self.cache_size: int = cache_size
    
    @property
    def event_loop(self) -> AbstractEventLoop:
        return self._event_loop
    
    _cookies = {
        "cf_clearance": ""
    }

    def _solve_captcha(self):
        with SB(uc=True, headless=False, test=True, locale_code="en", pls="none") as sb:
            sb.activate_cdp_mode("about:blank")
            sb.cdp.open(self._BASE_URL)
            sb.sleep(5)
            sb.uc_gui_click_captcha()
            sb.sleep(2)

            cf_cookie = next((item for item in sb.cdp.get_all_cookies() if item.name == "cf_clearance"), None)
            if cf_cookie != None:
                print(f"Solved Cloudflare Captcha: {cf_cookie}")
                self._cookies["cf_clearance"] = cf_cookie.value
            else:
                print("No Cloudflare Captcha detected!")

    def _fetch(self, page_path: str, params={}, is_json: bool=False) -> Union[BeautifulSoup, dict]:
        page_path = page_path[1:] if page_path[0] == '/' else page_path
        PAGE_REQUEST = requests.get(urljoin(self._API_URL if is_json else self._BASE_URL, page_path), params=params)
        try:  # Detect the format of the response in case of runtime error
            PAGE_REQUEST.json()
        except ContentTypeError:
            is_json_response = False
        else:
            is_json_response = True

        if PAGE_REQUEST.status_code == 200:
            if is_json:
                return PAGE_REQUEST.json()
            else:
                return BeautifulSoup(PAGE_REQUEST.content, 'html.parser')
        else:
            return PAGE_REQUEST.json() if is_json_response else BeautifulSoup("", 'html.parser')
    
    async def _async_fetch(self, page_path: str, params={}, is_json: bool=False) -> Union[BeautifulSoup, dict]:
        page_path = page_path[1:] if page_path[0] == '/' else page_path
        print(f"Grabbing with Cloudflare cookie: {self._cookies['cf_clearance']}")
        async with ClientSession(cookies=self._cookies) as session:
            async with session.get(urljoin(self._API_URL if is_json else self._BASE_URL, page_path), params=params) as response:
                try:  # Detect the format of the response in case of runtime error
                    await response.json()
                except ContentTypeError:
                    is_json_response = False
                else:
                    is_json_response = True

                if response.status == 200:
                    if is_json:
                        CONTENT = await response.json()
                        return CONTENT
                    else:
                        CONTENT = await response.read()
                        return BeautifulSoup(CONTENT, 'html.parser')
                else:
                    return await response.json() if is_json_response else BeautifulSoup("", 'html.parser')
