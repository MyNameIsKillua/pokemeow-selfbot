"""PokemonNamesMixin: Pokemon name loading, Discord text cleaning, name matching."""
import os
import re
from colorama import Fore, Style


class PokemonNamesMixin:
    def load_pokemon_names(self):
        """Laedt alle Pokemon-Namen aus Pokemon_Names.txt"""
        names = set()
        
        # Suche die Datei im gleichen Verzeichnis wie das Script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths = [
            os.path.join(script_dir, 'Pokemon_Names.txt'),
            'Pokemon_Names.txt',
            os.path.join(script_dir, 'pokemon_names.txt'),
            'pokemon_names.txt',
        ]
        
        file_path = None
        for p in possible_paths:
            if os.path.exists(p):
                file_path = p
                break
        
        if not file_path:
            print(f"{Fore.RED}⚠️ Pokemon_Names.txt not found! Name detection disabled.{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}   Place the file in the same folder as catchbot.py.{Style.RESET_ALL}")
            return names
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    name = line.strip()
                    # Ueberspringe leere Zeilen und Header ("Name")
                    if name and name.lower() != 'name':
                        names.add(name)
            
            print(f"{Fore.GREEN}✅ {len(names)} Pokemon names loaded from {file_path}!{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}⚠️ Error loading Pokemon_Names.txt: {str(e)}{Style.RESET_ALL}")
        
        return names
    
    def clean_discord_text(self, text):
        """
        Bereinigt Discord-Text von Markdown, Emojis und Sonderzeichen.
        So wird z.B. '**Klefki**' zu 'Klefki' und '<:194:722265188627382312>' entfernt.
        """
        cleaned = text
        # 1. Discord Custom Emojis entfernen: <:name:id> und <a:name:id>
        cleaned = re.sub(r'<a?:\w+:\d+>', ' ', cleaned)
        # 2. Discord Markdown entfernen: **bold**, *italic*, __underline__, ~~strike~~, ||spoiler||
        cleaned = re.sub(r'\*\*([^*]+)\*\*', r' \1 ', cleaned)  # **bold** -> bold
        cleaned = re.sub(r'\*([^*]+)\*', r' \1 ', cleaned)       # *italic* -> italic
        cleaned = re.sub(r'__([^_]+)__', r' \1 ', cleaned)       # __underline__ -> underline
        cleaned = re.sub(r'~~([^~]+)~~', r' \1 ', cleaned)       # ~~strike~~ -> strike
        cleaned = re.sub(r'\|\|([^|]+)\|\|', r' \1 ', cleaned)   # ||spoiler|| -> spoiler
        # 3. Uebrige Markdown-Zeichen entfernen
        cleaned = cleaned.replace('*', ' ').replace('_', ' ').replace('~', ' ').replace('|', ' ')
        # 4. Mehrfache Leerzeichen zusammenfassen
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned
    
    def find_pokemon_name_in_text(self, text):
        """
        Durchsucht den Text nach einem bekannten Pokemon-Namen aus der Pokemon_Names.txt.
        Gibt den gefundenen Namen zurueck oder None wenn keiner gefunden wurde.
        
        Zuerst wird der Text von Discord-Markdown und Emojis bereinigt,
        dann wird nach Pokemon-Namen gesucht (laengste zuerst, damit z.B. 
        "Mr. Mime" vor "Mime" und "Mewtwo" vor "Mew" gefunden wird).
        
        If no match in the name list, tries to extract special forms directly from
        patterns like "You caught an **Iron-Leaves**" or "You caught a **Arceus-Fairy**"
        """
        # Text bereinigen (Markdown, Emojis, etc. entfernen)
        cleaned = self.clean_discord_text(text)
        cleaned_lower = cleaned.lower()
        
        # === PRIORITY 1: Try to extract name directly from known patterns ===
        # This catches special forms like "Iron-Leaves", "Arceus-Fairy", "Necrozma-Ultra"
        # Works for BOTH catch results ("You caught") AND spawn text ("found a wild")
        direct_patterns = [
            # --- Spawn patterns: "found/fished a wild **Iron-Leaves**!" ---
            r'(?:found|fished) a wild\s+(?:[^\*]*?\s*)?\*\*([A-Za-z][\w\s\-\'\.]+?)\*\*',
            r'(?:found|fished) a wild\s+(?:<[^>]+>\s*)*([A-Za-z][\w\-]+(?:-[A-Za-z\-]+)?)\s*!',
            # --- Catch result patterns: "You caught a/an **Iron-Leaves** with" ---
            r'[Yy]ou caught an?\s+(?:[^\*]*?\s+)?\*\*([A-Za-z][\w\s\-\'\.]+?)\*\*',
            r'[Yy]ou caught an?\s+(?:<[^>]+>\s*)*([A-Za-z][\w\-]+(?:-[A-Za-z\-]+)?)\s+with',
            # Shiny pattern: "You caught a ... Shiny Milcery with"
            r'[Yy]ou caught an?\s+[^\w]*(?:Shiny\s+)?([A-Za-z][\w\s\-\'\.]+?)\s+with',
        ]
        
        for pattern in direct_patterns:
            match = re.search(pattern, text)
            if match:
                extracted_name = match.group(1).strip()
                # Clean up any trailing/leading special chars
                extracted_name = re.sub(r'^[\s\*]+|[\s\*]+$', '', extracted_name)
                # Validate: must have at least 2 chars and not be just "a" or "an"
                if len(extracted_name) >= 2 and extracted_name.lower() not in ['a', 'an', 'the', 'with']:
                    # Check if this looks like a Pokemon name (has letters)
                    if re.match(r'^[A-Za-z]', extracted_name):
                        self.log(f"[NAME-DIRECT] Extracted from pattern: '{extracted_name}'")
                        return extracted_name
        
        # === PRIORITY 2: Search in pokemon_names list ===
        if not self.pokemon_names:
            return None
        
        # Sortiere nach Laenge (laengste zuerst) damit mehrteilige Namen
        # wie "Tapu Koko", "Mr. Mime", "Iron Hands" zuerst geprueft werden
        # und "Mewtwo" vor "Mew" gefunden wird
        sorted_names = sorted(self.pokemon_names, key=len, reverse=True)
        
        for name in sorted_names:
            name_lower = name.lower()
            # Einfache case-insensitive Substring-Suche im bereinigten Text
            pos = cleaned_lower.find(name_lower)
            if pos != -1:
                # Pruefe ob es ein eigenstaendiges Wort ist (nicht Teil eines anderen Wortes)
                # Zeichen vor dem Match pruefen
                if pos > 0:
                    char_before = cleaned_lower[pos - 1]
                    if char_before.isalpha():  # Buchstabe davor = Teil eines anderen Wortes
                        continue
                # Zeichen nach dem Match pruefen
                end_pos = pos + len(name_lower)
                if end_pos < len(cleaned_lower):
                    char_after = cleaned_lower[end_pos]
                    if char_after.isalpha():  # Buchstabe danach = Teil eines anderen Wortes
                        continue
                
                return name  # Gib den originalen Namen aus der Liste zurueck (korrekte Schreibweise)
        
        return None
    
    # ═════════════════════════════════════════════════════════════════
    #  CAPTCHA SYSTEM
    # ══════════════════════════════════════════════════════════════════
    
