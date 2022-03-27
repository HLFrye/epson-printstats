from dataclasses import dataclass
import asyncio
import argparse

import aiohttp
from lxml.etree import fromstring, HTMLParser
from lxml.cssselect import CSSSelector


@dataclass
class Ink:
    name: str
    pct: float


def get_children(el, selector):
    sel = CSSSelector(selector)
    return sel(el)


async def get_ink(ip):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://{ip}/PRESENTATION/ADVANCED/INFO_PRTINFO/TOP", ssl=False
        ) as resp:
            result = await resp.text()
            parser = HTMLParser()
            h = fromstring(result, parser)
            sel = CSSSelector("body > div > div.section > div > ul > li ")
            for li in sel(h):
                name = None
                val = None
                max_height = 50.0

                for el in get_children(li, "div.tank > img.color"):
                    val = el.get("height")
                for el in get_children(li, "div.clrname"):
                    name = el.text

                if name is not None:
                    yield Ink(name, float(val) / max_height)


def get_value(el, sel):
    sel = CSSSelector(sel)
    for el in sel(el):
        return el.text


@dataclass
class MaintenanceInfo:
    total: int
    color: int
    bandw: int


async def get_paper(ip):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://{ip}/PRESENTATION/ADVANCED/INFO_MENTINFO/TOP", ssl=False
        ) as resp:
            result = await resp.text()
            parser = HTMLParser()
            h = fromstring(result, parser)

            total = int(
                get_value(
                    h,
                    "body > div > div.section > fieldset:nth-child(2) > dl > dd:nth-child(2) > div",
                )
            )
            color = int(
                get_value(
                    h,
                    "body > div > div.section > fieldset:nth-child(2) > dl > dd:nth-child(4) > div",
                )
            )
            bandw = int(
                get_value(
                    h,
                    "body > div > div.section > fieldset:nth-child(2) > dl > dd:nth-child(6) > div",
                )
            )

            return MaintenanceInfo(total, color, bandw)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ip")
    args = parser.parse_args()

    ip = args.ip
    async for ink in get_ink(ip):
        print(f"epson_printer_ink_left_percent{{ip={ip},color={ink.name}}} {ink.pct}")

    maint_info = await get_paper(ip)
    print(f"epson_printer_maint_total_pages{{ip={ip}}} {maint_info.total}")
    print(f"epson_printer_maint_color_pages{{ip={ip}}} {maint_info.color}")
    print(f"epson_printer_maint_bandw_pages{{ip={ip}}} {maint_info.bandw}")


if __name__ == "__main__":
    asyncio.run(main())
