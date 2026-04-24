"""NetMixin: check_ip (proxy / IP verification)."""
import os
import time as time_module
from urllib.parse import urlparse
from colorama import Fore, Style

from utils.platform import HAS_REQUESTS

try:
    import requests
except ImportError:
    pass


class NetMixin:
    def check_ip(self):
        """Zeigt die aktuelle IP an — direkt und ueber Proxy"""
        if not HAS_REQUESTS:
            print(f"\n           {Fore.RED}'requests' not installed! → py -m pip install requests{Style.RESET_ALL}")
            time_module.sleep(2)
            return
        
        IP_SERVICES = [
            'https://api.ipify.org',
            'https://icanhazip.com',
            'https://checkip.amazonaws.com',
        ]
        
        def fetch_ip(proxies=None):
            """Versucht IP von mehreren Services abzufragen"""
            for url in IP_SERVICES:
                try:
                    resp = requests.get(url, proxies=proxies, timeout=10)
                    if resp.status_code == 200:
                        return resp.text.strip(), None
                except requests.exceptions.ProxyError:
                    return None, "Proxy Error: Connection failed"
                except requests.exceptions.ConnectTimeout:
                    continue
                except requests.exceptions.ConnectionError:
                    continue
                except Exception:
                    continue
            return None, "All IP services unreachable"
        
        print(f"\n           {Fore.CYAN}═══ IP-Check ═══{Style.RESET_ALL}\n")
        
        # 1) Echte IP (direkt, ohne Proxy)
        print(f"           {Fore.YELLOW}Checking your real IP...{Style.RESET_ALL}", end="", flush=True)
        real_ip, error = fetch_ip(proxies=None)
        if error:
            print(f"\r           {Fore.RED}Real IP: {error}{Style.RESET_ALL}                         ")
        else:
            print(f"\r           {Fore.WHITE}Real IP (no Proxy):  {Fore.CYAN}{real_ip}{Style.RESET_ALL}                         ")
        
        # 2) Proxy IP (falls konfiguriert)
        proxy_url = self.config.get('proxy', '')
        if proxy_url:
            parsed = urlparse(proxy_url)
            proxy_type = parsed.scheme.upper()
            
            print(f"           {Fore.YELLOW}Checking Proxy IP ({proxy_type})...{Style.RESET_ALL}", end="", flush=True)
            
            # requests Proxy-Dict aufbauen
            proxy_dict = {
                'http': proxy_url,
                'https': proxy_url,
            }
            
            proxy_ip, error = fetch_ip(proxies=proxy_dict)
            if error:
                print(f"\r           {Fore.RED}Proxy-IP:               {error}{Style.RESET_ALL}                         ")
                print(f"           {Fore.RED}⚠ Proxy not working! Check URL.{Style.RESET_ALL}")
            else:
                print(f"\r           {Fore.WHITE}Proxy-IP ({proxy_type}):  {Fore.GREEN}{proxy_ip}{Style.RESET_ALL}                         ")
                
                # Vergleich
                if real_ip and proxy_ip:
                    if real_ip != proxy_ip:
                        print(f"\n           {Fore.GREEN}✓ Proxy working! IPs are different.{Style.RESET_ALL}")
                    else:
                        print(f"\n           {Fore.RED}⚠ WARNING: IPs are identical! Proxy is not forwarding correctly.{Style.RESET_ALL}")
        else:
            print(f"\n           {Fore.YELLOW}No proxy configured. Set one under [Y].{Style.RESET_ALL}")
        
        print()
        time_module.sleep(4)
    
    # ═════════════════════════════════════════════════════════════════
    #  CAPTCHA AUTO-SOLVE SYSTEM
    # ═════════════════════════════════════════════════════════════════
    
