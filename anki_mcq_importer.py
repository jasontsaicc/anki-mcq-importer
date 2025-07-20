#!/usr/bin/env python3
"""
Anki MCQ Auto Importer
A tool to automatically import Multiple Choice Questions into Anki from clipboard
"""

import re
import time
import json
import urllib.request
import urllib.error
import subprocess
import sys
import os
import argparse
from typing import Dict, List, Optional, Tuple
import hashlib
from datetime import datetime
from collections import deque

# Version info
__version__ = "1.0.0"
__author__ = "Your Name"
__license__ = "MIT"

# Configuration defaults
DEFAULT_CONFIG = {
    "deck_name": "AWS_SAP_02_IKKZ",
    "model_name": "IKKZ__MCQ.EN.NATIVE",
    "check_interval": 1.0,  # seconds
    "max_cache_size": 100,  # maximum number of cached hashes
    "anki_url": "http://localhost:8765",
    "tags": ["auto-imported", "mcq"],
    "verbose": False
}

class ClipboardManager:
    """Cross-platform clipboard manager with memory optimization"""
    
    def __init__(self):
        self._last_content = ""
        self._last_hash = ""
        
    def get_clipboard(self) -> str:
        """Get clipboard content with caching"""
        if sys.platform == 'darwin':
            try:
                result = subprocess.run(
                    ['pbpaste'], 
                    capture_output=True, 
                    text=True,
                    timeout=1
                )
                if result.returncode == 0:
                    content = result.stdout
                    # Cache to reduce subprocess calls
                    if hashlib.md5(content.encode()).hexdigest() != self._last_hash:
                        self._last_content = content
                        self._last_hash = hashlib.md5(content.encode()).hexdigest()
                    return content
            except Exception as e:
                if DEFAULT_CONFIG.get("verbose"):
                    print(f"Clipboard error: {e}")
        
        return self._last_content
    
    def test_clipboard(self) -> bool:
        """Test clipboard functionality"""
        print("Testing clipboard access...")
        content = self.get_clipboard()
        if content:
            print(f" Clipboard access OK (content length: {len(content)} chars)")
            return True
        else:
            print("  Clipboard is empty or inaccessible")
            return False

class AnkiConnector:
    """AnkiConnect API interface with connection pooling"""
    
    def __init__(self, url: str = DEFAULT_CONFIG["anki_url"]):
        self.url = url
        self._test_connection()
        
    def _test_connection(self):
        """Test connection to Anki"""
        try:
            self.invoke('version')
            print("✓ Connected to Anki")
        except Exception as e:
            print(f"✗ Cannot connect to Anki: {e}")
            raise
        
    def invoke(self, action: str, **params) -> dict:
        """Send request to AnkiConnect"""
        request_json = json.dumps({
            'action': action,
            'version': 6,
            'params': params
        }).encode('utf-8')
        
        request = urllib.request.Request(self.url, request_json)
        request.add_header('Content-Type', 'application/json')
        
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                
            if response_data['error'] is not None:
                raise Exception(response_data['error'])
                
            return response_data['result']
        except urllib.error.URLError as e:
            raise Exception(f"Cannot connect to Anki. Ensure Anki is running and AnkiConnect is installed. Error: {e}")
    
    def create_note(self, deck_name: str, model_name: str, fields: dict, tags: List[str] = None) -> int:
        """Create new note"""
        note = {
            'deckName': deck_name,
            'modelName': model_name,
            'fields': fields,
            'options': {
                'allowDuplicate': False,
                'duplicateScope': 'deck',
                'duplicateScopeOptions': {
                    'deckName': deck_name,
                    'checkChildren': False
                }
            }
        }
        
        if tags:
            note['tags'] = tags
            
        return self.invoke('addNote', note=note)
    
    def find_notes(self, query: str) -> List[int]:
        """Find notes"""
        return self.invoke('findNotes', query=query)
    
    def get_decks(self) -> List[str]:
        """Get all decks"""
        return self.invoke('deckNames')
    
    def create_deck(self, deck_name: str) -> int:
        """Create new deck"""
        return self.invoke('createDeck', deck=deck_name)
    
    def get_model_names(self) -> List[str]:
        """Get all model names"""
        return self.invoke('modelNames')
    
    def get_model_field_names(self, model_name: str) -> List[str]:
        """Get field names for a model"""
        return self.invoke('modelFieldNames', modelName=model_name)

