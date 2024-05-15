# AI Terminal

AI Terminal is a Python-based command-line interface (CLI) tool that allows you to interact with OpenAI's models, providing a convenient and direct way to chat with an AI and get assistance with various tasks. This includes support for terminal commands, coding help, and other queries. The application provides function calling for file operations based on user interactions.

## Features

- **Direct AI Interaction**: Engage directly with OpenAI's AI models from your terminal.
- **Platform-Specific Commands**: Supports terminal commands specific to your platform (Windows, macOS, or Linux).
- **Coding Assistance**: Get help with coding tasks directly in your terminal.
- **Memory Utilization**: Optionally save and load conversation history to improve response quality over time.
- **File Operations**: Perform file reading and writing based on your interactions.
- **File and Directory Listing**: Optionally show a list of files and directories in the current working directory (excluding those in the `.gitignore`). These files and directories are shown to the GPT model for providing relevant assistance.
- **Run Python Code**: Execute Python code snippets directly in the terminal.

## Prerequisites

- Python 3.7 or higher
- pip (Python Package Installer)
- OpenAI API key

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/Munkyfoot/ai-terminal.git
   ```

2. Navigate to the project directory:

   ```bash
   cd ai-terminal
   ```

3. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

4. Activate the virtual environment:

   - For Linux/macOS:

     ```bash
     source venv/bin/activate
     ```

   - For Windows:

     ```batch
     venv\Scripts\activate
     ```

5. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

6. Rename `.env.example` to `.env`:

   - For Linux/macOS:

     ```bash
     mv .env.example .env
     ```

   - For Windows:

     ```batch
     rename .env.example .env
     ```

7. Add your OpenAI API key in the `.env` file:

   ```env
   OPENAI_API_KEY="YOUR_API_KEY"
   ```

## Usage

To run AI Terminal, use the following command:

```bash
python main.py [query] [flags]
```

### Options:

- `query` (optional): Initial query to start the conversation.
- `flags`:
  - `--memory` or `-m`: Save/load conversation history to add long-term memory to the conversation.
  - `--ls` or `-l`: Show files and directories in the current working directory.
  - `--always-allow` or `-a`: Always allow file operations without confirmation.
  - `--save-defaults` or `-S`: Save the current flag values as defaults for future runs.
  - `--reset-defaults` or `-R`: Reset the flags to their original defaults.

### Examples:

1. **Start AI Terminal without an initial query:**

   ```bash
   python main.py
   ```

2. **Provide an initial query:**

   ```bash
   python main.py "How can I list files in a directory?"
   ```

3. **Use memory to save/load conversation history:**

   ```bash
   python main.py "Do you remember our previous conversation?" --memory
   ```

4. **Show files and directories to the GPT model for assistance:**

   ```bash
   python main.py "What files are present in the current directory?" --ls
   ```

5. **Always allow file operations without confirmation:**

   ```bash
   python main.py "Write a file named 'test.txt' with the content 'Hello, World!'" --always-allow
   ```

6. **Save the current flag values as defaults:**

   ```bash
   python main.py --ls --memory --save-defaults
   ```

7. **Reset the flags to their original defaults:**

   ```bash
   python main.py --reset-defaults
   ```

## Setting Up for Command Line Alias (`ask`)

### Linux/macOS

1. Open your `.bashrc` or `.zshrc` file:

   ```bash
   nano ~/.bashrc
   ```

   Or for zsh:

   ```bash
   nano ~/.zshrc
   ```

2. Add the following lines to create an alias that activates the virtual environment, runs the command, and then deactivates the virtual environment:

   ```bash
   alias ask='source /path/to/your/project/venv/bin/activate && python /path/to/your/project/main.py "$@" && deactivate'
   ```

3. Save the file and reload the shell configuration:

   ```bash
   source ~/.bashrc
   ```

   Or for zsh:

   ```bash
   source ~/.zshrc
   ```

### Windows

1. Open the Command Prompt as an Administrator and run:

   ```batch
   setx PATH "%PATH%;C:\path\to\your\project"
   ```

2. Create a batch file named `ask.bat` in a directory included in your system `PATH`. Ensure it activates the virtual environment, runs the command, and then deactivates the virtual environment:

   ```batch
   echo @echo off > C:\path\to\your\project\ask.bat
   echo call C:\path\to\your\project\venv\Scripts\activate >> C:\path\to\your\project\ask.bat
   echo python C:\path\to\your\project\main.py %* >> C:\path\to\your\project\ask.bat
   echo call C:\path\to\your\project\venv\Scripts\deactivate >> C:\path\to\your\project\ask.bat
   ```

Now you can use the `ask` command from any location in the terminal:

```bash
ask "How can I list files in a directory?" --memory --ls
```

### Examples:

1. Start AI Terminal without an initial query:

   ```bash
   ask
   ```

2. Ask a general question:

   ```bash
   ask "What is the weather like today?"
   ```

3. Use memory flag:

   ```bash
   ask "Do you remember my previous question?" --memory
   ```

4. Show files and directories:

   ```bash
   ask "What files are present in the current directory?" --ls
   ```

5. Always allow file operations without confirmation:

   ```bash
   ask "Write a file named 'test.txt' with the content 'Hello, World!'" --always-allow
   ```

6. Save the current flag values as defaults:

   ```bash
   ask --ls --memory --save-defaults
   ```

7. Reset the flags to their original defaults:

   ```bash
   ask --reset-defaults
   ```

## Contributing

1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a pull request.

## License

Distributed under the MIT License. See `LICENSE` for more information.
