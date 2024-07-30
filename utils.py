import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Literal

from anthropic import Anthropic
from dotenv import load_dotenv
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_random_exponential

# Load environment variables from the .env file
load_dotenv()

# Constants
MEMORY_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "memory.json"))
MAX_MESSAGES = 24  # Limit for messages stored in chat history

# User's platform and environment information
USER_PLATFORM = sys.platform
USER_ENV = (
    os.environ.get("COMSPEC")
    if USER_PLATFORM == "win32"
    else os.environ.get("SHELL", "unknown")
)
USER_CWD = os.getcwd()
USER_INFO = f"""User's Information:
- Platform: {USER_PLATFORM}
- Environment: {USER_ENV}
- Current Working Directory: {USER_CWD}
"""


# Enum for console text styles
class PrintStyle(Enum):
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    GRAY = "\033[90m"
    WHITE = "\033[37m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_GRAY = "\033[90m"
    BRIGHT_WHITE = "\033[97m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    INVERT = "\033[7m"
    STRIKETHROUGH = "\033[9m"
    BOLD_END = "\033[21m"
    UNDERLINE_END = "\033[24m"
    INVERT_END = "\033[27m"
    STRIKETHROUGH_END = "\033[29m"
    RESET = "\033[0m"


# Patterns and their corresponding ANSI color codes
HIGHLIGHT_PATTERNS = [
    (
        r"\b(def|class|lambda|True|False|None)\b",
        PrintStyle.BLUE.value,
    ),  # Keywords
    (
        r"\b(if|elif|else|try|except|finally|for|while|break|continue|return|import|from|as|pass|raise|with|yield|and|or|not|is|in)\b",
        PrintStyle.MAGENTA.value,
    ),  # Keywords
    (
        r"\b(int|float|str|list|dict|set|tuple|bool|bytes|object|type|super|range|print|len|input|open|exec|eval|dir|vars|locals|globals|staticmethod|classmethod|property|Exception|BaseException|AssertionError|AttributeError|EOFError|FloatingPointError|GeneratorExit|ImportError|IndexError|KeyError|KeyboardInterrupt|MemoryError|NameError|NotImplementedError|OSError|OverflowError|ReferenceError|RuntimeError|StopIteration|SyntaxError|IndentationError|TabError|SystemError|SystemExit|TypeError|UnboundLocalError|ValueError|ZeroDivisionError)\b",
        PrintStyle.GREEN.value,
    ),  # Built-in functions and exceptions
    (
        r"(?<=\s|\.)[a-zA-Z_][a-zA-Z0-9_]*(?=\()",
        PrintStyle.YELLOW.value,
    ),  # Catch all function calls
    (
        r"(\"\"\".*?\"\"\"|\'\'\'.*?\'\'\')",
        PrintStyle.RED.value,
    ),  # Triple-quoted strings
    (
        r"(\".*?\"|\'.*?\')",
        PrintStyle.RED.value,
    ),  # Single or double-quoted strings
    (
        r"#.*",
        PrintStyle.GREEN.value,
    ),  # Comments
    (
        r"\b([A-Z_][A-Z0-9_]*)\b",
        PrintStyle.BOLD.value,
    ),  # Constants in uppercase
]


def remove_ansi_escape_sequences(text):
    """
    Removes ANSI escape sequences from a text.

    Args:
        text (str): The text containing ANSI escape sequences.

    Returns:
        str: The text with ANSI escape sequences removed.
    """
    return re.sub(r"\033\[[0-9;]*m", "", text)


# Function to apply highlighting to code
def highlight_code(code):
    for pattern, color in HIGHLIGHT_PATTERNS:
        code = re.sub(
            pattern,
            lambda match: f"{color}{remove_ansi_escape_sequences(match.group(0))}{PrintStyle.RESET.value}",
            code,
        )
    return code


# User's input style prefix
USER_STYLE_PREFIX = f"{PrintStyle.BRIGHT_BLUE.value}"


def load_gitignore_entries(use_gitignore):
    """
    Loads entries from the .gitignore file if it exists.

    Args:
        use_gitignore (bool): Flag to indicate whether to read the .gitignore file.

    Returns:
        set: A set of entries from the .gitignore file.
    """
    gitignore_entries = set()
    if use_gitignore:
        gitignore_path = os.path.join(USER_CWD, ".gitignore")
        if os.path.isfile(gitignore_path):
            with open(gitignore_path, "r") as file:
                gitignore_entries = {line.strip() for line in file}
    return gitignore_entries


def is_excluded(item_path, gitignore_entries):
    """
    Checks if a file/directory should be excluded based on .gitignore entries.

    Args:
        item_path (str): The path of the item to check.
        gitignore_entries (set): A set of .gitignore entries.

    Returns:
        bool: True if the item should be excluded, False otherwise.
    """
    rel_path = os.path.relpath(item_path, USER_CWD)
    rel_path = os.path.normpath(rel_path).replace(os.sep, "/")
    if rel_path in gitignore_entries or f"{rel_path}/" in gitignore_entries:
        return True
    return any(
        entry.endswith("/") and rel_path.startswith(entry)
        for entry in gitignore_entries
    )


def get_files_dirs(use_gitignore=True, ignore_all_hidden=False, max_depth=1):
    """
    Builds a list of files and directories in the current working directory.

    Args:
        use_gitignore (bool): Whether to respect the .gitignore file.
        ignore_all_hidden (bool): Whether to ignore all hidden files and directories.
        max_depth (int): Maximum depth of the directory tree to traverse.

    Returns:
        str: A formatted string representing the file tree.
    """
    output = []
    gitignore_entries = load_gitignore_entries(use_gitignore)

    def tree(dir_path, indent="", current_depth=0):
        if current_depth > max_depth:
            return

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
                if not is_excluded(item_path, gitignore_entries):
                    rel_path = os.path.relpath(item_path, USER_CWD)
                    rel_path = os.path.normpath(rel_path).replace(os.sep, "/")
                    if os.path.isdir(item_path):
                        output.append(f"{indent}{rel_path}/")
                        tree(item_path, indent + "  ", current_depth + 1)
                    else:
                        output.append(f"{indent}{rel_path}")
        except PermissionError:
            output.append(f"{indent}Permission denied: {dir_path}")

    # Start building the tree from the current working directory
    tree(USER_CWD)

    return "\n".join(output)


def write_file(file_path, content, append=False):
    """
    Writes content to a file, creating directories if necessary.

    Args:
        file_path (str): The path of the file to write (relative to the current working directory).
        content (str): The content to write to the file.
        append (bool): Whether to append to the file instead of overwriting it.

    Returns:
        str: A success message indicating that the file was written successfully.
    """
    print(
        f"{PrintStyle.BRIGHT_CYAN.value}Writing to file '{file_path}'...{PrintStyle.RESET.value}"
    )
    file_path = os.path.join(USER_CWD, file_path)
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        mode = "a" if append else "w"
        with open(file_path, mode, encoding="utf-8") as file:
            file.write(content)
        return f"File '{file_path}' written successfully."
    except:
        return f"Error writing to file '{file_path}'."


def read_file(file_path):
    """
    Reads the content of a file.

    Args:
        file_path (str): The path of the file to read (relative to the current working directory).

    Returns:
        str: The content of the file or an error message if the file is not found.
    """
    print(
        f"{PrintStyle.BRIGHT_CYAN.value}Reading file '{file_path}'...{PrintStyle.RESET.value}"
    )
    file_path = os.path.join(USER_CWD, file_path)
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return f"Content of file '{file_path}':\n\n{content}"
    except FileNotFoundError:
        return f"Error: File '{file_path}' not found."


def run_python_code(code):
    """
    Executes Python code and returns the output.

    Args:
        code (str): The Python code to execute.

    Returns:
        str: The output of the Python code execution.
    """
    print(
        f"{PrintStyle.BRIGHT_CYAN.value}Executing Python code...{PrintStyle.RESET.value}"
    )
    try:
        abs_dir = os.path.abspath(os.path.dirname(__file__))
        if USER_PLATFORM == "win32":
            python_path = os.path.join(abs_dir, "venv", "Scripts", "python.exe")
        else:
            python_path = os.path.join(abs_dir, "venv", "bin", "python")
        output = subprocess.check_output(
            [python_path, "-c", code],
            stderr=subprocess.STDOUT,
            text=True,
        )
        return (
            f"Python code executed successfully.\n\nOutput:\n\n{output}"
            if output
            else "Python code executed successfully."
        )
    except subprocess.CalledProcessError as e:
        return f"Error executing Python code:\n\n{e.output}"


class Agent:
    """Agent for handling user queries related to terminal commands and other tasks."""

    def __init__(
        self,
        model: Literal[
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "claude-3-5-sonnet-20240620",
        ] = "gpt-4o",
        use_memory=False,
        view_list_dir=False,
        always_allow=False,
    ) -> None:
        self.model = model if model else "gpt-4o"
        if self.model.startswith("claude"):
            self.api = "anthropic"
            self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        elif self.model.startswith("gpt"):
            self.api = "openai"
            self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        self.chat = []

        self.use_memory = use_memory

        self.view_list_dir = view_list_dir
        self.always_allow = always_allow

        self.system_prompt = (
            f"Your primary function is to assist the user with tasks related to terminal commands in their respective platform. You can also help with code and other queries. Information about the user's platform, environment, and current working directory is provided below.\n\n{USER_INFO}"
            + "\n\nTool Calls:\nIf you're asked to perform a task that requires writing to the file system, reading from a file, or executing Python code, use the tool directly to perform the task. Do not ask for permission first. Perform any tasks that require a tool call immediately, without responding to the user first, unless absolutely necessary for clarification."
        )

        self._failed_tool_calls = 0

    def is_valid_tool_call(self, tool_call):
        """
        Checks if a tool call is valid.

        Args:
            tool_call (dict): Tool call information.

        Returns:
            bool: True if the tool call is valid, False otherwise.
            str: An error message if the tool call is invalid.
        """
        if tool_call["tool_name"] not in [
            "file_writer",
            "file_reader",
            "python_executor",
            "save_memory",
            "remove_memory",
        ]:
            return (
                False,
                "Invalid tool name. The tool name must be one of 'file_writer', 'file_reader', 'python_executor', 'save_memory', or 'remove_memory'.",
            )

        try:
            if self.api == "anthropic":
                args = tool_call["args_json"]
            elif self.api == "openai":
                args = json.loads(tool_call["args_json"])
        except:
            return (
                False,
                "Error decoding arguments. Ensure the arguments are in valid JSON format.",
            )

        if tool_call["tool_name"] == "file_writer":
            if "file_path" not in args or "content" not in args or "append" not in args:
                return (
                    False,
                    "Missing required arguments. 'file_path', 'content' and 'append' are required arguments for the 'file_writer' tool. If you receive this error repeatedly, it may be because the content is too large. Try reducing the content size - you can break it up into multiple tool calls if necessary.",
                )
        elif tool_call["tool_name"] == "file_reader":
            if "file_path" not in args:
                return (
                    False,
                    "Missing required argument. 'file_path' is a required argument for the 'file_reader' tool.",
                )
        elif tool_call["tool_name"] == "python_executor":
            if "code" not in args:
                return (
                    False,
                    "Missing required argument. 'code' is a required argument for the 'python_executor' tool. If you receive this error repeatedly, it may be because the code is too large. Try reducing the code size.",
                )
        elif tool_call["tool_name"] == "save_memory":
            if "content" not in args:
                return (
                    False,
                    "Missing required argument. 'content' is a required argument for the 'save_memory' tool.",
                )
        elif tool_call["tool_name"] == "remove_memory":
            if "index" not in args:
                return (
                    False,
                    "Missing required argument. 'index' is a required argument for the 'remove_memory' tool.",
                )

        return True, ""

    def get_tool_call_message(self, tool_call):
        """
        Generates a message for a tool call.

        Args:
            tool_call (dict): Tool call information.

        Returns:
            str: A formatted message describing the tool call.
        """
        tool_name = tool_call["tool_name"]
        if self.api == "anthropic":
            args = tool_call["args_json"]
        elif self.api == "openai":
            args = json.loads(tool_call["args_json"])

        if tool_name == "file_writer":
            file_name = args["file_path"]
            content = args["content"]
            append = bool(args["append"])
            if append:
                return f"{PrintStyle.WHITE.value}{content}\n\n{PrintStyle.BRIGHT_CYAN.value}GPT wants to append the content to the file '{file_name}'.{PrintStyle.RESET.value}"
            else:
                return f"{PrintStyle.WHITE.value}{content}\n\n{PrintStyle.BRIGHT_CYAN.value}GPT wants to create the file '{file_name}' with this content.{PrintStyle.RESET.value}"
        elif tool_name == "file_reader":
            file_name = args["file_path"]
            return f"{PrintStyle.BRIGHT_CYAN.value}GPT wants to open and read '{file_name}'.{PrintStyle.RESET.value}"
        elif tool_name == "python_executor":
            code = highlight_code(args["code"])
            return f"{code}\n\n{PrintStyle.BRIGHT_CYAN.value}GPT wants to execute the above Python code.{PrintStyle.RESET.value}"
        elif tool_name == "save_memory":
            content = args["content"]
            return f"{PrintStyle.WHITE.value}{content}\n\n{PrintStyle.BRIGHT_CYAN.value}GPT wants to store this information in memory for future reference.{PrintStyle.RESET.value}"
        elif tool_name == "remove_memory":
            index = args["index"]
            return f"{PrintStyle.BRIGHT_CYAN.value}GPT wants to remove the memory item at index {index}.{PrintStyle.RESET.value}"
        else:
            return ""

    def process_tool_call(self, tool_call):
        """
        Processes a tool call and executes the corresponding function.

        Args:
            tool_call (dict): Tool call information.

        Returns:
            str: The result of the tool execution.
        """
        tool_name = tool_call["tool_name"]
        if self.api == "anthropic":
            args = tool_call["args_json"]
        elif self.api == "openai":
            args = json.loads(tool_call["args_json"])
        if tool_name == "file_writer":
            file_name = args["file_path"]
            content = args["content"]
            append = bool(args["append"])
            result = write_file(file_name, content, append)
        elif tool_name == "file_reader":
            file_name = args["file_path"]
            result = read_file(file_name)
        elif tool_name == "python_executor":
            code = args["code"]
            result = run_python_code(code)
        elif tool_name == "save_memory":
            content = args["content"]
            self.save_memory(content)
            result = f"Stored in memory: {content}"
        elif tool_name == "remove_memory":
            index = args["index"]
            self.remove_memory(index)
            result = f"Removed memory item at index {index}."
        else:
            return ""

        return result

    def format_tool(self, tool):
        """
        Formats the tool for the current API.

        Args:
            tool (dict): The tool to format.

        Returns:
            dict: The formatted tool.
        """

        if self.api == "anthropic":
            formatted_tool = {
                "name": tool["function"]["name"],
                "description": tool["function"]["description"],
                "input_schema": tool["function"]["parameters"],
            }
        elif self.api == "openai":
            formatted_tool = tool

        return formatted_tool

    def run(self, query: str = "") -> None:
        """
        Runs the agent with the provided user query.

        Args:
            query (str): The user's query.
        """
        if query != "":
            self.chat.append({"role": "user", "content": query})
        full_system_prompt = f"""{self.system_prompt}"""

        if self.view_list_dir:
            files_tree = get_files_dirs()
            full_system_prompt += f"\n\nHere's a list of files and directories in the current working directory:\n\n{files_tree}"

        if self.use_memory:
            memories = self.load_memory()
            if memories:
                full_system_prompt += f"\n\nMemories:\n\n"
                for i, memory in enumerate(memories):
                    full_system_prompt += f"#{i} -> {memory}\n\n"

        _messages = self.chat[-MAX_MESSAGES:]

        while _messages and _messages[0]["role"] != "user":
            _messages.pop(0)

        @retry(
            wait=wait_random_exponential(min=2, max=60),
            stop=stop_after_attempt(3),
            after=lambda retry_state: print(
                f"{PrintStyle.BRIGHT_YELLOW.value}⚠ Unable to get response. Trying again... (Attempt {retry_state.attempt_number}/3){PrintStyle.RESET.value}"
            ),
            reraise=True,
        )
        def get_stream():
            tools = [
                self.format_tool(FILE_WRITER_TOOL),
                self.format_tool(FILE_READER_TOOL),
                self.format_tool(PYTHON_EXECUTOR_TOOL),
            ]
            if self.use_memory:
                tools.append(self.format_tool(SAVE_MEMORY_TOOL))
                tools.append(self.format_tool(REMOVE_MEMORY_TOOL))

            if self.api == "anthropic":
                stream = self.client.messages.stream(
                    max_tokens=4096,
                    system=full_system_prompt,
                    messages=_messages,
                    model=self.model,
                    tools=tools,
                )
            elif self.api == "openai":
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
                    tools=tools,
                    stream=True,
                )
            return stream

        try:
            stream = get_stream()
        except Exception as e:
            print(
                f"{PrintStyle.BRIGHT_RED.value}⚠ Error getting response: {e}{PrintStyle.RESET.value}"
            )
            return

        text_stream_content = ""
        tool_calls = {}
        tool_call_detected = False

        if self.api == "anthropic":
            with stream as claude_stream:
                for text in claude_stream.text_stream:
                    text = text if text_stream_content else text.strip()
                    if text:
                        text_stream_content += text
                        print(text, end="", flush=True)

                final_message_content = claude_stream.get_final_message().content
                tool_uses = [
                    {
                        "tool_call_id": content.id,
                        "tool_name": content.name,
                        "args_json": content.input,
                    }
                    for content in final_message_content
                    if content.type == "tool_use"
                ]

            if tool_uses:
                tool_call_detected = True
                for i, tool_use in enumerate(tool_uses):
                    tool_calls[i] = tool_use

            response_message = {
                "role": "assistant",
                "content": [],
            }

            if text_stream_content:
                response_message["content"].append(
                    {
                        "type": "text",
                        "text": text_stream_content,
                    }
                )

            if tool_call_detected:
                for index, tool_call in tool_calls.items():
                    response_message["content"].append(
                        {
                            "id": tool_call["tool_call_id"],
                            "type": "tool_use",
                            "name": tool_call["tool_name"],
                            "input": tool_call["args_json"],
                        }
                    )

        elif self.api == "openai":
            for chunk in stream:
                if chunk.choices[0].delta.tool_calls:
                    for tool_call in chunk.choices[0].delta.tool_calls:
                        tool_call_detected = True
                        if tool_call.index not in tool_calls:
                            tool_calls[tool_call.index] = {
                                "tool_call_id": tool_call.id,
                                "tool_name": tool_call.function.name,
                                "args_json": "",
                            }

                        tool_calls[tool_call.index][
                            "args_json"
                        ] += tool_call.function.arguments

                text = chunk.choices[0].delta.content
                if text:
                    text = text if text_stream_content else text.strip()
                    text_stream_content += text
                    print(text, end="", flush=True)

            response_message = {
                "role": "assistant",
                "content": text_stream_content,
            }
            if tool_call_detected:
                response_message["tool_calls"] = []
                for index, tool_call in tool_calls.items():
                    response_message["tool_calls"].append(
                        {
                            "id": tool_call["tool_call_id"],
                            "type": "function",
                            "function": {
                                "name": tool_call["tool_name"],
                                "arguments": tool_call["args_json"],
                            },
                        }
                    )

        if text_stream_content:
            print("", flush=True)

        self.chat.append(response_message)

        if tool_call_detected:
            has_failed = (
                False  # Flag to indicate if a tool call has failed at least once
            )
            for index, tool_call in tool_calls.items():
                valid_tool_call, error_message = self.is_valid_tool_call(tool_call)
                if valid_tool_call:
                    self._failed_tool_calls = 0

                    if not self.always_allow:
                        print(
                            f"{PrintStyle.BRIGHT_CYAN.value}{self.get_tool_call_message(tool_call)}{PrintStyle.RESET.value}",
                            end=" ",
                        )
                        tool_confirmation = input(
                            f"{PrintStyle.BRIGHT_MAGENTA.value}Allow?\n[y or yes to confirm else cancel with optional message]: {PrintStyle.RESET.value}"
                        )
                    if self.always_allow or tool_confirmation.lower() in ["y", "yes"]:
                        try:
                            tool_result = self.process_tool_call(tool_call)
                            if tool_result:
                                text_stream_content += f"\n\n{tool_result}"

                            if tool_result.startswith("Error"):
                                print(
                                    f"{PrintStyle.BRIGHT_YELLOW.value}⚠ Something went wrong.{PrintStyle.RESET.value}"
                                )
                            else:
                                print(
                                    f"{PrintStyle.BRIGHT_GREEN.value}✔ Tool executed successfully.{PrintStyle.RESET.value}"
                                )

                            if self.api == "anthropic":
                                self.chat.append(
                                    {
                                        "role": "user",
                                        "content": [
                                            {
                                                "type": "tool_result",
                                                "tool_use_id": tool_call[
                                                    "tool_call_id"
                                                ],
                                                "content": tool_result,
                                                "is_error": tool_result.startswith(
                                                    "Error"
                                                ),
                                            }
                                        ],
                                    }
                                )
                            elif self.api == "openai":
                                self.chat.append(
                                    {
                                        "tool_call_id": tool_call["tool_call_id"],
                                        "role": "tool",
                                        "name": tool_call["tool_name"],
                                        "content": tool_result,
                                    }
                                )
                        except Exception as e:
                            print(
                                f"{PrintStyle.BRIGHT_RED.value}⚠ Error executing tool: {e}{PrintStyle.RESET.value}"
                            )

                            if self.api == "anthropic":
                                self.chat.append(
                                    {
                                        "role": "user",
                                        "content": [
                                            {
                                                "type": "tool_result",
                                                "tool_use_id": tool_call[
                                                    "tool_call_id"
                                                ],
                                                "content": f"Error executing tool: {e}",
                                                "is_error": True,
                                            }
                                        ],
                                    }
                                )
                            elif self.api == "openai":
                                self.chat.append(
                                    {
                                        "tool_call_id": tool_call["tool_call_id"],
                                        "role": "tool",
                                        "name": tool_call["tool_name"],
                                        "content": f"Error executing tool: {e}",
                                    }
                                )
                    else:
                        print(
                            f"{PrintStyle.BRIGHT_YELLOW.value}✖ Cancelled {tool_call['tool_name']}.{PrintStyle.RESET.value}"
                        )

                        if self.api == "anthropic":
                            response_content = [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_call["tool_call_id"],
                                    "content": "User cancelled the tool execution.",
                                    "is_error": True,
                                }
                            ]
                            if tool_confirmation:
                                response_content.append(
                                    {
                                        "type": "text",
                                        "text": tool_confirmation,
                                    }
                                )
                            self.chat.append(
                                {
                                    "role": "user",
                                    "content": response_content,
                                }
                            )
                        elif self.api == "openai":
                            self.chat.append(
                                {
                                    "tool_call_id": tool_call["tool_call_id"],
                                    "role": "tool",
                                    "name": tool_call["tool_name"],
                                    "content": f"""User cancelled the tool execution.{
                                        f' User Message: {tool_confirmation}' if tool_confirmation else ''
                                    }""",
                                }
                            )
                else:
                    if self._failed_tool_calls < 3:
                        # Only increment the failed tool calls counter once per response
                        if not has_failed:
                            self._failed_tool_calls += (
                                1  # Increment the failed tool calls counter
                            )
                            has_failed = True

                        print(
                            f"{PrintStyle.BRIGHT_YELLOW.value}⚠ Error using {tool_call['tool_name']} tool. Trying again... (Attempt {self._failed_tool_calls}/3){PrintStyle.RESET.value}"
                        )
                        if self.api == "anthropic":
                            self.chat.append(
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "tool_result",
                                            "tool_use_id": tool_call["tool_call_id"],
                                            "content": error_message,
                                            "is_error": True,
                                        }
                                    ],
                                }
                            )
                        elif self.api == "openai":
                            self.chat.append(
                                {
                                    "tool_call_id": tool_call["tool_call_id"],
                                    "role": "tool",
                                    "name": tool_call["tool_name"],
                                    "content": error_message,
                                }
                            )
                    else:
                        print(
                            f"{PrintStyle.BRIGHT_RED.value}⚠ Unable to use {tool_call['tool_name']} tool. Maximum attempts reached.{PrintStyle.RESET.value}"
                        )
                        if self.api == "anthropic":
                            self.chat.append(
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "tool_result",
                                            "tool_use_id": tool_call["tool_call_id"],
                                            "content": "Tool use failed again. Maximum attempts reached. Do not retry.",
                                            "is_error": True,
                                        }
                                    ],
                                }
                            )
                        elif self.api == "openai":
                            self.chat.append(
                                {
                                    "tool_call_id": tool_call["tool_call_id"],
                                    "role": "tool",
                                    "name": tool_call["tool_name"],
                                    "content": "Tool use failed again. Maximum attempts reached. Do not retry.",
                                }
                            )

        if tool_call_detected:
            self.run()

    def load_memory(self) -> None:
        """
        Loads the conversation memory from a file.
        """
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r") as f:
                memories = json.load(f)
                if isinstance(memories, list):
                    if len(memories) > 0:
                        if isinstance(memories[0], str):
                            return memories
        return []

    def save_memory(self, memory) -> None:
        """
        Saves the conversation memory to a file.
        """
        memories = self.load_memory()
        while len("".join(memories + [memory])) > 4096:
            memories.pop(0)
        memories.append(memory)
        with open(MEMORY_FILE, "w") as f:
            json.dump(memories, f)

    def remove_memory(self, index) -> None:
        """
        Removes a memory item from the conversation memory.
        """
        memories = self.load_memory()
        if index < len(memories):
            memories.pop(index)
            with open(MEMORY_FILE, "w") as f:
                json.dump(memories, f)


