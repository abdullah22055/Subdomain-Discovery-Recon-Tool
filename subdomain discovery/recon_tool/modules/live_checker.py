import asyncio
import aiohttp
from typing import List
from aiohttp import ClientTimeout
from asyncio import Semaphore

class LiveChecker:
    def __init__(self, max_concurrent=20, requests_per_second=10):
        self.timeout = ClientTimeout(total=10, connect=5, sock_read=5)
        self.semaphore = Semaphore(max_concurrent)
        self.rate_limit = 1.0 / requests_per_second
        self.last_request_time = 0
    
    async def check_alive(self, subdomains: List[str]) -> List[str]:
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            tasks = [self.check_subdomain(session, subdomain) for subdomain in subdomains]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [subdomain for subdomain, is_alive in zip(subdomains, results) 
                   if isinstance(is_alive, bool) and is_alive]
    
    async def check_subdomain(self, session: aiohttp.ClientSession, subdomain: str) -> bool:
        
        now = asyncio.get_event_loop().time()
        if now - self.last_request_time < self.rate_limit:
            await asyncio.sleep(self.rate_limit - (now - self.last_request_time))
        self.last_request_time = now
        
        async with self.semaphore:
            try:
                async with session.get(f"https://{subdomain}", ssl=False) as response:
                    return response.status < 500
            except:
                try:
                    async with session.get(f"http://{subdomain}") as response:
                        return response.status < 500
                except:
                    return False
