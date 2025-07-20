#!/usr/bin/env python3
"""
Test script to verify text formatting functionality
"""

import sys
import os

# Add src to path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from anki_mcq_importer.parser import MCQParser
from anki_mcq_importer.text_formatter import format_mcq_field

def test_formatting():
    """Test the formatting with a sample MCQ"""
    
    # Sample MCQ content with formatting
    sample_mcq = """question: AWS API Gateway 的安全防護問題
optionA: 使用 CloudFront + WAF，設定 IP 白名單
optionB: 使用 CloudFront + WAF，搭配 OAI
optionC: 只使用 Resource Policy 限制請求數
optionD: 使用 WAF + Usage Plan + API Key
answer: D
note: 題目重點：
API Gateway 為 Regional endpoint（不是透過 CloudFront）
合作對象明確（僅六位合作夥伴）
請求頻率應該很低（每天一次）
被 botnet 大量攻擊（每秒 1000 請求，500 IP）
目標是「保護 API 並最小化成本」

為何選擇 D？
WAF ACL 限定六個合作夥伴的 IP，可擋下所有不明流量。
搭配 API Gateway Usage Plan + API Key，可對每個合作夥伴設下請求配額。
Usage Plan 可設定速率限制與配額（例如每天最多 1 次請求），完全符合需求。
不需額外加上 CloudFront 或 Lambda，成本最低、效能直接、維護簡單。

錯誤選項分析：
A & B（CloudFront + WAF）
題目已是 Regional Endpoint，不建議額外再繞 CloudFront，會增加成本與延遲。
CloudFront OAI 概念主要用於保護 S3，不適用於 API Gateway。
實作與維運較複雜，無法直接限制特定 IP。

C（使用 Resource Policy 限制請求數）
Resource Policy 是 IAM 授權策略，無法用來限制請求速率或頻率。
API Gateway 的速率控制需透過 Usage Plan。

費曼學習法總結：
你可以想像 WAF 就像在 API 前加了一道門，只讓合作夥伴的 IP 進來。進來之後還要「輸入 API 金鑰」才可以進一步使用 POST 方法，而 Usage Plan 則像一個「出入證配額系統」，限制每天只能用一次，這樣就能有效防止 botnet 攻擊，又不增加不必要的元件或費用。"""

    print("=== 測試 MCQ 格式化功能 ===\n")
    
    # Parse the MCQ
    parser = MCQParser()
    mcq_data = parser.parse(sample_mcq)
    
    if not mcq_data:
        print("❌ MCQ 解析失敗")
        return False
    
    print("✅ MCQ 解析成功")
    print(f"問題: {mcq_data.question[:50]}...")
    print(f"選項數量: {len(mcq_data.options)}")
    print(f"答案: {mcq_data.answer}")
    print(f"說明長度: {len(mcq_data.note)} 字元\n")
    
    # Test formatting
    print("=== 原始說明文字 ===")
    print(f"前100字元: {mcq_data.note[:100]}...")
    print()
    
    print("=== 格式化後的說明 (HTML) ===")
    formatted_note = format_mcq_field(mcq_data.note, "note", True)
    print(f"前300字元: {formatted_note[:300]}...")
    print()
    
    # Convert to Anki fields
    print("=== Anki 字段格式 ===")
    anki_fields = mcq_data.to_anki_fields(preserve_formatting=True)
    
    for field_name, field_value in anki_fields.items():
        if field_value:
            print(f"{field_name}: {field_value[:100]}{'...' if len(field_value) > 100 else ''}")
    
    print("\n=== 格式化功能驗證 ===")
    
    # Check if formatting is preserved
    checks = {
        "包含 <br> 標籤": "<br>" in formatted_note,
        "包含樣式設定": "style=" in formatted_note,
        "包含粗體標題": "font-weight: bold" in formatted_note,
        "包含縮排或列表": "margin-left" in formatted_note or "span style" in formatted_note,
        "保留中文冒號": "題目重點：" in formatted_note,
        "保留換行結構": "為何選擇 D？" in formatted_note,
        "文字完整性": len(formatted_note) > 500,  # 确保内容没有被截断
    }
    
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}")
    
    all_passed = all(checks.values())
    
    if all_passed:
        print("\n🎉 所有格式化測試通過！")
        print("文字格式應該會在 Anki 中正確顯示，包含：")
        print("- 保留換行和段落結構")
        print("- 標題會以粗體顯示")
        print("- 列表項目會有適當的縮排")
        print("- 整體版面會更容易閱讀")
    else:
        print("\n⚠️ 部分格式化測試未通過")
    
    return all_passed

if __name__ == "__main__":
    success = test_formatting()
    sys.exit(0 if success else 1)