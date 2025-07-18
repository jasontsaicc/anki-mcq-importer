# Anki MCQ Auto Importer 

Automatically import Multiple Choice Questions (MCQs) into Anki from your clipboard. Perfect for exam preparation, especially for AWS certifications and other technical exams.

## ✨ Features

- 📋 **Clipboard Monitoring**: Automatically detects and imports MCQs when copied
- 🔄 **Smart Parsing**: Supports multiple MCQ text formats
- 🚫 **Duplicate Prevention**: Automatically skips already imported questions
- 💾 **Memory Efficient**: Optimized for long-running sessions
- ⚙️ **Configurable**: Customize deck names, tags, and import behavior
- 🖥️ **Cross-platform**: Works on macOS, with Windows/Linux support planned

## 📸 Demo



## 🚀 Quick Start

### Prerequisites

1. **Anki** (version 2.1+) - [Download here](https://apps.ankiweb.net/)
2. **AnkiConnect** addon - Install code: `2055492159`
3. **Python 3.7+**
4. **MCQ Card Template** - [Download from IKKZ](https://template.ikkz.fun/?template=mcq.en.native)

### Installation

```bash
# Clone the repository
git clone https://github.com/jasontsaicc/anki-mcq-importer.git
cd anki-mcq-importer

# Install dependencies (minimal - uses standard library)
# No pip install required!

# Make executable (optional)
chmod +x anki_mcq_importer.py
```

### Basic Usage

```bash
# Start monitoring with defaults
python3 anki_mcq_importer.py

# Use specific deck
python3 anki_mcq_importer.py --deck "AWS Exam Prep"

# Interactive setup (recommended for first time)
python3 anki_mcq_importer.py --setup
```

## 📝 Supported Formats

### Format 1: Structured MCQ
```
question: What is the capital of France?
optionA: London
optionB: Berlin
optionC: Paris
optionD: Madrid
optionE: Rome
optionF: Amsterdam
answer: C
note: Paris has been the capital of France since 987 AD.
```

### Format 2: Bullet Point Style
```
• question: What is the capital of France?
• options:
A. London
B. Berlin
C. Paris
D. Madrid
E. Rome
F. Amsterdam
• answer: C
• notes: Paris has been the capital of France since 987 AD.
```

## ⚙️ Configuration

Create a `anki_mcq_config.json` file or use `--setup`:

```json
{
  "deck_name": "My MCQ Deck",
  "model_name": "IKKZ__MCQ.EN.NATIVE",
  "tags": ["auto-imported", "mcq"],
  "check_interval": 1.0,
  "max_cache_size": 100,
  "verbose": false
}
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `deck_name` | Target Anki deck | `MCQ_Import` |
| `model_name` | Anki note type | `IKKZ__MCQ.EN.NATIVE` |
| `tags` | Tags to add to cards | `["auto-imported", "mcq"]` |
| `check_interval` | Clipboard check frequency (seconds) | `1.0` |
| `max_cache_size` | Maximum cached items | `100` |
| `verbose` | Enable detailed logging | `false` |

## 🛠️ Advanced Usage

### Command Line Options

```bash
# Test clipboard access
python3 anki_mcq_importer.py --test

# Use custom config file
python3 anki_mcq_importer.py --config myconfig.json

# Save current settings
python3 anki_mcq_importer.py --deck "AWS" --tags aws exam --save-config

# Verbose output for debugging
python3 anki_mcq_importer.py --verbose
```

### Batch Import from File

```python
# batch_import.py
from anki_mcq_importer import AnkiMCQImporter

importer = AnkiMCQImporter()

with open('questions.txt', 'r') as f:
    content = f.read()
    
# Split by delimiter
questions = content.split('\n---\n')

for q in questions:
    importer.process_content(q)
```

## 🔧 Troubleshooting

### macOS Clipboard Access

If clipboard monitoring doesn't work on macOS:

1. Grant Terminal/IDE accessibility permissions:
   - System Preferences → Security & Privacy → Privacy → Accessibility
   - Add your Terminal app

2. Test clipboard access:
   ```bash
   python3 anki_mcq_importer.py --test
   ```

### AnkiConnect Issues

1. Ensure Anki is running
2. Check AnkiConnect is installed (Tools → Add-ons)
3. Restart Anki after installing AnkiConnect

### Memory Issues

The tool includes automatic memory management:
- Caches only recent items (configurable via `max_cache_size`)
- Performs garbage collection every 5 minutes
- Uses efficient data structures (deque)

## 📊 Performance

- **Memory Usage**: ~10-20MB for typical usage
- **CPU Usage**: < 1% when idle
- **Import Speed**: ~1-2 seconds per card
- **Clipboard Check**: Configurable (default 1 second)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/asontsaicc/anki-mcq-importer.git
cd anki-mcq-importer

# Create virtual environment (optional)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run tests
python3 -m pytest tests/
```

## Roadmap

- [ ] Windows clipboard support
- [ ] Linux clipboard support  
- [ ] GUI version with system tray
- [ ] Support for more question formats
- [ ] Image support in questions
- [ ] Excel/CSV import
- [ ] Question bank management
- [ ] Statistics and analytics


##  Acknowledgments

- [Anki](https://apps.ankiweb.net/) - Powerful, intelligent flash cards
- [AnkiConnect](https://github.com/FooSoft/anki-connect) - Anki plugin for external applications
- [IKKZ MCQ Template](https://template.ikkz.fun/) - Professional MCQ card template

##  Support

- 📧 Contact: jason.tsaicc@gmail.com

---

Made with ❤️ for the Anki community