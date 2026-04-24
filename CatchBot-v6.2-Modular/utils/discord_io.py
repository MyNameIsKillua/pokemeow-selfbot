"""DiscordIOMixin: send_command, wait_for_message* helpers."""
import asyncio
import random
from datetime import datetime
from colorama import Fore, Style


class DiscordIOMixin:
    async def wait_for_message(self, channel, keyword, timeout=15):
        """Wartet auf eine Nachricht die ein bestimmtes Keyword enthält"""
        def check(msg):
            if str(msg.channel.id) != str(channel.id):
                return False
            
            text = ""
            if msg.content:
                text += msg.content.lower()
            if msg.embeds:
                for embed in msg.embeds:
                    embed_dict = embed.to_dict()
                    if 'description' in embed_dict:
                        text += str(embed_dict['description']).lower()
                    if 'title' in embed_dict:
                        text += str(embed_dict['title']).lower()
            
            return keyword.lower() in text
        
        try:
            msg = await self.client.wait_for('message', check=check, timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False
    
    async def wait_for_message_return(self, channel, keyword, timeout=15):
        """Waits for a message containing a keyword and returns the message object (or None).
        If keyword is empty, returns the next non-self message in the channel."""
        def check(msg):
            if str(msg.channel.id) != str(channel.id):
                return False
            # Ignore own messages
            if self.client and self.client.user and msg.author.id == self.client.user.id:
                return False
            if not keyword:
                return True
            
            text = ""
            if msg.content:
                text += msg.content.lower()
            if msg.embeds:
                for embed in msg.embeds:
                    embed_dict = embed.to_dict()
                    if 'description' in embed_dict:
                        text += str(embed_dict['description']).lower()
                    if 'title' in embed_dict:
                        text += str(embed_dict['title']).lower()
                    # Also check author name (e.g. inventory embeds use author field)
                    author = embed_dict.get('author', {})
                    if 'name' in author:
                        text += str(author['name']).lower()
                    # Check footer too
                    footer = embed_dict.get('footer', {})
                    if 'text' in footer:
                        text += str(footer['text']).lower()
            
            return keyword.lower() in text
        
        try:
            msg = await self.client.wait_for('message', check=check, timeout=timeout)
            return msg
        except asyncio.TimeoutError:
            return None
    
    async def wait_for_message_edit_return(self, channel, keyword, timeout=15):
        """Waits for an edited message containing a keyword and returns the 'after' message.
        Used for PokeMeow fishing which edits its initial embed to add bite/nibble result."""
        def check(before, after):
            if str(after.channel.id) != str(channel.id):
                return False
            if self.client and self.client.user and after.author.id == self.client.user.id:
                return False
            
            text = ""
            if after.content:
                text += after.content.lower()
            if after.embeds:
                for embed in after.embeds:
                    embed_dict = embed.to_dict()
                    if 'description' in embed_dict:
                        text += str(embed_dict['description']).lower()
                    if 'title' in embed_dict:
                        text += str(embed_dict['title']).lower()
            
            return keyword.lower() in text
        
        try:
            before, after = await self.client.wait_for('message_edit', check=check, timeout=timeout)
            return after
        except asyncio.TimeoutError:
            return None
    
    # ═════════════════════════════════════════════════════════════════
    #  AUTOBUYER SYSTEM
    # ═════════════════════════════════════════════════════════════════
    
    async def send_command(self, channel, command):
        """Sendet einen Command im Discord-Channel"""
        try:
            await channel.send(command)
            self.log(f"Command sent: {command}")
            print(f"{Fore.GREEN}[{datetime.now().strftime('%H:%M:%S')}] Sent: {command}{Style.RESET_ALL}")
        except Exception as e:
            self.log(f"Error sending {command}: {str(e)}")
            print(f"{Fore.RED}[{datetime.now().strftime('%H:%M:%S')}] Error: {str(e)}{Style.RESET_ALL}")
    
