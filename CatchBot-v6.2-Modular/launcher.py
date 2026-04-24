"""
CatchBot Multi-Account Launcher
================================
Starts multiple CatchBot instances simultaneously, each with its own config.

Usage:
    python launcher.py

Each account gets its own files:
    config_acc1.json, stats_acc1.json, logs/acc1/
    config_acc2.json, stats_acc2.json, logs/acc2/
    ...

On first launch, a separate config_<name>.json is created for each account,
which you can then configure in the bot menu.
"""

import subprocess
import sys
import os
import json
import time as time_module
from urllib.parse import urlparse
from colorama import Fore, Style, init

init(autoreset=True)


def get_base_dir():
    """Gibt das Verzeichnis zurueck, in dem die .exe / .py Dateien liegen.
    Funktioniert mit PyInstaller, Nuitka (onefile + onedir) und als .py."""
    # Nuitka onefile: __compiled__ ist gesetzt, aber sys.executable zeigt
    # in den Temp-Ordner.  Die echte .exe liegt dort, wo der User sie
    # gestartet hat.  Nuitka setzt NICHT sys.frozen, aber wir koennen
    # __compiled__ (Modul-Level) oder sys.frozen (nur PyInstaller) pruefen.
    #
    # Die zuverlaessigste Methode fuer BEIDE Compiler:
    #   1. Pruefen ob wir als gebundelte .exe laufen
    #   2. Das Verzeichnis per os.path.dirname des ORIGINAL-Pfads ermitteln
    #
    # Nuitka onefile entpackt nach %TEMP% und startet von dort.
    # sys.argv[0] enthaelt aber den ORIGINALEN Pfad der gestarteten .exe!
    if is_compiled():
        # sys.argv[0] ist der Pfad mit dem die .exe aufgerufen wurde
        # (zeigt auf das echte Verzeichnis, nicht den Temp-Ordner)
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        # Entwicklungsmodus: Verzeichnis des Scripts
        return os.path.dirname(os.path.abspath(__file__))


def is_compiled():
    """Prueft ob wir als kompilierte .exe laufen (PyInstaller ODER Nuitka)."""
    # PyInstaller setzt sys.frozen
    if getattr(sys, 'frozen', False):
        return True
    # Nuitka setzt __compiled__ auf Modul-Ebene (wird True wenn kompiliert)
    # Alternativ: Pruefen ob die Dateiendung .exe ist
    if globals().get('__compiled__', False):
        return True
    # Fallback: Pruefen ob sys.executable auf eine .exe zeigt die NICHT python.exe ist
    exe_name = os.path.basename(sys.executable).lower()
    if exe_name.endswith('.exe') and 'python' not in exe_name:
        return True
    return False


def get_bot_cmd(acc_name):
    """Gibt den richtigen Befehl zurueck um catchbot zu starten.
    Erkennt automatisch ob wir als .exe oder .py laufen.
    Kompatibel mit PyInstaller UND Nuitka."""
    if is_compiled():
        # Wir laufen als .exe (PyInstaller oder Nuitka)
        # CatchBot.exe muss im GLEICHEN Ordner liegen wie die Launcher .exe
        base_dir = get_base_dir()
        bot_path = os.path.join(base_dir, 'CatchBot.exe')
        if not os.path.exists(bot_path):
            print(f"    {Fore.RED}ERROR: CatchBot.exe not found in:{Style.RESET_ALL}")
            print(f"    {Fore.RED}  {base_dir}{Style.RESET_ALL}")
            print(f"    {Fore.YELLOW}Make sure CatchBot.exe is in the same folder.{Style.RESET_ALL}")
        return [bot_path, '--account', acc_name]
    else:
        # Wir laufen als .py (Entwicklung)
        return [sys.executable, 'catchbot.py', '--account', acc_name]


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    clear_screen()
    header = f"""
{Fore.CYAN}+=====================================================================+
|                                                                     |
|  ██████╗ █████╗ ████████╗ ██████╗██╗  ██╗██████╗  ██████╗ ████████╗ |
| ██╔════╝██╔══██╗╚══██╔══╝██╔════╝██║  ██║██╔══██╗██╔═══██╗╚══██╔══╝ |
| ██║     ███████║   ██║   ██║     ███████║██████╔╝██║   ██║   ██║    |
| ██║     ██╔══██║   ██║   ██║     ██╔══██║██╔══██╗██║   ██║   ██║    |
| ╚██████╗██║  ██║   ██║   ╚██████╗██║  ██║██████╔╝╚██████╔╝   ██║    |
|  ╚═════╝╚═╝  ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝╚═════╝  ╚═════╝    ╚═╝    |
|                                                                     |
|             Multi-Account Launcher by MyNameIsKillua                |
|                                                                     |
+=====================================================================+{Style.RESET_ALL}
                                              {Fore.YELLOW}v6.2{Style.RESET_ALL}
"""
    print(header)


