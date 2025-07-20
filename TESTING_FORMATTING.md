# 測試文字格式化功能

## 快速測試

### 1. 執行格式化測試腳本
```bash
python3 test_formatting.py
```

### 2. 使用範例檔案測試
```bash
# 使用新的 CLI 測試
pip install -e .
anki-mcq-importer --test

# 測試範例 MCQ
cat examples/formatted_sample.txt
```

### 3. 手動測試格式化

複製以下內容到剪貼簿並啟動匯入器：

```
question: AWS API Gateway 安全測試
optionA: 選項 A
optionB: 選項 B  
optionC: 選項 C
optionD: 選項 D
answer: B
note: 題目重點：
這是第一個重點
這是第二個重點

解答說明：
這裡是詳細的解答說明
包含多個段落和換行

重要概念：
• 第一個要點
• 第二個要點
• 第三個要點

總結：
「重要術語」會被特別標示
**粗體文字** 會正確顯示
*斜體文字* 也會正確顯示
```

## 預期結果

在 Anki 中應該會看到：

### Note 欄位格式化效果：
- **題目重點：** (粗體標題)
  - 這是第一個重點
  - 這是第二個重點

- **解答說明：** (粗體標題)
  - 這裡是詳細的解答說明
  - 包含多個段落和換行

- **重要概念：** (粗體標題)
  - • 第一個要點
  - • 第二個要點  
  - • 第三個要點

- **總結：** (粗體標題)
  - 重要術語 會被特別標示
  - **粗體文字** 會正確顯示
  - *斜體文字* 也會正確顯示

## 自訂格式化設定

### 停用格式化
```bash
anki-mcq-importer --no-formatting
```

### 只停用樣式但保留換行
```bash
anki-mcq-importer --no-styling
```

### 配置檔設定
```json
{
  "preserve_formatting": true,
  "convert_markdown": true,
  "add_note_styling": true
}
```

## 故障排除

如果格式化沒有正常運作：

1. **檢查 Anki 卡片模板**：確保模板支援 HTML 格式
2. **測試簡單範例**：先用基本的換行測試
3. **查看匯入日誌**：使用 `--verbose` 選項檢查詳細日誌
4. **檢查配置**：使用 `--status` 查看目前的格式化設定

## 報告問題

如果發現格式化問題，請提供：
1. 原始輸入文字
2. 預期的顯示效果
3. 實際的顯示效果
4. 使用的配置設定

這樣我們就能快速協助解決問題！