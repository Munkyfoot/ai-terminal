import json
import logging
import os
import sys
from enum import Enum
from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI

# Set up logging - save logs to a file
logging.basicConfig(
    filename="debug.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Load environment variables from .env file
load_dotenv()

# Constants
MEMORY_FILE = "memory.json"
MEMORY_MAX = 24  # Used to limit the number of messages stored in memory (applies to short and long-term memory)

# User's platform and environment information
USER_PLATFORM = sys.platform

if USER_PLATFORM == "win32":
    USER_ENV = os.environ.get("COMSPEC")
else:
    USER_ENV = os.environ.get("SHELL", "unknown")

USER_CWD = os.getcwd()

USER_INFO = f"""User's Information:
- Platform: {USER_PLATFORM}
- Environment: {USER_ENV}
- Current Working Directory: {USER_CWD}
"""


def get_files_dirs(use_gitignore=True, ignore_all_hidden=False):
    output = []

    # Read .gitignore file if use_gitignore is True
    gitignore_entries = set()
    if use_gitignore:
        gitignore_path = os.path.join(USER_CWD, ".gitignore")
        if os.path.isfile(gitignore_path):
            with open(gitignore_path, "r") as file:
                gitignore_entries = {line.strip() for line in file}

    # Helper function to check if an item should be excluded based on .gitignore
    def is_excluded(item_path):
        rel_path = os.path.relpath(item_path, USER_CWD)
        rel_path = os.path.normpath(rel_path).replace(os.sep, "/")
        if rel_path in gitignore_entries or f"{rel_path}/" in gitignore_entries:
            return True
        return any(
            entry.endswith("/") and rel_path.startswith(entry)
            for entry in gitignore_entries
        )

    # Helper function to build the file tree
    def tree(dir_path, indent=""):
        try:
            dir_content = [
                item
                for item in os.listdir(dir_path)
                if not item.startswith(".git")
                and (not ignore_all_hidden or not item.startswith("."))
            ]
            dir_content.sort()
            for item in dir_content:
                item_path = os.path.join(dir_path, item)
                if not is_excluded(item_path):
                    rel_path = os.path.relpath(item_path, USER_CWD)
                    rel_path = os.path.normpath(rel_path).replace(os.sep, "/")
                    if os.path.isdir(item_path):
                        output.append(f"{indent}{rel_path}/")
                        tree(item_path, indent + "  ")
                    else:
                        output.append(f"{indent}{rel_path}")
        except PermissionError:
            output.append(f"{indent}Permission denied: {dir_path}")

    # Start building the tree from the current working directory
    tree(USER_CWD)

    return "\n".join(output)


def write_file(file_path, content):
    print(
        f"{PrintStyle.CYAN.value}Writing to file '{file_path}'...{PrintStyle.RESET.value}"
    )
    file_path = os.path.join(USER_CWD, file_path)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as file:
        file.write(content)
    return f"File '{file_path}' written successfully."


def read_file(file_path):
    print(
        f"{PrintStyle.CYAN.value}Reading file '{file_path}'...{PrintStyle.RESET.value}"
    )
    file_path = os.path.join(USER_CWD, file_path)
    try:
        with open(file_path, "r") as file:
            content = file.read()
        return f"Content of file '{file_path}':\n\n{content}"
    except FileNotFoundError:
        return f"File '{file_path}' not found."


FILE_WRITER_TOOL = {
    "type": "function",
    "function": {
        "name": "file_writer",
        "description": "Writes content to a file at the specified path relative to the current working directory, creating directories if necessary.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The path of the file to create (relative to the current working directory).",
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file.",
                },
            },
            "required": ["file_path", "content"],
        },
    },
}

FILE_READER_TOOL = {
    "type": "function",
    "function": {
        "name": "file_reader",
        "description": "Reads the content of a file at the specified path relative to the current working directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The path of the file to read (relative to the current working directory).",
                },
            },
            "required": ["file_path"],
        },
    },
}