def load_launcher_config():
    """Laedt die Launcher-Config oder erstellt eine neue"""
    config_path = 'launcher_config.json'
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            data = json.load(f)
        # Backward-Kompatibilitaet: disabled_accounts hinzufuegen falls nicht vorhanden
        if 'disabled_accounts' not in data:
            data['disabled_accounts'] = []
        return data
    return {'accounts': [], 'disabled_accounts': []}


def save_launcher_config(config):
    """Speichert die Launcher-Config"""
    with open('launcher_config.json', 'w') as f:
        json.dump(config, f, indent=4)


def get_account_status(account_name):
    """Prueft ob ein Account konfiguriert ist (Token gesetzt)"""
    config_path = f'config_{account_name}.json'
    if not os.path.exists(config_path):
        return 'Not configured'
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        token = config.get('token', 'Your_Discord_Token_Here')
        channel = config.get('channel_id', 'Your_Channel_ID_Here')
        if token == 'Your_Discord_Token_Here' or not token:
            return 'Token missing'
        if channel == 'Your_Channel_ID_Here' or not channel:
            return 'Channel ID missing'
        return 'Ready'
    except Exception:
        return 'Config error'


def show_accounts(config):
    """Zeigt alle konfigurierten Accounts an"""
    print(f"\n    {Fore.YELLOW}{'=' * 58}{Style.RESET_ALL}")
    print(f"    {Fore.CYAN}Configured Accounts:{Style.RESET_ALL}\n")

    if not config['accounts']:
        print(f"    {Fore.YELLOW}No accounts configured.{Style.RESET_ALL}")
        print(f"    {Fore.YELLOW}Add accounts first with [A].{Style.RESET_ALL}")
    else:
        disabled = config.get('disabled_accounts', [])
        for i, acc in enumerate(config['accounts'], 1):
            is_disabled = acc in disabled
            if is_disabled:
                status_color = Fore.LIGHTBLACK_EX
                status_icon = 'x'
                status = 'Disabled'
                print(f"    {status_color}  [{status_icon}] {i}. {acc.upper()}"
                      f"  -  {status}"
                      f"  -  config_{acc}.json{Style.RESET_ALL}")
            else:
                status = get_account_status(acc)
                if status == 'Ready':
                    status_color = Fore.GREEN
                    status_icon = '+'
                elif status == 'Token missing' or status == 'Channel ID missing':
                    status_color = Fore.YELLOW
                    status_icon = '!'
                else:
                    status_color = Fore.RED
                    status_icon = '-'
                
                # Proxy-Info auslesen
                proxy_info = ''
                try:
                    cfg_path = f'config_{acc}.json'
                    if os.path.exists(cfg_path):
                        with open(cfg_path, 'r') as f:
                            acc_cfg = json.load(f)
                        p_url = acc_cfg.get('proxy', '')
                        if p_url:
                            p = urlparse(p_url)
                            p_type = 'SOCKS5' if p.scheme.startswith('socks') else 'HTTP'
                            proxy_info = f"  {Fore.CYAN}[{p_type}: {p.hostname}:{p.port}]{Style.RESET_ALL}"
                        else:
                            proxy_info = f"  {Fore.YELLOW}[No Proxy]{Style.RESET_ALL}"
                except Exception:
                    pass
                
                print(f"    {status_color}  [{status_icon}] {i}. {acc.upper()}{Style.RESET_ALL}"
                      f"  -  {status_color}{status}{Style.RESET_ALL}"
                      f"  -  config_{acc}.json{proxy_info}")

    print(f"\n    {Fore.YELLOW}{'=' * 58}{Style.RESET_ALL}")


