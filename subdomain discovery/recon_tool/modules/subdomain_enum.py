import asyncio
import aiohttp
import json
import os
from typing import List, Set
from urllib.parse import quote
import socket

class SubdomainEnumerator:
    def __init__(self, domain: str):
        self.domain = domain
        self.subdomains: Set[str] = set()
        self.api_keys = self._load_api_keys()
        self.rate_limits = {
            'virustotal': 4,  
            'shodan': 1,      
            'github': 30      
        }
        self.last_request_times = {
            'virustotal': 0,
            'shodan': 0,
            'github': 0
        }
        
    def _load_api_keys(self) -> dict:
        """Load API keys from config file or environment variables"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
            with open(config_path) as f:
                config = json.load(f)
                return {
                    'virustotal': config.get('VIRUSTOTAL_API_KEY', ''),
                    'shodan': config.get('SHODAN_API_KEY', ''),
                    'github': config.get('GITHUB_TOKEN', '')
                }
        except:
            return {
                'virustotal': os.getenv('VIRUSTOTAL_API_KEY', ''),
                'shodan': os.getenv('SHODAN_API_KEY', ''),
                'github': os.getenv('GITHUB_TOKEN', '')
            }

    async def enumerate(self) -> List[str]:
        tasks = [
            self.search_crtsh(),
            self.search_virustotal(),
            self.search_shodan(),
            self.search_github(),
            self.bruteforce_dns()
        ]
        
        print("[*] Starting subdomain enumeration from multiple sources...")
        await asyncio.gather(*tasks)
        return list(self.subdomains)

    async def search_crtsh(self):
        """Search Certificate Transparency logs"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://crt.sh/?q=%.{self.domain}&output=json"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        for entry in data:
                            subdomain = entry['name_value'].lower()
                            if subdomain.endswith(self.domain):
                                self.subdomains.add(subdomain)
                        print(f"[+] Found {len(self.subdomains)} subdomains from crt.sh")
        except Exception as e:
            print(f"[-] Error searching crt.sh: {str(e)}")

    async def _respect_rate_limit(self, service):
        now = asyncio.get_event_loop().time()
        wait_time = (1.0 / self.rate_limits[service]) - (now - self.last_request_times[service])
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        self.last_request_times[service] = now

    async def search_virustotal(self):
        """Search VirusTotal for subdomains"""
        if not self.api_keys['virustotal']:
            print("[-] VirusTotal API key not found. Skipping...")
            return
            
        try:
            await self._respect_rate_limit('virustotal')
            headers = {'x-apikey': self.api_keys['virustotal']}
            timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
            async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
                url = f"https://www.virustotal.com/api/v3/domains/{self.domain}/subdomains"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        for item in data.get('data', []):
                            self.subdomains.add(item['id'])
                        print(f"[+] Found subdomains from VirusTotal")
        except Exception as e:
            print(f"[-] Error searching VirusTotal: {str(e)}")

    async def search_shodan(self):
        """Search Shodan for subdomains"""
        if not self.api_keys['shodan']:
            print("[-] Shodan API key not found. Skipping...")
            return
            
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.shodan.io/dns/domain/{self.domain}?key={self.api_keys['shodan']}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        for subdomain in data.get('subdomains', []):
                            self.subdomains.add(f"{subdomain}.{self.domain}")
                        print(f"[+] Found subdomains from Shodan")
        except Exception as e:
            print(f"[-] Error searching Shodan: {str(e)}")

    async def search_github(self):
        """Search GitHub for subdomains"""
        if not self.api_keys['github']:
            print("[-] GitHub token not found. Skipping...")
            return
            
        try:
            headers = {
                'Authorization': f"token {self.api_keys['github']}",
                'Accept': 'application/vnd.github.v3+json'
            }
            async with aiohttp.ClientSession(headers=headers) as session:
                query = quote(f"'{self.domain}' in:file")
                url = f"https://api.github.com/search/code?q={query}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"[+] Found potential subdomains from GitHub")
        except Exception as e:
            print(f"[-] Error searching GitHub: {str(e)}")

    async def bruteforce_dns(self):
        """Simple DNS bruteforce using common subdomain wordlist"""
        wordlist = ['www', 'mail', 'ftp', 'admin', 'blog', 'dev', 'test', 'staging', 
                   'api', 'portal', 'vpn', 'cdn', 'shop', 'store', 'app']
        
        for word in wordlist:
            try:
                subdomain = f"{word}.{self.domain}"
                try:
                    addr = socket.gethostbyname(subdomain)
                    if addr:
                        self.subdomains.add(subdomain)
                        print(f"[+] Found subdomain: {subdomain}")
                except socket.gaierror:
                    continue
            except Exception:
                continue
        
        print(f"[+] Completed DNS bruteforce")
