"""Terminal header: clear_screen + print_header."""
import os
import sys
from colorama import Fore, Style


class HeaderMixin:
    def clear_screen(self):
        """Löscht den Terminal-Bildschirm"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Zeigt den Header mit ASCII-Art"""
        self.clear_screen()
        header = f"""
{Fore.CYAN}
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║    ██████╗ █████╗ ████████╗ ██████╗██╗  ██╗                      ║
║   ██╔════╝██╔══██╗╚══██╔══╝██╔════╝██║  ██║                      ║
║   ██║     ███████║   ██║   ██║     ███████║                      ║
║   ██║     ██╔══██║   ██║   ██║     ██╔══██║                      ║
║   ╚██████╗██║  ██║   ██║   ╚██████╗██║  ██║                      ║
║    ╚═════╝╚═╝  ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝                      ║
║                                                                  ║
║          ██████╗  ██████╗ ████████╗                              ║
║          ██╔══██╗██╔═══██╗╚══██╔══╝                              ║
║          ██████╔╝██║   ██║   ██║                                 ║
║          ██╔══██╗██║   ██║   ██║                                 ║
║          ██████╔╝╚██████╔╝   ██║                                 ║
║          ╚═════╝  ╚═════╝    ╚═╝                                 ║
║                                                                  ║
║                    by MyNameIsKillua                             ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
                                    {Fore.YELLOW}{self.CATCHBOT_VERSION}{Style.RESET_ALL}
"""
        print(header)
        if self.account_name:
            print(f"                    {Fore.CYAN}Account: {Fore.GREEN}{self.account_name.upper()}{Style.RESET_ALL}")
            print(f"                    {Fore.YELLOW}Config: {self.config_path} | Stats: {self.stats_path}{Style.RESET_ALL}")
            print()

