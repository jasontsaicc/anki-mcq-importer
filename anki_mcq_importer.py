#!/usr/bin/env python3
"""
Anki Auto Import Tool for MCQ Template
"""

import re
import time
import json
import urllib.request
import urllib.error
import subprocess
import sys
from typing import Dict, List, Optional
import hashlib

# 嘗試導入 pyperclip，如果失敗則使用備用方案
try:
    import pyperclip
    USE_PYPERCLIP = True
except ImportError:
    USE_PYPERCLIP = False
    print("提示: pyperclip 未安裝，使用 macOS 原生方法")

class ClipboardManager:
    """跨平台剪貼簿管理器"""
    
    @staticmethod
    def get_clipboard():
        """取得剪貼簿內容"""
        if USE_PYPERCLIP:
            try:
                return pyperclip.paste()
            except:
                # 如果 pyperclip 失敗，嘗試 macOS 方法
                pass
        
        # macOS 原生方法
        if sys.platform == 'darwin':
            try:
                result = subprocess.run(['pbpaste'], 
                                      capture_output=True, 
                                      text=True,
                                      timeout=1)
                if result.returncode == 0:
                    return result.stdout
            except Exception as e:
                print(f"pbpaste 錯誤: {e}")
        
        return ""
    
    @staticmethod
    def test_clipboard():
        """測試剪貼簿功能"""
        print("測試剪貼簿存取...")
        content = ClipboardManager.get_clipboard()
        if content:
            print(f"✓ 剪貼簿存取正常，當前內容長度: {len(content)} 字元")
            return True
        else:
            print("⚠️  剪貼簿為空或無法存取")
            return False

class AnkiConnector:
    """AnkiConnect API 介面"""
    
    def __init__(self, url='http://localhost:8765'):
        self.url = url
        
    def invoke(self, action: str, **params) -> dict:
        """發送請求到 AnkiConnect"""
        request_json = json.dumps({
            'action': action,
            'version': 6,
            'params': params
        })
        
        try:
            response = urllib.request.urlopen(
                urllib.request.Request(
                    self.url,
                    request_json.encode('utf-8')
                )
            )
            response_data = json.loads(response.read().decode('utf-8'))
            
            if response_data['error'] is not None:
                raise Exception(response_data['error'])
                
            return response_data['result']
        except urllib.error.URLError:
            raise Exception("無法連接到 Anki。請確保 Anki 已開啟且 AnkiConnect 插件已安裝。")
    
    def create_note(self, deck_name: str, model_name: str, fields: dict, tags: List[str] = None) -> int:
        """建立新卡片"""
        note = {
            'deckName': deck_name,
            'modelName': model_name,
            'fields': fields,
            'options': {
                'allowDuplicate': False
            }
        }
        
        if tags:
            note['tags'] = tags
            
        return self.invoke('addNote', note=note)
    
    def find_notes(self, query: str) -> List[int]:
        """查詢卡片"""
        return self.invoke('findNotes', query=query)
    
    def get_decks(self) -> List[str]:
        """取得所有牌組"""
        return self.invoke('deckNames')
    
    def create_deck(self, deck_name: str) -> int:
        """建立新牌組"""
        return self.invoke('createDeck', deck=deck_name)

class TextParser:
    """文字解析器"""
    
    @staticmethod
    def parse_clipboard_text(text: str) -> Optional[Dict[str, str]]:
        """解析剪貼簿文字並返回所有欄位"""
        # 清理文字
        text = text.strip()
        
        # 檢查是否包含必要的標記
        if 'question:' not in text or 'answer:' not in text:
            return None
        
        # 定義解析模式 
        patterns = {
            'question': r'\s*question:\s*(.*?)(?=\s*optionA:|$)',
            'optionA': r'\s*optionA:\s*(.*?)(?=\s*optionB:|$)',
            'optionB': r'\s*optionB:\s*(.*?)(?=\s*optionC:|$)',
            'optionC': r'\s*optionC:\s*(.*?)(?=\s*optionD:|$)',
            'optionD': r'\s*optionD:\s*(.*?)(?=\s*optionE:|answer:|$)',
            'optionE': r'\s*optionE:\s*(.*?)(?=\s*optionF:|answer:|$)',
            'optionF': r'\s*optionF:\s*(.*?)(?=\s*answer:|note:|$)',
            'answer': r'\s*answer:\s*(.*?)(?=\s*note:|$)',
            'note': r'\s*note:\s*(.*?)(?=$)'
        }

        
        result = {}
        
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                result[field] = match.group(1).strip()
        
        # 解析個別選項
        if 'options' in result:
            options_dict = TextParser._parse_options(result['options'])
            result.update(options_dict)
        
        # 驗證必要欄位
        required_fields = ['question', 'answer']
        if all(field in result for field in required_fields):
            return result
        
        return None
    