class TextParser:
    """Text parser for MCQ format"""
    
    @staticmethod
    def parse_mcq_text(text: str) -> Optional[Dict[str, str]]:
        """Parse MCQ formatted text"""
        # Clean text
        text = text.strip()
        
        # Check for required markers
        if 'question:' not in text.lower() or 'answer:' not in text.lower():
            return None
        
        # Define parsing patterns
        patterns = {
            'question': r'question:\s*(.*?)(?=option[A-F]:|answer:|note:|$)',
            'optionA': r'option\s*A:\s*(.*?)(?=option[B-F]:|answer:|note:|$)',
            'optionB': r'option\s*B:\s*(.*?)(?=option[C-F]:|answer:|note:|$)',
            'optionC': r'option\s*C:\s*(.*?)(?=option[D-F]:|answer:|note:|$)',
            'optionD': r'option\s*D:\s*(.*?)(?=option[E-F]:|answer:|note:|$)',
            'optionE': r'option\s*E:\s*(.*?)(?=option[F]:|answer:|note:|$)',
            'optionF': r'option\s*F:\s*(.*?)(?=answer:|note:|$)',
            'answer': r'answer:\s*(.*?)(?=note:|$)',
            'note': r'note:\s*(.*?)(?=$)'
        }
        
        result = {}
        
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                # Clean up extra whitespace
                content = ' '.join(content.split())
                result[field] = content
        
        # Validate required fields
        required_fields = ['question', 'answer']
        if all(field in result for field in required_fields):
            return result
        
        return None
    
    @staticmethod
    def parse_alternative_format(text: str) -> Optional[Dict[str, str]]:
        """Parse alternative format with bullet points"""
        # For format like: • question: ... • options: A. ... B. ... • answer: ... • notes: ...
        if '• question:' not in text:
            return None
            
        patterns = {
            'question': r'•\s*question:\s*(.*?)(?=•\s*options:|$)',
            'options': r'•\s*options:\s*(.*?)(?=•\s*answer:|$)',
            'answer': r'•\s*answer:\s*(.*?)(?=•\s*notes:|$)',
            'notes': r'•\s*notes:\s*(.*?)(?=$)'
        }
        
        result = {}
        
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                result[field] = match.group(1).strip()
        
        # Parse individual options from the options field
        if 'options' in result:
            option_pattern = r'([A-F])\.\s*(.*?)(?=(?:[A-F]\.|$))'
            matches = re.findall(option_pattern, result['options'], re.DOTALL)
            
            # Initialize all options as empty
            for letter in 'ABCDEF':
                result[f'option{letter}'] = ''
            
            # Fill in found options
            for letter, content in matches:
                result[f'option{letter}'] = ' '.join(content.strip().split())
            
            # Remove the combined options field
            del result['options']
        
        # Map 'notes' to 'note' for consistency
        if 'notes' in result:
            result['note'] = result.pop('notes')
        
        # Validate required fields
        if 'question' in result and 'answer' in result:
            return result
        
        return None