def main():
    # === WICHTIG: Working Directory auf den Ordner der .exe setzen ===
    # Nuitka onefile entpackt in %TEMP%, aber Config-Dateien liegen neben der .exe.
    # Daher muessen wir sicherstellen, dass das Working Directory korrekt ist.
    base_dir = get_base_dir()
    if base_dir and os.path.isdir(base_dir):
        os.chdir(base_dir)
        if is_compiled():
            print(f"    {Fore.CYAN}Working directory: {base_dir}{Style.RESET_ALL}")

    config = load_launcher_config()
    processes = {}  # account_name -> subprocess.Popen

    while True:
        print_header()
        show_accounts(config)

        print(f"""
    {Fore.GREEN}[S]{Style.RESET_ALL} Start All Accounts
    {Fore.GREEN}[1-9]{Style.RESET_ALL} Start/Configure Single Account
    {Fore.CYAN}[A]{Style.RESET_ALL} Add Account
    {Fore.CYAN}[D]{Style.RESET_ALL} Disable / Enable Account
    {Fore.CYAN}[R]{Style.RESET_ALL} Remove Account
    {Fore.CYAN}[K]{Style.RESET_ALL} Configure Account (Open Config Menu)
    {Fore.CYAN}[P]{Style.RESET_ALL} Show Running Processes
    {Fore.RED}[Q]{Style.RESET_ALL} Exit
""")

        choice = input(f"    {Fore.CYAN}Choose an option: {Style.RESET_ALL}").strip()

        # ─── Account hinzufuegen ───
        if choice.lower() == 'a':
            print(f"\n    {Fore.CYAN}Enter account name (e.g. main, alt1, alt2):{Style.RESET_ALL}")
            print(f"    {Fore.YELLOW}Only letters, numbers and underscores allowed.{Style.RESET_ALL}")
            name = input(f"    {Fore.CYAN}Name: {Style.RESET_ALL}").strip().lower()

            if not name:
                print(f"    {Fore.RED}No name entered!{Style.RESET_ALL}")
                time_module.sleep(1)
                continue

            # Validierung: nur alphanumerisch + underscore
            if not all(c.isalnum() or c == '_' for c in name):
                print(f"    {Fore.RED}Invalid name! Only letters, numbers and _ allowed.{Style.RESET_ALL}")
                time_module.sleep(2)
                continue

            if name in config['accounts']:
                print(f"    {Fore.RED}Account '{name}' already exists!{Style.RESET_ALL}")
                time_module.sleep(1)
                continue

            config['accounts'].append(name)
            save_launcher_config(config)

            print(f"    {Fore.GREEN}Account '{name}' added!{Style.RESET_ALL}")
            print(f"    {Fore.YELLOW}Config file: config_{name}.json{Style.RESET_ALL}")
            print(f"    {Fore.YELLOW}Open the config menu with [K] to set Token & Channel.{Style.RESET_ALL}")
            time_module.sleep(3)

        # ─── Account deaktivieren / aktivieren ───
        elif choice.lower() == 'd':
            if not config['accounts']:
                print(f"    {Fore.RED}No accounts available!{Style.RESET_ALL}")
                time_module.sleep(1)
                continue

            disabled = config.get('disabled_accounts', [])
            print(f"\n    {Fore.CYAN}Disable / Enable Account:{Style.RESET_ALL}")
            for i, acc in enumerate(config['accounts'], 1):
                is_disabled = acc in disabled
                if is_disabled:
                    print(f"    {Fore.LIGHTBLACK_EX}  [{i}] {acc.upper()}  -  DISABLED{Style.RESET_ALL}")
                else:
                    print(f"    {Fore.GREEN}  [{i}] {acc.upper()}  -  ACTIVE{Style.RESET_ALL}")

            print(f"\n    {Fore.YELLOW}Choose an account to toggle (active <-> disabled){Style.RESET_ALL}")
            idx = input(f"    {Fore.CYAN}Number: {Style.RESET_ALL}").strip()
            try:
                idx = int(idx) - 1
                if 0 <= idx < len(config['accounts']):
                    acc_name = config['accounts'][idx]
                    if acc_name in disabled:
                        disabled.remove(acc_name)
                        config['disabled_accounts'] = disabled
                        save_launcher_config(config)
                        print(f"    {Fore.GREEN}Account '{acc_name.upper()}' has been ENABLED!{Style.RESET_ALL}")
                        print(f"    {Fore.GREEN}Will be included again when using [S] Start All.{Style.RESET_ALL}")
                    else:
                        disabled.append(acc_name)
                        config['disabled_accounts'] = disabled
                        save_launcher_config(config)
                        print(f"    {Fore.YELLOW}Account '{acc_name.upper()}' has been DISABLED!{Style.RESET_ALL}")
                        print(f"    {Fore.YELLOW}Will be skipped when using [S] Start All.{Style.RESET_ALL}")
                    time_module.sleep(2)
                else:
                    print(f"    {Fore.RED}Invalid number!{Style.RESET_ALL}")
                    time_module.sleep(1)
            except ValueError:
                print(f"    {Fore.RED}Invalid input!{Style.RESET_ALL}")
                time_module.sleep(1)

        # ─── Account entfernen ───
        elif choice.lower() == 'r':
            if not config['accounts']:
                print(f"    {Fore.RED}No accounts to remove!{Style.RESET_ALL}")
                time_module.sleep(1)
                continue

            print(f"\n    {Fore.CYAN}Which account to remove?{Style.RESET_ALL}")
            for i, acc in enumerate(config['accounts'], 1):
                print(f"    [{i}] {acc}")
            idx = input(f"    {Fore.CYAN}Number: {Style.RESET_ALL}").strip()
            try:
                idx = int(idx) - 1
                if 0 <= idx < len(config['accounts']):
                    removed = config['accounts'].pop(idx)
                    # Auch aus disabled_accounts entfernen falls vorhanden
                    if removed in config.get('disabled_accounts', []):
                        config['disabled_accounts'].remove(removed)
                    save_launcher_config(config)
                    print(f"    {Fore.GREEN}Account '{removed}' removed!{Style.RESET_ALL}")
                    print(f"    {Fore.YELLOW}Config files (config_{removed}.json etc.) were NOT deleted.{Style.RESET_ALL}")
                    time_module.sleep(2)
                else:
                    print(f"    {Fore.RED}Invalid number!{Style.RESET_ALL}")
                    time_module.sleep(1)
            except ValueError:
                print(f"    {Fore.RED}Invalid input!{Style.RESET_ALL}")
                time_module.sleep(1)

        # ─── Account konfigurieren ───
        elif choice.lower() == 'k':
            if not config['accounts']:
                print(f"    {Fore.RED}No accounts available!{Style.RESET_ALL}")
                time_module.sleep(1)
                continue

            print(f"\n    {Fore.CYAN}Which account to configure?{Style.RESET_ALL}")
            for i, acc in enumerate(config['accounts'], 1):
                status = get_account_status(acc)
                print(f"    [{i}] {acc} ({status})")
            idx = input(f"    {Fore.CYAN}Number: {Style.RESET_ALL}").strip()
            try:
                idx = int(idx) - 1
                if 0 <= idx < len(config['accounts']):
                    acc_name = config['accounts'][idx]
                    print(f"\n    {Fore.GREEN}Opening config menu for '{acc_name}'...{Style.RESET_ALL}")
                    time_module.sleep(1)

                    # Starte den Bot im normalen Modus (mit Menue)
                    proc = subprocess.run(get_bot_cmd(acc_name))
                else:
                    print(f"    {Fore.RED}Invalid number!{Style.RESET_ALL}")
                    time_module.sleep(1)
            except ValueError:
                print(f"    {Fore.RED}Invalid input!{Style.RESET_ALL}")
                time_module.sleep(1)

        # ─── Alle starten ───
        elif choice.lower() == 's':
            disabled = config.get('disabled_accounts', [])
            ready_accounts = [
                acc for acc in config['accounts']
                if get_account_status(acc) == 'Ready' and acc not in disabled
            ]

            if not ready_accounts:
                print(f"    {Fore.RED}No accounts ready to start!{Style.RESET_ALL}")
                print(f"    {Fore.YELLOW}Configure Token & Channel ID first with [K].{Style.RESET_ALL}")
                time_module.sleep(2)
                continue

            disabled_accounts = [
                acc for acc in config['accounts']
                if acc in disabled
            ]
            not_ready = [
                acc for acc in config['accounts']
                if acc not in ready_accounts and acc not in disabled
            ]

            print(f"\n    {Fore.GREEN}Starting {len(ready_accounts)} account(s):{Style.RESET_ALL}")
            for acc in ready_accounts:
                print(f"    {Fore.GREEN}  + {acc.upper()}{Style.RESET_ALL}")
            if disabled_accounts:
                print(f"    {Fore.LIGHTBLACK_EX}Disabled (skipped):{Style.RESET_ALL}")
                for acc in disabled_accounts:
                    print(f"    {Fore.LIGHTBLACK_EX}  x {acc.upper()}{Style.RESET_ALL}")
            if not_ready:
                print(f"    {Fore.YELLOW}Not ready (skipped):{Style.RESET_ALL}")
                for acc in not_ready:
                    print(f"    {Fore.YELLOW}  - {acc.upper()} ({get_account_status(acc)}){Style.RESET_ALL}")

            confirm = input(f"\n    {Fore.CYAN}Start? (y/n): {Style.RESET_ALL}").strip().lower()
            if confirm != 'y':
                continue

            # Starte jeden Account als separaten Prozess
            for acc in ready_accounts:
                if acc in processes and processes[acc].poll() is None:
                    print(f"    {Fore.YELLOW}{acc.upper()} is already running!{Style.RESET_ALL}")
                    continue

                print(f"    {Fore.GREEN}Starting {acc.upper()}...{Style.RESET_ALL}", end="", flush=True)

                if os.name == 'nt':
                    # Windows: Neues Fenster fuer jeden Account
                    proc = subprocess.Popen(
                        get_bot_cmd(acc),
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
                else:
                    # Linux/Mac: Im Hintergrund starten
                    log_file = open(f'launcher_{acc}.log', 'w')
                    proc = subprocess.Popen(
                        get_bot_cmd(acc),
                        stdout=log_file,
                        stderr=log_file
                    )

                processes[acc] = proc
                print(f" PID: {proc.pid}")
                time_module.sleep(1)

            print(f"\n    {Fore.GREEN}All accounts started!{Style.RESET_ALL}")
            if os.name == 'nt':
                print(f"    {Fore.YELLOW}Each account has its own window.{Style.RESET_ALL}")
            else:
                print(f"    {Fore.YELLOW}Logs: launcher_<account>.log{Style.RESET_ALL}")
            print(f"    {Fore.YELLOW}Press [P] to see running processes.{Style.RESET_ALL}")
            input(f"\n    {Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        # ─── Einzelnen Account starten ───
        elif choice.isdigit() and 1 <= int(choice) <= len(config['accounts']):
            idx = int(choice) - 1
            acc_name = config['accounts'][idx]
            status = get_account_status(acc_name)

            if status != 'Ready':
                print(f"    {Fore.RED}Account '{acc_name}' is not ready: {status}{Style.RESET_ALL}")
                print(f"    {Fore.YELLOW}Configure Token & Channel first with [K].{Style.RESET_ALL}")
                time_module.sleep(2)
                continue

            print(f"\n    {Fore.CYAN}What do you want to do with '{acc_name.upper()}'?{Style.RESET_ALL}")
            print(f"    [1] Start (new window)")
            print(f"    [2] Configure")
            sub = input(f"    {Fore.CYAN}Choose: {Style.RESET_ALL}").strip()

            if sub == '1':
                if acc_name in processes and processes[acc_name].poll() is None:
                    print(f"    {Fore.YELLOW}{acc_name.upper()} is already running! (PID: {processes[acc_name].pid}){Style.RESET_ALL}")
                    time_module.sleep(2)
                    continue

                if os.name == 'nt':
                    proc = subprocess.Popen(
                        get_bot_cmd(acc_name),
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
                else:
                    proc = subprocess.Popen(
                        get_bot_cmd(acc_name),
                    )
                processes[acc_name] = proc
                print(f"    {Fore.GREEN}{acc_name.upper()} started! PID: {proc.pid}{Style.RESET_ALL}")
                time_module.sleep(2)

            elif sub == '2':
                subprocess.run(get_bot_cmd(acc_name))

        # ─── Laufende Prozesse ───
        elif choice.lower() == 'p':
            print(f"\n    {Fore.CYAN}Running Bot Processes:{Style.RESET_ALL}")
            print(f"    {'=' * 50}")

            any_running = False
            for acc, proc in list(processes.items()):
                if proc.poll() is None:
                    any_running = True
                    print(f"    {Fore.GREEN}  [ACTIVE]  {acc.upper()} (PID: {proc.pid}){Style.RESET_ALL}")
                else:
                    exit_code = proc.returncode
                    print(f"    {Fore.RED}  [STOPPED] {acc.upper()} (Exit Code: {exit_code}){Style.RESET_ALL}")

            if not processes:
                print(f"    {Fore.YELLOW}  No processes started.{Style.RESET_ALL}")
            elif not any_running:
                print(f"\n    {Fore.YELLOW}  All processes have ended.{Style.RESET_ALL}")

            print(f"    {'=' * 50}")

            if any_running:
                print(f"\n    {Fore.RED}[X] Terminate All Processes{Style.RESET_ALL}")
                sub = input(f"    {Fore.CYAN}(Enter = back, X = terminate): {Style.RESET_ALL}").strip()
                if sub.lower() == 'x':
                    print(f"    {Fore.RED}Terminating all processes...{Style.RESET_ALL}")
                    for acc, proc in processes.items():
                        if proc.poll() is None:
                            proc.terminate()
                            print(f"    {Fore.YELLOW}  {acc.upper()} terminated.{Style.RESET_ALL}")
                    time_module.sleep(2)
            else:
                input(f"\n    {Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        # ─── Beenden ───
        elif choice.lower() == 'q':
            # Pruefen ob noch Prozesse laufen
            running = [
                acc for acc, proc in processes.items()
                if proc.poll() is None
            ]
            if running:
                print(f"\n    {Fore.YELLOW}Still {len(running)} account(s) active:{Style.RESET_ALL}")
                for acc in running:
                    print(f"    {Fore.YELLOW}  - {acc.upper()}{Style.RESET_ALL}")
                confirm = input(f"    {Fore.RED}Terminate all and close launcher? (y/n): {Style.RESET_ALL}").strip()
                if confirm.lower() != 'y':
                    continue
                for acc, proc in processes.items():
                    if proc.poll() is None:
                        proc.terminate()

            print(f"\n    {Fore.YELLOW}Goodbye!{Style.RESET_ALL}")
            break


if __name__ == "__main__":
    main()