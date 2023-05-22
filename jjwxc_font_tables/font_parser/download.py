import asyncio
import hashlib
import io
import tempfile
from typing import Union

import h2.exceptions
import httpx
from fontTools.ttLib import woff2, ttFont


async def request_font(font_name: str, retry: int = 5) \
        -> Union[tuple[bytes, str], tuple[None, str]]:
    url = 'https://static.jjwxc.net/tmp/fonts/{}.woff2?h=my.jjwxc.net'.format(font_name)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5666.197 Safari/537.36",
        "Accept": "application/font-woff2;q=1.0,application/font-woff;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.5",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "Referer": "https://my.jjwxc.net/",
        "Origin": "https://my.jjwxc.net"
    }

    client = httpx.AsyncClient(headers=headers, http2=True)
    while retry > 0:
        try:
            resp = await client.get(url, headers=headers, timeout=5, follow_redirects=True)

            if 200 <= resp.status_code < 300:
                await client.aclose()
                return resp.content, 'OK'

            if resp.status_code == 404:
                await client.aclose()
                return None, '404'

            retry = retry - 1

        except (httpx.TransportError, h2.exceptions.ProtocolError):
            await asyncio.sleep(5)
            retry = retry - 1

    await client.aclose()
    return None, 'ERROR'


def woff2_to_ttf(input_bytest: bytes):
    """将 woff2 bytes 转捣为 TTFont 对象"""
    with io.BytesIO(input_bytest) as input_file:
        with tempfile.TemporaryFile() as tmp:
            woff2.decompress(input_file, tmp)
            tmp.seek(0)
            ttf = ttFont.TTFont(tmp)
            return ttf


async def get_font(font_name: str) -> dict[str, Union[str, bytes, ttFont.TTFont]]:
    font_bytes, status = await request_font(font_name)

    if status == 'OK':
        m = hashlib.sha1()
        m.update(font_bytes)
        hashsum = m.hexdigest()

        return {
            "name": font_name,
            "bytes": font_bytes,
            "ttf": woff2_to_ttf(font_bytes),
            "hashsum": hashsum,
            "status": status
        }
    else:
        return {"status": status}
