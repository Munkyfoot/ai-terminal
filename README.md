# AI Terminal

AI Terminal is a Python-based command-line interface (CLI) tool that allows you to interact with OpenAI's models, providing a convenient and direct way to chat with an AI and get assistance with various tasks. This includes support for terminal commands, coding help, and other queries. The application provides function calling for file operations, based on user interactions.

## Features

- Direct interaction with OpenAI's AI models from your terminal
- Supports terminal commands specific to your platform (Windows, macOS, or Linux)
- Coding assistance and guidance
- Optional conversation history saving to improve responses over time
- File operations support, enabling file writing and reading based on user interactions
- Flexibility to switch between different AI models for tailored responses
- Ability to show files and directories in the current working directory (except those specified in the .gitignore file)

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

```bash
mv .env.example .env
```

- Then open the `.env` file in a text editor and add your OpenAI API key:

```
OPENAI_API_KEY="YOUR_API_KEY"
```

## Usage

To run AI Terminal, use the following command:

```bash
python main.py [query] [flags]
```

- `query`: Optional initial query to start the conversation
- `flags`:
  - `--memory` or `-m`: Save/load conversation history to add long-term memory to the conversation
  - `--ls` or `-l`: Show files and directories in the current working directory

You can run the following example commands:

```bash
python main.py
```

```bash
python main.py "How can I list files in a directory?"
```

```bash
python main.py "How can I list files in a directory?" --memory
```

```bash
python main.py "How can I list files in a directory?" --memory --ls
```
