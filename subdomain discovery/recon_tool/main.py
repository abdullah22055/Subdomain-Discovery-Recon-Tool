import asyncio
import platform
import argparse
import json
import os
from datetime import datetime
from modules.subdomain_enum import SubdomainEnumerator
from modules.live_checker import LiveChecker
from modules.crawler import WebCrawler
from utils.logger import setup_logger

class ReconTool:
    def __init__(self, target_domain, output_dir="results"):
        self.target_domain = target_domain
        self.output_dir = output_dir
        self.logger = setup_logger("recon_tool")
        self._task = None
        self._is_running = False
        
    def terminate(self):
        "Terminate the current reconnaissance"
        if self._task and not self._task.done():
            self._is_running = False
            self._task.cancel()
            self.logger.info("Terminating reconnaissance...")
            print("\n[!] Terminating reconnaissance...")
            
    async def run(self):
        self._is_running = True
        try:
            self.logger.info(f"Starting reconnaissance for {self.target_domain}")
            subdomain_enum = SubdomainEnumerator(self.target_domain)
            live_checker = LiveChecker(max_concurrent=30, requests_per_second=20)
            crawler = WebCrawler(
                max_concurrent_requests=20,  
                requests_per_second=10,      
                max_depth=2,                 
                timeout=10                   
            )
            if not self._is_running:
                return
            subdomains = await subdomain_enum.enumerate()
            self.logger.info(f"Found {len(subdomains)} subdomains")
            
            if not subdomains:
                print("\n[-] No subdomains found.")
                return
            
            print("\n[+] Found Subdomains:")
            print("=" * 50)
            for subdomain in sorted(subdomains):
                print(f"  → {subdomain}")
            print("=" * 50)
            if not self._is_running:
                return
            live_subdomains = await live_checker.check_alive(subdomains)
            self.logger.info(f"Found {len(live_subdomains)} live subdomains")
            
            if not live_subdomains:
                print("\n[-] No live subdomains found.")
                return
            
            print("\n[+] Live Subdomains:")
            print("=" * 50)
            for subdomain in sorted(live_subdomains):
                print(f"  → {subdomain}")
            print("=" * 50)
                     
            if not self._is_running:
                return
            print("\n[*] Crawling live subdomains for paths and parameters...")
            crawl_results = await crawler.crawl_subdomains(live_subdomains)
            print("[+] Crawling completed")
                        
            if self._is_running:
                self._save_results(subdomains, live_subdomains, crawl_results)
            
        except asyncio.CancelledError:
            self.logger.info("Reconnaissance cancelled")
            print("\n[!] Reconnaissance cancelled")
        except Exception as e:
            self.logger.error(f"Error during reconnaissance: {str(e)}")
            print(f"\n[-] Error during reconnaissance: {str(e)}")
        finally:
            self._is_running = False
            
    def _save_results(self, subdomains, live_subdomains, crawl_results):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        results = {
            "target_domain": self.target_domain,
            "scan_date": timestamp,
            "total_subdomains": len(subdomains),
            "live_subdomains": len(live_subdomains),
            "subdomains": list(subdomains),
            "live_subdomains_list": list(live_subdomains),
            "crawl_results": crawl_results
        }
        
        output_file = os.path.join(self.output_dir, f"scan_{self.target_domain}_{timestamp}.json")
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=4)
        
        print(f"\n[+] Results saved to: {output_file}")
        print("\n[+] Scan Summary:")
        print("=" * 50)
        print(f"Target Domain: {self.target_domain}")
        print(f"Total Subdomains: {len(subdomains)}")
        print(f"Live Subdomains: {len(live_subdomains)}")
        print("\nCrawling Results:")
        for subdomain, data in crawl_results.items():
            print(f"\n{subdomain}:")
            print(f"  Paths found: {len(data['paths'])}")
            print(f"  Parameters found: {len(data['parameters'])}")
        print("=" * 50)

def main():
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    print("""
    
            Subdomain Discovery Tool 
            For Ethical Testing Only 
    
        """)
    
    parser = argparse.ArgumentParser(description="Ethical Reconnaissance Tool")
    parser.add_argument("-d", "--domain", required=True, help="Target domain (e.g., example.com)")
    args = parser.parse_args()
    
    tool = ReconTool(args.domain)
    
    try:
        tool._task = asyncio.run(tool.run())
    except KeyboardInterrupt:
        if tool._is_running:
            tool.terminate()
        print("\n[-] Scan interrupted by user")
    except Exception as e:
        print(f"\n[-] Error: {str(e)}")

if __name__ == "__main__":
    main()


