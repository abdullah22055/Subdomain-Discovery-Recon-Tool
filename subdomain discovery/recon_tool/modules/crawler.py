import asyncio
import aiohttp
from typing import List, Dict
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from aiohttp import ClientTimeout
from asyncio import Semaphore

class WebCrawler:
    def __init__(self, max_concurrent_requests=10, requests_per_second=2, max_depth=2, timeout=10):
        self.visited_urls = set()
        self.parameters = set()
        self.timeout = ClientTimeout(total=timeout, connect=5, sock_read=5)
        self.semaphore = Semaphore(max_concurrent_requests)
        self.rate_limit = 1.0 / requests_per_second
        self.last_request_time = 0
        self.max_depth = max_depth  
        
    def is_valid_url(self, url: str, domain: str) -> bool:
        "Check if URL is valid and belongs to target domain"
        try:
            if not url.startswith(("http://", "https://")):
                return False
                
            parsed = urlparse(url)
            if not parsed.netloc or domain not in parsed.netloc:
                return False
                
           
            if parsed.scheme not in ('http', 'https'):
                return False
                
           
            skip_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.doc', 
                             '.docx', '.xls', '.xlsx', '.zip', '.tar', '.gz'}
            if any(url.lower().endswith(ext) for ext in skip_extensions):
                return False
                
            return True
        except:
            return False
    
    async def crawl_subdomains(self, subdomains: List[str]) -> Dict:
        results = {}
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            tasks = [self.crawl_site(session, subdomain) for subdomain in subdomains]
            completed = await asyncio.gather(*tasks, return_exceptions=True)
            
            for subdomain, result in zip(subdomains, completed):
                if isinstance(result, Exception):
                    results[subdomain] = {"paths": [], "parameters": []}
                else:
                    paths, params = result
                    results[subdomain] = {
                        "paths": list(paths),
                        "parameters": list(params)
                    }
        return results
    
    async def crawl_site(self, session: aiohttp.ClientSession, domain: str):
        paths = set()
        parameters = set()
        
        async def crawl_url(url, depth=0):
            if depth >= self.max_depth:
                return
                
            if url in self.visited_urls:
                return
            
            if not self.is_valid_url(url, domain):
                return
                
            self.visited_urls.add(url)
            
            now = asyncio.get_event_loop().time()
            if now - self.last_request_time < self.rate_limit:
                await asyncio.sleep(self.rate_limit - (now - self.last_request_time))
            self.last_request_time = now
            
            async with self.semaphore:
                try:
                    async with session.get(url, ssl=False, allow_redirects=True) as response:
                        if response.status != 200:
                            return
                        
                        content_type = response.headers.get('content-type', '').lower()
                        if not content_type.startswith('text/html'):
                            return
                            
                        text = await response.text()
                        soup = BeautifulSoup(text, 'html.parser')
                        
                        parsed_url = urlparse(url)
                        paths.add(parsed_url.path)
                        
                        
                        if parsed_url.query:
                            for param in parsed_url.query.split('&'):
                                if '=' in param:
                                    parameters.add(param.split('=')[0])
                        
                        
                        for form in soup.find_all('form'):
                            for input_tag in form.find_all(['input', 'select', 'textarea']):
                                name = input_tag.get('name')
                                if name:
                                    parameters.add(name)
                        
                        
                        if depth < self.max_depth - 1:
                            tasks = []
                        
                            for link in soup.find_all('a', href=True)[:20]:
                                href = link.get('href')
                                if href:
                                    full_url = urljoin(url, href)
                                    if full_url not in self.visited_urls and self.is_valid_url(full_url, domain):
                                        tasks.append(crawl_url(full_url, depth + 1))
                            
                            if tasks:
                                await asyncio.gather(*tasks)
                                
                except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                    print(f"Error crawling {url}: {str(e)}")
                except Exception as e:
                    pass
        
        
        for protocol in ['https://', 'http://']:
            try:
                await crawl_url(f"{protocol}{domain}")
            except Exception:
                continue
                
        return paths, parameters


