import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import httpx
from fastapi import HTTPException

MAX_BYTES = 5 * 1024 * 1024
MAX_REDIRECTS = 5

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@ Ochrona przed SSRF @@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


# czy adres IP jest publiczny (nie localhost, nie siec prywatna, nie metadane chmury)
def isPublic(ip: str) -> bool:
    addr = ipaddress.ip_address(ip)
    if addr.version == 6 and addr.ipv4_mapped:
        addr = addr.ipv4_mapped
    return addr.is_global and not addr.is_multicast


# sprawdza adres przed pobraniem: tylko http/https i tylko publiczne IP
def checkUrl(url: str) -> None:
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        raise HTTPException(400, "invalid_url")
    try:
        infos = socket.getaddrinfo(p.hostname, p.port or (443 if p.scheme == "https" else 80))
    except socket.gaierror as e:
        raise HTTPException(400, "url_unreachable") from e
    if not infos or not all(isPublic(info[4][0]) for info in infos):
        raise HTTPException(400, "url_blocked")


# pobiera strone; kazde przekierowanie jest sprawdzane od nowa, rozmiar i czas sa ograniczone
async def fetchPage(url: str) -> tuple[str, str]:
    async with httpx.AsyncClient(timeout=10, follow_redirects=False) as client:
        for _ in range(MAX_REDIRECTS + 1):
            checkUrl(url)
            try:
                async with client.stream("GET", url, headers={"User-Agent": "ApocryphaBot/0.1"}) as res:
                    if res.is_redirect:
                        url = urljoin(url, res.headers.get("location", ""))
                        continue
                    if res.status_code >= 400:
                        raise HTTPException(400, "url_unreachable")
                    body = b""
                    async for part in res.aiter_bytes():
                        body += part
                        if len(body) > MAX_BYTES:
                            raise HTTPException(413, "file_too_large")
                    ctype = res.headers.get("content-type", "")
                    return url, body.decode(
                        res.encoding or "utf-8", errors="replace"
                    ) if "html" in ctype or "text" in ctype else ""
            except httpx.HTTPError as e:
                raise HTTPException(400, "url_unreachable") from e
    raise HTTPException(400, "too_many_redirects")
