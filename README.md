# TranslateGemma

Batch translation helper using **TranslateGemma via Ollama**.

---

## Project Description

`translate_gemma.py` sends input text to a locally running Ollama model (`translategemma:4b`) and writes structured translations to `batch_output.json`.

Designed for fast local testing of translations (including Indian languages).

---

## Requirements

- Python 3.8+ (3.10+ recommended)
- Ollama installed
- ~6 GB free disk space for the model
- GPU recommended (works on CPU but slower)

---

## Installation Steps

### 1. Install Ollama

Download and install from:

https://ollama.com/download

Verify:

```bash
ollama --version
Pull the model:

bash
Copy code
ollama pull translategemma:4b
2. Install Python dependencies
(Optional but recommended)

bash
Copy code
python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate   # macOS / Linux
Install client:

bash
Copy code
pip install ollama
Project Structure
perl
Copy code
.
├── translate_gemma.py
├── batch.json
├── batch_output.json
├── my-docs/          # gitignored
└── README.md
Batch Input Format
Example batch.json:

json
Copy code
{
  "sequence": ["Hindi", "Tamil", "Telugu"],
  "items": [
    "Where is the nearest hospital?",
    "How much does this cost?"
  ]
}
sequence → target languages

items → list of English sentences

Usage
Default input:

bash
Copy code
python translate_gemma.py
Custom file:

bash
Copy code
python translate_gemma.py path/to/your_batch.json
Output will be written to:

pgsql
Copy code
batch_output.json
Notes
Edit sequence in batch.json to control target languages.

Translations are printed to console and saved to file.

Ollama must be running in the background.

Troubleshooting
Check Ollama:
ollama list

Test manually:
ollama run translategemma:4b








