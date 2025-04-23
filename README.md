# Subdomain Discovery Tool
This python-based tool helps security researchers and penetration testers discover and analyze subdomains of a target domain. Just update your config.json with legit api keys and you are good to go.
=======================================================================
Uses:
  - VirusTotal API
  - Shodan API
  - GitHub API
  - DNS bruteforce
- Live subdomain verification
- Web crawling for path and parameter discovery
- Rate limiting to prevent API abuse
- Asynchronous operations for better performance
=======================================================================
For Installation

1.Clone the repository
git clone https://github.com/yourusername/recon_tool.git
cd recon_tool

2.Install required packages
pip install -r requirements.txt

3.Configuration

Create a `config.json` file in the root directory:
{
    "VIRUSTOTAL_API_KEY": "your_virustotal_api_key",
    "SHODAN_API_KEY": "your_shodan_api_key",
    "GITHUB_TOKEN": "your_github_token"
}
========================================================================
Usage

python main.py -d example.com


Arguments
 -d, domain-name: Target domain to scan (required)
=================================================================
Output

Results are saved in the `results` directory in JSON format:
- List of all discovered subdomains
- Live subdomains
- Crawled paths and parameters
- Scan summary and statistics
==================================================================
Project Structure

recon_tool/
├── main.py                 
├── config.json            
└── modules/
    ├── subdomain_enum.py  
    ├── live_checker.py    
    └── crawler.py         
==================================================================
## Disclaimer

This tool is for educational and ethical testing purposes only. Users are responsible for ensuring compliance with applicable laws and regulations.
====================================================================