# Tool definitions for integration with the OpenAI agent
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
                "append": {
                    "type": "boolean",
                    "description": "Whether to append to the file if it already exists. Useful for writing longer content in multiple steps.",
                },
            },
            "required": ["file_path", "content", "append"],
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

PYTHON_EXECUTOR_TOOL = {
    "type": "function",
    "function": {
        "name": "python_executor",
        "description": "Executes Python code and returns the output. Useful for doing calculations, generating data, etc. In addition to standard libraries, you can use matplotlib, numpy, pypdf, and pillow. Avoid using this for potentially harmful code.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The Python code to execute.",
                },
            },
            "required": ["code"],
        },
    },
}

SAVE_MEMORY_TOOL = {
    "type": "function",
    "function": {
        "name": "save_memory",
        "description": "Stores information from the conversation to provide context for future responses. Useful for maintaining state across multiple sessions, especially in memory-intensive tasks.",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The content to store in memory.",
                },
            },
            "required": ["content"],
        },
    },
}

REMOVE_MEMORY_TOOL = {
    "type": "function",
    "function": {
        "name": "remove_memory",
        "description": "Removes a specific memory item from the conversation memory.",
        "parameters": {
            "type": "object",
            "properties": {
                "index": {
                    "type": "integer",
                    "description": "The index of the memory item to remove.",
                },
            },
            "required": ["index"],
        },
    },
}
