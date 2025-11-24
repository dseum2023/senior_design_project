# BrainBench LLM Tester

An interactive Python application that processes calculus questions from an XML dataset and queries a local LLM (gpt-oss:20b) via Ollama. The application processes questions one at a time with manual confirmation and stores results in JSON format.

## Features

- 🧮 **Interactive Processing**: Process calculus questions one at a time with manual confirmation
- 🤖 **Local LLM Integration**: Uses Ollama to query gpt-oss:20b model locally
- 💾 **Persistent Storage**: Saves results in JSON format with progress tracking
- 📊 **Progress Tracking**: Resume from where you left off if interrupted
- 📈 **Statistics & Reporting**: View progress summaries and export to CSV
- ⚙️ **Flexible Configuration**: Configurable Ollama URL and model selection

## Prerequisites

1. **Python 3.8+** installed on your system
2. **Ollama** installed and running locally
3. **gpt-oss:20b model** installed in Ollama
4. **calculus_comprehensive_1000.xml** file in the project directory

### Installing Ollama and Model

1. Install Ollama from [https://ollama.ai](https://ollama.ai)
2. Start Ollama service
3. Install the required model:
   ```bash
   ollama pull gpt-oss:20b
   ```

## Installation

1. Clone or download this project
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure `calculus_comprehensive_1000.xml` is in the project root directory

## Usage

### Basic Usage

Run the application with the interactive menu:

```bash
python main.py
```

### Command Line Options

```bash
python main.py --help
```

Available options:
- `--ollama-url`: Ollama server URL (default: http://localhost:11434)
- `--model`: LLM model name (default: gpt-oss:20b)
- `--auto-start`: Skip menu and start processing immediately

### Example Commands

```bash
# Use default settings
python main.py

# Use custom Ollama URL
python main.py --ollama-url http://192.168.1.100:11434

# Use different model
python main.py --model llama2:7b

# Auto-start processing
python main.py --auto-start
```

## How It Works

### 1. Question Processing Flow

1. **Load Questions**: Parse XML file or load from cache
2. **Display Question**: Show question details, category, and expected answer
3. **Query LLM**: Send question to local LLM via Ollama
4. **Show Response**: Display LLM response and processing time
5. **User Choice**: Manual confirmation to continue, skip, retry, or quit
6. **Save Result**: Store question and response in JSON format
7. **Repeat**: Continue with next question

### 2. Interactive Options

During processing, you can choose:
- **[C] Continue**: Save result and move to next question
- **[S] Skip**: Skip current question without saving
- **[R] Retry**: Query the LLM again for the same question
- **[Q] Quit**: Save progress and exit
- **[I] Info**: Show current progress statistics

### 3. Data Storage

The application creates a `data/` directory with:
- `questions.json`: Cached parsed questions from XML
- `results.json`: All LLM responses and metadata
- `progress.json`: Processing progress and session tracking

## Project Structure

```
calculus-llm-tester/
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── calculus_comprehensive_1000.xml  # Input XML file (not included)
├── src/
│   ├── __init__.py
│   ├── xml_parser.py       # XML parsing functionality
│   ├── ollama_client.py    # Ollama API client
│   ├── storage.py          # JSON storage management
│   └── question_processor.py # Interactive question processing
└── data/                   # Created automatically
    ├── questions.json      # Cached questions
    ├── results.json        # LLM responses
    └── progress.json       # Progress tracking
```

## Menu Options

### 1. Start Processing Questions
Begin or resume interactive question processing.

### 2. Show Progress Summary
Display statistics about processed questions:
- Total processed, successful, and failed responses
- Average processing time
- Breakdown by question category

### 3. Export Results to CSV
Export all results to a timestamped CSV file for analysis.

### 4. Test Ollama Connection
Verify that Ollama is running and the model is available.

### 5. Show Question Statistics
Display information about the loaded questions:
- Total questions by category
- Distribution percentages

## Sample Session

```
============================================================
🧮 CALCULUS LLM TESTER
============================================================
Interactive tool for testing calculus questions with LLM
Model: gpt-oss:20b via Ollama
============================================================

🔍 Checking prerequisites...
✅ Found XML file: calculus_comprehensive_1000.xml
📖 Initializing XML parser...
🤖 Initializing Ollama client...
💾 Initializing storage manager...
⚙️  Initializing question processor...
📂 Loading questions from cache...
✅ Loaded 1170 questions

================================================================================
Question #1 (1/1170)
Category: limits
--------------------------------------------------------------------------------
Question: Find the limit: lim(x→-2) [-5*x**4 + x**3 - 6*x**2 + 10*x - 1]
Expected Answer: -133
================================================================================

🔄 Querying LLM...

🤖 LLM Response:
--------------------------------------------------
To find this limit, I can substitute x = -2 directly since this is a polynomial function...

The limit is -133.
⏱️  Processing Time: 2.34 seconds
🔧 Model: gpt-oss:20b
--------------------------------------------------

Options:
  [C] Continue to next question
  [S] Skip this question
  [R] Retry this question
  [Q] Quit and save progress
  [I] Show progress info

Your choice: C
✅ Result saved successfully
```

## Error Handling

The application includes comprehensive error handling for:
- Network connection issues with Ollama
- Missing or invalid XML files
- JSON parsing errors
- File system permissions
- Model availability issues

## Data Format

### Results JSON Structure

```json
{
  "metadata": {
    "created": "2024-01-01T12:00:00",
    "total_questions": 1170,
    "processed_questions": 15,
    "successful_responses": 14,
    "failed_responses": 1
  },
  "results": [
    {
      "question_id": "1",
      "category": "limits",
      "question_text": "Find the limit: lim(x→-2) [-5*x**4 + x**3 - 6*x**2 + 10*x - 1]",
      "expected_answer": "-133",
      "llm_response": "To find this limit...",
      "processing_time": 2.34,
      "timestamp": "2024-01-01T12:00:00",
      "success": true,
      "model_used": "gpt-oss:20b"
    }
  ]
}
```

## Troubleshooting

### Common Issues

1. **"Cannot connect to Ollama server"**
   - Ensure Ollama is installed and running
   - Check if the URL is correct (default: http://localhost:11434)
   - Verify firewall settings

2. **"Model 'gpt-oss:20b' is not available"**
   - Install the model: `ollama pull gpt-oss:20b`
   - Check available models: `ollama list`

3. **"XML file not found"**
   - Ensure `calculus_comprehensive_1000.xml` is in the project directory
   - Check file permissions

4. **"Permission denied" errors**
   - Ensure write permissions for the `data/` directory
   - Run with appropriate user permissions

### Testing Components

You can test individual components:

```bash
# Test XML parser
python -m src.xml_parser

# Test Ollama client
python -m src.ollama_client

# Test storage system
python -m src.storage
```

## Contributing

This is a simple educational tool. Feel free to modify and extend it for your needs.

## License

This project is provided as-is for educational purposes.
