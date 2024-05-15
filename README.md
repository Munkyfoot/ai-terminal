# AI Terminal 🚀

AI Terminal is a versatile Python-based command-line interface (CLI) tool that unlocks the power of OpenAI's models right from your terminal. It allows you to interact with AI models, perform file operations, and execute Python code snippets directly from the terminal.

## ✨ Features

- **Direct AI Interaction:** Chat directly with OpenAI's AI models from your terminal.
- **Platform-Specific Commands:** Seamlessly supports terminal commands for Windows, macOS, and Linux.
- **Coding Assistance:** Get in-terminal help for coding tasks.
- **Memory Utilization:** Optionally save and load conversation history to personalize and improve interactions.
- **File Operations:** Perform file reading and writing based on user interactions.
- **Directory Insight:** Let AI Terminal see the files and directories within your current working directory.
- **Python Execution:** Run Python code snippets directly from the terminal.

## 🔧 Prerequisites

- Python 3.7 or higher
- pip (Python Package Installer)
- OpenAI API key

## 📦 Installation

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

7. **Add your OpenAI API key in the `.env` file:**

   ```env
   OPENAI_API_KEY="YOUR_API_KEY"
   ```

## 🚀 Usage

To run AI Terminal, enter:

```bash
python main.py [query] [flags]
```

### Options:

- `query` (optional): Initial question or command to start the conversation.
- `flags`:
  - `--memory` or `-m`: Save/load conversation history to add long-term memory.
  - `--ls` or `-l`: Let AI Terminal see the files and directories in the current working directory.
  - `--always-allow` or `-a`: Execute file operations without requiring confirmation.
  - `--save-defaults` or `-S`: Save these flags as defaults for future runs.
  - `--reset-defaults` or `-R`: Revert the flags to their original defaults.

### Examples:

1. **Start AI Terminal:**
   ```bash
   python main.py
   ```
2. **Provide an initial query:**
   ```bash
   python main.py "How can I list files in a directory?"
   ```
3. **Use memory for conversation history:**
   ```bash
   python main.py "Do you remember our previous conversation?" --memory
   ```
4. **Show files and directories to the GPT model:**
   ```bash
   python main.py "What files are present in the current directory?" --ls
   ```
5. **Always allow file operations without confirmation:**
   ```bash
   python main.py "Create a file named 'hello.txt' with 'Hello, World!' as content" --always-allow
   ```
6. **Save the current flags as defaults:**
   ```bash
   python main.py --memory --ls --always-allow --save-defaults
   ```
7. **Reset the flags to their original defaults:**
   ```bash
   python main.py --reset-defaults
   ```

## 💡 Setting Up a Command Line Alias (`ask`)

### For Linux/macOS

1. **Edit your shell's configuration file (`.bashrc` or `.zshrc`):**

   ```bash
   nano ~/.bashrc  # or ~/.zshrc
   ```

2. **Add an alias:**

   ```bash
   alias ask='source /path/to/your/project/venv/bin/activate && python /path/to/your/project/main.py "$@" && deactivate'
   ```

3. **Apply the changes:**
   ```bash
   source ~/.bashrc  # or ~/.zshrc
   ```

### For Windows

1. **Add project directory to system PATH:**

   ```cmd
   setx PATH "%PATH%;C:\path\to\your\project"
   ```

2. **Create a batch file (`ask.bat`) in a directory in your PATH:**
   ```cmd
   echo @echo off > C:\path\to\your\project\ask.bat
   echo call C:\path\to\your\project\venv\Scripts\activate >> C:\path\to\your\project\ask.bat
   echo python C:\path\to\your\project\main.py %* >> C:\path\to\your\project\ask.bat
   echo call C:\path\to\your\project\venv\Scripts\deactivate >> C:\path\to\your\project\ask.bat
   ```

### Using the `ask` Command:

1. **Run without initial query:**
   ```bash
   ask
   ```
2. **Ask a general question:**
   ```bash
   ask "What's the weather today?"
   ```
3. **Use memory flag:**
   ```bash
   ask "Remember my last question?" --memory
   ```
4. **Show files and directories:**
   ```bash
   ask "What files are in this directory?" --ls
   ```
5. **Always allow file operations:**
   ```bash
   ask "Create a file named 'hello.txt' with 'Hello, World!' as content" --always-allow
   ```
6. **Save the current flags as defaults:**
   ```bash
   ask --memory --ls --always-allow --save-defaults
   ```
7. **Reset the flags to their original defaults:**
   ```bash
   ask --reset-defaults
   ```

## 🤝 Contributing

1. **Fork the repository.**
2. **Create a feature branch (`git checkout -b feature/AmazingFeature`).**
3. **Commit your changes (`git commit -m 'Add some AmazingFeature'`).**
4. **Push to the branch (`git push origin feature/AmazingFeature`).**
5. **Open a pull request.**

## 📜 License

Distributed under the MIT License. See `LICENSE` for more details.
