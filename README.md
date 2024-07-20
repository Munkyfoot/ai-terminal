# AI Terminal

AI Terminal is a Python-based command-line tool that enables interaction with OpenAI and Anthropic AI models directly from your terminal. The AI can read and write files, execute Python code, answer questions, and more. By default, it requires your confirmation before performing file operations and executing Python code - though this can be changed with caution.

## Features

- **Direct AI Interaction:** Engage with OpenAI's and Anthropic's AI models via terminal.
- **Multiple AI Models:** Support for various AI models, including GPT-4o, GPT-4-Turbo, GPT-3.5-Turbo, and Claude 3.5 Sonnet.
- **Cross-Platform Commands:** Supports Windows, macOS, and Linux.
- **Coding Assistance:** Help for programming tasks within the terminal.
- **Memory Utilization:** Option to save and load important information for context retention across sessions.
- **File Operations:** Read and write files based on user interaction.
- **Directory Insight:** View files and directories within your current directory.
- **Python Execution:** Run Python code snippets directly in terminal.
- **Syntax Highlighting:** Colorful output for better readability of code and commands.
- **Customizable Settings:** Save and load default settings for convenience.

## Prerequisites

- Python 3.7+
- pip (Python Package Installer)
- OpenAI API key and/or Anthropic API key

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Munkyfoot/ai-terminal.git
   ```

2. **Navigate to the project directory:**

   ```bash
   cd ai-terminal
   ```

3. **Create a virtual environment:**

   ```bash
   python -m venv venv
   ```

4. **Activate the virtual environment:**

   **This is required for the python execution tool to work.**

   - For Linux/macOS:
     ```bash
     source venv/bin/activate
     ```
   - For Windows:
     ```cmd
     venv\Scripts\activate
     ```

5. **Install the required dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

6. **Rename `.env.example` to `.env`:**

   - For Linux/macOS:
     ```bash
     mv .env.example .env
     ```
   - For Windows:
     ```cmd
     rename .env.example .env
     ```

7. **Add your API key(s) in the `.env` file:**

   ```env
   OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
   ANTHROPIC_API_KEY="YOUR_ANTHROPIC_API_KEY"
   ```

## Usage

Launch AI Terminal with:

```bash
python main.py [query] [flags]
```

Or use the command line alias:

```bash
ask [query] [flags]
```

_See [Command Line Alias](#command-line-alias-ask) for more details._

The query can be a question, command, or code snippet. The flags are optional and can be used to enable memory, file operations, directory insight, and more.

### Options:

- `query` (optional): Initial question or command.
- `flags`:
  - `--memory` | `-m`: Enable memory to save and load context across sessions.
  - `--ls` | `-l`: Let AI Terminal view files and directories.
  - `--always-allow` | `-a`: Execute file operations without confirmation.
  - `--save-defaults` | `-S`: Save current flags as defaults.
  - `--reset-defaults` | `-R`: Reset flags to default settings.
  - `--show-models`: Display available AI models.
  - `--model`: Choose the AI model to use (e.g., "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo", "claude-3-5-sonnet-20240620").
  - `--hide-splash`: Hide the ASCII art splash screen and settings display.

### Examples:

1. **Start AI Terminal:**
   ```bash
   python main.py
   ```
2. **Initial query:**
   ```bash
   python main.py "How can I list files in a directory?"
   ```
3. **Use memory:**
   ```bash
   python main.py "Do you remember our previous conversation?" --memory
   ```
4. **Show files and directories:**
   ```bash
   python main.py "What files are present in the current directory?" --ls
   ```
5. **Allow file operations without confirmation:**
   ```bash
   python main.py "Create a file named 'hello.txt' with 'Hello, World!' as content" --always-allow
   ```
6. **Save current flags as defaults:**
   ```bash
   python main.py --memory --ls --always-allow --save-defaults
   ```
7. **Reset flags to defaults:**
   ```bash
   python main.py --reset-defaults
   ```
8. **Show available AI models:**
   ```bash
   python main.py --show-models
   ```
9. **Use a specific AI model:**
   ```bash
   python main.py "Tell me a joke" --model gpt-4-turbo
   ```
10. **Hide the splash screen:**
    ```bash
    python main.py "What's the weather like today?" --hide-splash
    ```

## Command Line Alias (`ask`)

### For Linux/macOS

#### Bash:

1. **Edit shell configuration (`.bashrc`):**
   ```bash
   nano ~/.bashrc
   ```
2. **Add alias:**
   ```bash
   alias ask='source /path/to/project/venv/bin/activate && python /path/to/project/main.py "$@" && deactivate'
   ```
3. **Apply changes:**
   ```bash
   source ~/.bashrc
   ```

#### Zsh:

1. **Edit shell configuration (`.zshrc`):**
   ```bash
   nano ~/.zshrc
   ```
2. **Add function:**
   ```zsh
   function ask() {
       source /path/to/project/venv/bin/activate
       python /path/to/project/main.py "$@"
       deactivate
   }
   ```
3. **Apply changes:**
   ```bash
   source ~/.zshrc
   ```

### For Windows

1. **Add project directory to PATH:**
   ```cmd
   setx PATH "%PATH%;C:\path\to\project"
   ```
2. **Create batch file (`ask.bat`) in PATH:**
   ```cmd
   echo @echo off > C:\path\to\project\ask.bat
   echo call C:\path\to\project\venv\Scripts\activate >> C:\path\to\project\ask.bat
   echo python C:\path\to\project\main.py %* >> C:\path\to\project\ask.bat
   echo call C:\path\to\project\venv\Scripts\deactivate >> C:\path\to\project\ask.bat
   ```

### Using `ask` Command:

1. **Run without initial query:**
   ```bash
   ask
   ```
2. **General question:**
   ```bash
   ask "What's the weather today?"
   ```
3. **Use memory:**
   ```bash
   ask "Remember my last question?" --memory
   ```
4. **Show files and directories:**
   ```bash
   ask "What files are in this directory?" --ls
   ```
5. **Allow file operations without confirmation:**
   ```bash
   ask "Create a file named 'hello.txt' with 'Hello, World!' as content" --always-allow
   ```
6. **Save current flags as defaults:**
   ```bash
   ask --memory --ls --always-allow --save-defaults
   ```
7. **Reset flags to defaults:**
   ```bash
   ask --reset-defaults
   ```
8. **Use a specific AI model:**
   ```bash
   ask "Explain quantum computing" --model claude-3-5-sonnet-20240620
   ```
9. **Hide the splash screen:**
   ```bash
   ask "What's the capital of France?" --hide-splash
   ```

## Memory Feature

The memory feature in AI Terminal allows the AI to retain context across multiple sessions, enhancing its ability to provide consistent and contextually relevant responses. Here's how it works:

- When the `--memory` flag is used, the AI stores important information from the conversation in a JSON file (`memory.json`).
- In subsequent sessions with the `--memory` flag, the AI loads this stored information to maintain context.
- The memory is managed to stay within a 4096-character limit, ensuring optimal performance while retaining the most relevant information.

To use the memory feature:

1. Enable memory in a session:

   ```bash
   ask "Let's start a project about climate change" --memory
   ```

2. In a later session, reference previous context:
   ```bash
   ask "What were we discussing in our last session?" --memory
   ```

The AI will use the stored memory to provide a contextual response based on previous interactions.

## Contributing

1. **Fork the repository.**
2. **Create a feature branch (`git checkout -b feature/AmazingFeature`).**
3. **Commit changes (`git commit -m 'Add AmazingFeature'`).**
4. **Push to branch (`git push origin feature/AmazingFeature`).**
5. **Open a pull request.**

## License

Distributed under the MIT License. See `LICENSE` for details.