class Agent:
    def __init__(
        self,
        model: Literal["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"] = "gpt-4-turbo",
        use_memory=False,
        view_list_dir=False,
    ) -> None:
        self.client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
        self.model = model
        self.use_memory = use_memory
        self.chat = []
        if self.use_memory:
            self.load_memory()
        self.view_list_dir = view_list_dir
        self.system_prompt = f"Your primary function is to assist the user with tasks related to terminal commands in their respective platform. You can also help with code and other queries. Information about the user's platform, environment, and current working directory is provided below.\n\n{USER_INFO}"

    def get_tool_call_message(self, tool_call):
        tool_name = tool_call["tool_name"]
        args = json.loads(tool_call["args_json"])
        if tool_name == "file_writer":
            file_name = args["file_path"]
            content = args["content"]
            return f"GPT wants to create the file '{file_name}' with this content:\n\n{content}"
        elif tool_name == "file_reader":
            file_name = args["file_path"]
            return f"GPT wants to open and read '{file_name}'"
        else:
            return ""

    def process_tool_call(self, tool_call):
        tool_name = tool_call["tool_name"]
        args = json.loads(tool_call["args_json"])
        if tool_name == "file_writer":
            file_name = args["file_path"]
            content = args["content"]
            result = write_file(file_name, content)
        elif tool_name == "file_reader":
            file_name = args["file_path"]
            result = read_file(file_name)
        else:
            return False

        return result

    def run(self, query: str) -> None:
        self.chat.append({"role": "user", "content": query})

        full_system_prompt = f"""{self.system_prompt}"""

        if self.view_list_dir:
            files_tree = get_files_dirs()
            full_system_prompt += f"\n\nHere's a list of files and directories in the current working directory:\n\n{files_tree}"

        if self.use_memory:
            _messages = self.memory + self.chat
        else:
            _messages = self.chat

        _messages = _messages[-MEMORY_MAX:]

        stream = self.client.chat.completions.create(
            max_tokens=4096,
            messages=[
                {
                    "role": "system",
                    "content": full_system_prompt,
                }
            ]
            + _messages,
            model=self.model,
            tools=[
                FILE_WRITER_TOOL,
                FILE_READER_TOOL,
            ],
            stream=True,
        )

        text_stream_content = ""
        tool_calls = {}
        tool_call_detected = False
        for chunk in stream:
            if chunk.choices[0].delta.tool_calls:
                for tool_call in chunk.choices[0].delta.tool_calls:
                    tool_call_detected = True
                    if tool_call.index not in tool_calls:
                        tool_calls[tool_call.index] = {
                            "tool_name": tool_call.function.name,
                            "args_json": "",
                        }

                        if text_stream_content:
                            print("")

                        print(
                            f"{PrintStyle.CYAN.value}Building tool call...{PrintStyle.RESET.value}"
                        )

                    tool_calls[tool_call.index][
                        "args_json"
                    ] += tool_call.function.arguments

            text = chunk.choices[0].delta.content
            if text:
                text_stream_content += text

                print(text, end="", flush=True)
        if text_stream_content and not tool_call_detected:
            print("")

        if tool_call_detected:
            for index, tool_call in tool_calls.items():
                print(
                    f"{PrintStyle.CYAN.value}{self.get_tool_call_message(tool_call)}{PrintStyle.RESET.value}"
                )
                tool_confirmation = input(
                    f"{PrintStyle.MAGENTA.value}Allow? (y/[n]): {PrintStyle.RESET.value}"
                )
                if tool_confirmation.lower() == "y":
                    try:
                        print(
                            f"{PrintStyle.CYAN.value}Executing tool...{PrintStyle.RESET.value}"
                        )
                        tool_result = self.process_tool_call(tool_call)
                        if tool_result:
                            text_stream_content += f"\n\n{tool_result}"
                        print(
                            f"{PrintStyle.GREEN.value}Tool executed successfully.{PrintStyle.RESET.value}"
                        )
                    except Exception as e:
                        print(
                            f"{PrintStyle.RED.value}Error executing tool: {e}{PrintStyle.RESET.value}"
                        )
                else:
                    print(
                        f"{PrintStyle.YELLOW.value}Cancelled {tool_call['tool_name']}.{PrintStyle.RESET.value}"
                    )

        message = text_stream_content
        if message:
            self.chat.append({"role": "assistant", "content": message})

        if self.use_memory:
            self.save_memory()

    def save_memory(self) -> None:
        memory = (self.memory + self.chat)[-MEMORY_MAX:]
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f)

    def load_memory(self) -> None:
        self.chat = []
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r") as f:
                self.memory = json.load(f)
        else:
            self.memory = []


class PrintStyle(Enum):
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    INVERT = "\033[7m"
    STRIKETHROUGH = "\033[9m"
    BOLD_END = "\033[21m"
    UNDERLINE_END = "\033[24m"
    INVERT_END = "\033[27m"
    STRIKETHROUGH_END = "\033[29m"
    RESET = "\033[0m"


# User's input style prefix
USER_STYLE_PREFIX = f"{PrintStyle.BLUE.value}"