class AnkiAutoImporter:
    """主程式類別"""
    
    def __init__(self, deck_name: str = "test", model_name: str = "IKKZ__MCQ.EN.NATIVE"):
        self.anki = AnkiConnector()
        self.deck_name = deck_name
        self.model_name = model_name
        self.last_clipboard = ""
        self.processed_hashes = set()
        self.import_count = 0
        
        # 確保牌組存在
        self._ensure_deck_exists()
        
    def _ensure_deck_exists(self):
        """確保牌組存在"""
        try:
            decks = self.anki.get_decks()
            if self.deck_name not in decks:
                self.anki.create_deck(self.deck_name)
                print(f"已建立牌組: {self.deck_name}")
        except Exception as e:
            print(f"檢查牌組時發生錯誤: {e}")
    
    def _get_content_hash(self, content: str) -> str:
        """計算內容雜湊值"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def process_clipboard(self, content: str) -> bool:
        """處理剪貼簿內容"""
        # 檢查是否已處理過
        content_hash = self._get_content_hash(content)
        if content_hash in self.processed_hashes:
            return False
        
        print(f"\n偵測到新內容 (長度: {len(content)} 字元)")
        
        # 解析文字
        parsed = TextParser.parse_clipboard_text(content)
        if not parsed:
            print("無法解析內容（格式不符）")
            return False
        
        # 建立 MCQ 卡片欄位
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

        
        # 顯示解析結果
        print(f"問題: {fields['question'][:60]}...")
        print(f"答案: {fields['answer']}")
        
        try:
            # 新增卡片
            note_id = self.anki.create_note(
                deck_name=self.deck_name,
                model_name=self.model_name,
                fields=fields,
                tags=['auto-imported', 'mcq']
            )
            
            self.import_count += 1
            print(f"✓ 成功匯入卡片 (ID: {note_id}, 總計: {self.import_count})")
            self.processed_hashes.add(content_hash)
            return True
            
        except Exception as e:
            print(f"✗ 匯入失敗: {e}")
            return False
    
    def start_monitoring(self):
        """開始監聽剪貼簿"""
        print("=" * 60)
        print("Anki MCQ 自動匯入工具")
        print("=" * 60)
        print(f"目標牌組: {self.deck_name}")
        print(f"卡片類型: {self.model_name}")
        
        # 測試剪貼簿
        ClipboardManager.test_clipboard()
        
        print("\n開始監聽剪貼簿...")
        print("複製符合格式的文字即可自動匯入")
        print("按 Ctrl+C 停止")
        print("-" * 60)
        
        check_count = 0
        
        try:
            while True:
                try:
                    # 取得剪貼簿內容
                    current_clipboard = ClipboardManager.get_clipboard()
                    
                    # 每 30 秒顯示一次狀態
                    check_count += 1
                    if check_count % 60 == 0:  # 0.5秒 * 60 = 30秒
                        print(f"[{time.strftime('%H:%M:%S')}] 監聽中... (已檢查 {check_count} 次)")
                    
                    # 檢查剪貼簿是否有變化
                    if current_clipboard and current_clipboard != self.last_clipboard:
                        self.last_clipboard = current_clipboard
                        
                        # 檢查是否包含必要的標記
                        if 'question:' in current_clipboard and 'answer:' in current_clipboard:
                            # 嘗試處理內容
                            self.process_clipboard(current_clipboard)
                            print("-" * 60)
                        else:
                            # 偵測到變化但格式不符
                            if len(current_clipboard) < 200:
                                print(f"[{time.strftime('%H:%M:%S')}] 剪貼簿已更新但格式不符: {current_clipboard[:50]}...")
                        
                except Exception as e:
                    print(f"處理剪貼簿時發生錯誤: {e}")
                
                # 短暫休息
                time.sleep(3)
                
        except KeyboardInterrupt:
            print(f"\n\n監聽已停止")
            print(f"本次共匯入 {self.import_count} 張卡片")
            print(f"處理過 {len(self.processed_hashes)} 個不同的內容")

def main():
    """主程式進入點"""
    # 檢查命令列參數
    import argparse
    parser = argparse.ArgumentParser(description='Anki MCQ 自動匯入工具')
    parser.add_argument('--deck', default='test', help='目標牌組名稱')
    parser.add_argument('--model', default='IKKZ__MCQ.EN.NATIVE', help='卡片模型名稱')
    parser.add_argument('--test', action='store_true', help='執行剪貼簿測試')
    
    args = parser.parse_args()
    
    if args.test:
        # 執行測試模式
        print("執行剪貼簿測試...")
        ClipboardManager.test_clipboard()
        print("\n請複製一些文字，程式將顯示剪貼簿內容...")
        for i in range(10):
            content = ClipboardManager.get_clipboard()
            print(f"{i+1}. 剪貼簿: {content[:50] if content else '(空)'}")
            time.sleep(3)
        return
    
    # 建立匯入器
    importer = AnkiAutoImporter(deck_name=args.deck, model_name=args.model)
    
    # 開始監聽
    importer.start_monitoring()

if __name__ == "__main__":
    main()