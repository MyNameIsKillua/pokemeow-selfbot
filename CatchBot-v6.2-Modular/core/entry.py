"""Entry point: update banner, arg parsing, launches CatchBot."""
import os
import sys
from colorama import Fore, Style, init as _colorama_init

from utils.platform import CATCHBOT_VERSION, _get_base_dir
from utils.updates import check_for_updates_sync
from core.bot import CatchBot

_colorama_init(autoreset=True)


def main():
    # === WICHTIG: Working Directory auf den Ordner der .exe setzen ===
    # Nuitka onefile entpackt in %TEMP%, Config-Dateien liegen aber neben der .exe.
    base_dir = _get_base_dir()
    if base_dir and os.path.isdir(base_dir):
        os.chdir(base_dir)

    # === UPDATE CHECK (before main menu) ===
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"\n{Fore.CYAN}  ══════════════════════════════════════════════════{Style.RESET_ALL}")
    print(f"{Fore.CYAN}         CatchBot by MyNameIsKillua - {CATCHBOT_VERSION}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  ════════════════════════════════════════════════════{Style.RESET_ALL}\n")
    print(f"  {Fore.YELLOW}Checking for updates...{Style.RESET_ALL}", end="", flush=True)

    has_update, new_ver, download_url = check_for_updates_sync()

    if has_update:
        print(f"\r  {Fore.GREEN}Update available!{Style.RESET_ALL}                    ")
        print(f"\n  {Fore.GREEN}{'='*48}{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}  New version available!{Style.RESET_ALL}")
        print(f"  {Fore.WHITE}  Current : {Fore.RED}{CATCHBOT_VERSION}{Style.RESET_ALL}")
        print(f"  {Fore.WHITE}  Latest  : {Fore.GREEN}{new_ver}{Style.RESET_ALL}")
        print(f"  {Fore.WHITE}  Download: {Fore.CYAN}{download_url}{Style.RESET_ALL}")
        print(f"  {Fore.GREEN}{'='*48}{Style.RESET_ALL}\n")
        input(f"  {Fore.CYAN}Press Enter to continue to main menu...{Style.RESET_ALL}")
    else:
        print(f"\r  {Fore.GREEN}Up to date! ({CATCHBOT_VERSION}){Style.RESET_ALL}                    \n")
        import time
        time.sleep(2)
        input(f"  {Fore.CYAN}Press Enter to continue to main menu...{Style.RESET_ALL}")

    # Multi-Account Support: python catchbot.py --account acc1
    account_name = None
    if '--account' in sys.argv:
        idx = sys.argv.index('--account')
        if idx + 1 < len(sys.argv):
            account_name = sys.argv[idx + 1]

    bot = CatchBot(account_name=account_name)
    bot.run()