class AnkiMCQImporter:
    """Main importer class with memory optimization"""
    
    def __init__(self, config: dict = None):
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.anki = AnkiConnector(self.config["anki_url"])
        self.clipboard = ClipboardManager()
        
        # Memory-efficient cache using deque
        self.processed_hashes = deque(maxlen=self.config["max_cache_size"])
        self.last_clipboard_hash = ""
        self.import_count = 0
        self.start_time = datetime.now()
        
        self._validate_setup()
        
    def _validate_setup(self):
        """Validate Anki setup"""
        # Check if model exists
        try:
            models = self.anki.get_model_names()
            if self.config["model_name"] not in models:
                print(f"⚠️  Warning: Model '{self.config['model_name']}' not found")
                print(f"Available models: {', '.join(models[:5])}...")
                
                # Try to find MCQ model
                mcq_models = [m for m in models if 'MCQ' in m.upper()]
                if mcq_models:
                    print(f"Found MCQ models: {', '.join(mcq_models)}")
                    self.config["model_name"] = mcq_models[0]
                    print(f"Using model: {self.config['model_name']}")
        except Exception as e:
            print(f"Error checking models: {e}")
        
        # Ensure deck exists
        self._ensure_deck_exists()
        
    def _ensure_deck_exists(self):
        """Ensure target deck exists"""
        try:
            decks = self.anki.get_decks()
            if self.config["deck_name"] not in decks:
                self.anki.create_deck(self.config["deck_name"])
                print(f"✓ Created deck: {self.config['deck_name']}")
        except Exception as e:
            print(f"Error checking deck: {e}")
    
    def _get_content_hash(self, content: str) -> str:
        """Get hash of content"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def process_content(self, content: str) -> bool:
        """Process clipboard content"""
        # Check if already processed
        content_hash = self._get_content_hash(content)
        if content_hash in self.processed_hashes:
            return False
        
        if self.config.get("verbose"):
            print(f"\nDetected new content ({len(content)} chars)")
        
        # Try parsing with both formats
        parsed = TextParser.parse_mcq_text(content)
        if not parsed:
            parsed = TextParser.parse_alternative_format(content)
        
        if not parsed:
            if self.config.get("verbose"):
                print("✗ Cannot parse content (invalid format)")
            return False
        
        # Build fields for Anki
        fields = {
            'question': parsed.get('question', ''),
            'optionA': parsed.get('optionA', ''),
            'optionB': parsed.get('optionB', ''),
            'optionC': parsed.get('optionC', ''),
            'optionD': parsed.get('optionD', ''),
            'optionE': parsed.get('optionE', ''),
            'optionF': parsed.get('optionF', ''),
            'answer': parsed.get('answer', ''),
            'note': parsed.get('note', '')
        }
        
        # Display parsed result
        print(f"\n Question: {fields['question'][:60]}...")
        print(f"✓ Answer: {fields['answer']}")
        
        try:
            # Create note
            note_id = self.anki.create_note(
                deck_name=self.config["deck_name"],
                model_name=self.config["model_name"],
                fields=fields,
                tags=self.config["tags"]
            )
            
            self.import_count += 1
            print(f" Imported successfully (ID: {note_id}, Total: {self.import_count})")
            
            # Add to processed cache
            self.processed_hashes.append(content_hash)
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            if "duplicate" in error_msg.lower():
                print(" Skipped: Duplicate card")
                self.processed_hashes.append(content_hash)
            else:
                print(f" Import failed: {error_msg}")
            return False
    
    def start_monitoring(self):
        """Start clipboard monitoring"""
        print("\n" + "=" * 60)
        print(" Anki MCQ Auto Importer v" + __version__)
        print("=" * 60)
        print(f" Deck: {self.config['deck_name']}")
        print(f" Model: {self.config['model_name']}")
        print(f"  Tags: {', '.join(self.config['tags'])}")
        print(f"  Check interval: {self.config['check_interval']}s")
        
        # Test clipboard
        self.clipboard.test_clipboard()
        
        print("\n Monitoring clipboard...")
        print(" Copy MCQ text to auto-import")
        print(" Press Ctrl+C to stop")
        print("-" * 60)
        
        check_count = 0
        
        try:
            while True:
                try:
                    # Get clipboard content
                    current_content = self.clipboard.get_clipboard()
                    
                    if current_content:
                        current_hash = self._get_content_hash(current_content)
                        
                        # Check if content changed
                        if current_hash != self.last_clipboard_hash:
                            self.last_clipboard_hash = current_hash
                            
                            # Check for MCQ markers
                            if ('question:' in current_content.lower() and 
                                'answer:' in current_content.lower()):
                                self.process_content(current_content)
                            elif self.config.get("verbose") and len(current_content) < 200:
                                print(f"[{datetime.now().strftime('%H:%M:%S')}] Clipboard updated but not MCQ format")
                    
                    # Show status periodically
                    check_count += 1
                    if check_count % (30 / self.config['check_interval']) == 0:
                        elapsed = (datetime.now() - self.start_time).seconds
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Active for {elapsed//60}m {elapsed%60}s | Imported: {self.import_count}")
                        
                        # Memory cleanup every 5 minutes
                        if elapsed % 300 == 0:
                            import gc
                            gc.collect()
                    
                except Exception as e:
                    print(f"Error processing clipboard: {e}")
                
                # Sleep
                time.sleep(self.config['check_interval'])
                
        except KeyboardInterrupt:
            self._show_summary()
    
    def _show_summary(self):
        """Show import summary"""
        elapsed = (datetime.now() - self.start_time).seconds
        print(f"\n\n{'=' * 60}")
        print(" Import Summary")
        print(f"{'=' * 60}")
        print(f" Cards imported: {self.import_count}")
        print(f" Unique items processed: {len(self.processed_hashes)}")
        print(f"⏱  Total time: {elapsed//60}m {elapsed%60}s")
        if self.import_count > 0:
            print(f"⚡ Average: {elapsed/self.import_count:.1f}s per card")
        print(f"{'=' * 60}")

def load_config(config_file: str) -> dict:
    """Load configuration from file"""
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
    return {}

def save_config(config: dict, config_file: str):
    """Save configuration to file"""
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✓ Configuration saved to {config_file}")
    except Exception as e:
        print(f"Error saving config: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Anki MCQ Auto Importer - Automatically import MCQs from clipboard to Anki',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                     # Start with default settings
  %(prog)s --deck "AWS Exam"   # Import to specific deck
  %(prog)s --config my.json    # Use custom config file
  %(prog)s --test              # Test clipboard access
  %(prog)s --setup             # Interactive setup
        """
    )
    
    parser.add_argument('--deck', help='Target deck name')
    parser.add_argument('--model', help='Card model name')
    parser.add_argument('--tags', nargs='+', help='Tags to add to cards')
    parser.add_argument('--interval', type=float, help='Check interval in seconds')
    parser.add_argument('--config', default='anki_mcq_config.json', help='Config file path')
    parser.add_argument('--save-config', action='store_true', help='Save current settings to config')
    parser.add_argument('--test', action='store_true', help='Test clipboard access')
    parser.add_argument('--setup', action='store_true', help='Run interactive setup')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    
    args = parser.parse_args()
    
    # Load config
    config = {**DEFAULT_CONFIG, **load_config(args.config)}
    
    # Override with command line args
    if args.deck:
        config['deck_name'] = args.deck
    if args.model:
        config['model_name'] = args.model
    if args.tags:
        config['tags'] = args.tags
    if args.interval:
        config['check_interval'] = args.interval
    if args.verbose:
        config['verbose'] = True
    
    # Test mode
    if args.test:
        print("🧪 Testing clipboard access...\n")
        clipboard = ClipboardManager()
        clipboard.test_clipboard()
        print("\n📋 Monitoring clipboard for 10 seconds...")
        for i in range(10):
            content = clipboard.get_clipboard()
            print(f"{i+1}. Clipboard: {content[:50] if content else '(empty)'}")
            time.sleep(1)
        return
    
    # Interactive setup
    if args.setup:
        print("🔧 Interactive Setup\n")
        config['deck_name'] = input(f"Deck name [{config['deck_name']}]: ") or config['deck_name']
        config['model_name'] = input(f"Model name [{config['model_name']}]: ") or config['model_name']
        tags_input = input(f"Tags (space-separated) [{' '.join(config['tags'])}]: ")
        if tags_input:
            config['tags'] = tags_input.split()
        interval = input(f"Check interval (seconds) [{config['check_interval']}]: ")
        if interval:
            config['check_interval'] = float(interval)
        
        save = input("\nSave configuration? [Y/n]: ")
        if save.lower() != 'n':
            save_config(config, args.config)
    
    # Save config if requested
    if args.save_config:
        save_config(config, args.config)
        return
    
    # Start importer
    try:
        importer = AnkiMCQImporter(config)
        importer.start_monitoring()
    except KeyboardInterrupt:
        print("\n\n Goodbye!")
    except Exception as e:
        print(f"\n Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()