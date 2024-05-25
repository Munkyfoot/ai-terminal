import json
import os
import subprocess
import sys
from enum import Enum
from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_random_exponential

# Load environment variables from the .env file
load_dotenv()

# Constants
MEMORY_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "memory.json"))
MEMORY_MAX = 24  # Limit for messages stored in memory

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


def write_file(file_path, content):
    """
    Writes content to a file, creating directories if necessary.

    Args:
        file_path (str): The path of the file to write (relative to the current working directory).
        content (str): The content to write to the file.

    Returns:
        str: A success message indicating that the file was written successfully.
    """
    print(
        f"{PrintStyle.CYAN.value}Writing to file '{file_path}'...{PrintStyle.RESET.value}"
    )
    file_path = os.path.join(USER_CWD, file_path)
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
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
        f"{PrintStyle.CYAN.value}Reading file '{file_path}'...{PrintStyle.RESET.value}"
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
    print(f"{PrintStyle.CYAN.value}Executing Python code...{PrintStyle.RESET.value}")
    try:
        output = subprocess.check_output(
            ["python", "-c", code], stderr=subprocess.STDOUT, text=True
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
        model: Literal["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"] = "gpt-4-turbo",
        use_memory=False,
        view_list_dir=False,
        always_allow=False,
    ) -> None:
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model = model
        self.use_memory = use_memory
        self.chat = []
        if self.use_memory:
            self.load_memory()
        self.view_list_dir = view_list_dir
        self.always_allow = always_allow
        self.system_prompt = (
            f"Your primary function is to assist the user with tasks related to terminal commands in their respective platform. You can also help with code and other queries. Information about the user's platform, environment, and current working directory is provided below.\n\n{USER_INFO}"
            + "\n\nTool Calls:\nIf you're asked to perform a task that requires writing to the file system, reading from a file, or executing Python code, use the tool directly to perform the task. Do not ask for permission first. Perform any tasks that require a tool call immediately, without responding to the user first, unless absolutely necessary for clarification."
        )

    def get_tool_call_message(self, tool_call):
        """
        Generates a message for a tool call.

        Args:
            tool_call (dict): Tool call information.

        Returns:
            str: A formatted message describing the tool call.
        """
        tool_name = tool_call["tool_name"]
        args = json.loads(tool_call["args_json"])
        if tool_name == "file_writer":
            file_name = args["file_path"]
            content = args["content"]
            return f"GPT wants to create the file '{file_name}' with this content:\n\n{content}"
        elif tool_name == "file_reader":
            file_name = args["file_path"]
            return f"GPT wants to open and read '{file_name}'"
        elif tool_name == "python_executor":
            code = args["code"]
            return f"GPT wants to execute the following Python code:\n\n{code}"
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
        args = json.loads(tool_call["args_json"])
        if tool_name == "file_writer":
            file_name = args["file_path"]
            content = args["content"]
            result = write_file(file_name, content)
        elif tool_name == "file_reader":
            file_name = args["file_path"]
            result = read_file(file_name)
        elif tool_name == "python_executor":
            code = args["code"]
            result = run_python_code(code)
        else:
            return False

        return result

    def tool_calls_to_openai_format(self, tool_calls):
        """
        Converts tool calls to the format expected by the OpenAI API.

        Args:
            tool_calls (dict): Tool calls information.

        Returns:
            list: A list of tool calls in the OpenAI format.
        """
        openai_tool_calls = []
        for index, tool_call in tool_calls.items():
            openai_tool_call = {
                "id": tool_call["tool_call_id"],
                "type": "function",
                "function": {
                    "name": tool_call["tool_name"],
                    "arguments": tool_call["args_json"],
                },
            }
            openai_tool_calls.append(openai_tool_call)
        return openai_tool_calls

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
            _messages = self.memory + self.chat
        else:
            _messages = self.chat

        _messages = _messages[-MEMORY_MAX:]

        @retry(
            wait=wait_random_exponential(min=2, max=60),
            stop=stop_after_attempt(3),
            after=lambda retry_state: print(
                f"{PrintStyle.YELLOW.value}⚠ Unable to get response. Trying again... (Attempt {retry_state.attempt_number}/3){PrintStyle.RESET.value}"
            ),
            reraise=True,
        )
        def get_stream():
            stream = self.client.chat.completions.create(
                max_tokens=4092,
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
                    PYTHON_EXECUTOR_TOOL,
                ],
                stream=True,
            )
            return stream

        try:
            stream = get_stream()
        except Exception as e:
            print(
                f"{PrintStyle.RED.value}⚠ Error getting response: {e}{PrintStyle.RESET.value}"
            )
            return

        text_stream_content = ""
        tool_calls = {}
        tool_call_detected = False
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
                        print(
                            "\n" if text_stream_content else "",
                            f"{PrintStyle.CYAN.value}Building tool call...{PrintStyle.RESET.value}",
                            sep="",
                            flush=True,
                        )

                    tool_calls[tool_call.index][
                        "args_json"
                    ] += tool_call.function.arguments

            text = chunk.choices[0].delta.content
            if text:
                text_stream_content += text
                print(text, end="", flush=True)

        if text_stream_content and not tool_call_detected:
            print("", flush=True)

        response_message = {
            "role": "assistant",
            "content": text_stream_content,
        }
        if tool_call_detected:
            response_message["tool_calls"] = self.tool_calls_to_openai_format(
                tool_calls
            )
        self.chat.append(response_message)

        if tool_call_detected:
            for index, tool_call in tool_calls.items():
                try:
                    json.loads(tool_call["args_json"])
                except json.JSONDecodeError:
                    print(
                        f"{PrintStyle.YELLOW.value}⚠ Error decoding arguments for tool call {tool_call['tool_name']}. Trying again...{PrintStyle.RESET.value}"
                    )
                    self.chat.append(
                        {
                            "tool_call_id": tool_call["tool_call_id"],
                            "role": "tool",
                            "name": tool_call["tool_name"],
                            "content": "Error decoding arguments. Ensure the arguments are in valid JSON format and try again.",
                        }
                    )
                    break

                if not self.always_allow:
                    print(
                        f"{PrintStyle.CYAN.value}{self.get_tool_call_message(tool_call)}{PrintStyle.RESET.value}"
                    )
                    tool_confirmation = input(
                        f"{PrintStyle.MAGENTA.value}Allow?\n[y or yes to confirm else cancel with optional message]: {PrintStyle.RESET.value}"
                    )
                if self.always_allow or tool_confirmation.lower() in ["y", "yes"]:
                    try:
                        tool_result = self.process_tool_call(tool_call)
                        if tool_result:
                            text_stream_content += f"\n\n{tool_result}"

                        if tool_result.startswith("Error"):
                            print(
                                f"{PrintStyle.YELLOW.value}⚠ Something went wrong.{PrintStyle.RESET.value}"
                            )
                        else:
                            print(
                                f"{PrintStyle.GREEN.value}✔ Tool executed successfully.{PrintStyle.RESET.value}"
                            )

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
                            f"{PrintStyle.RED.value}⚠ Error executing tool: {e}{PrintStyle.RESET.value}"
                        )
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
                        f"{PrintStyle.YELLOW.value}✖ Cancelled {tool_call['tool_name']}.{PrintStyle.RESET.value}"
                    )
                    self.chat.append(
                        {
                            "tool_call_id": tool_call["tool_call_id"],
                            "role": "tool",
                            "name": tool_call["tool_name"],
                            "content": f"User cancelled the tool execution.",
                        }
                    )
                    if tool_confirmation:
                        self.chat.append(
                            {
                                "role": "user",
                                "content": tool_confirmation,
                            }
                        )

        if self.use_memory:
            self.save_memory()

        if tool_call_detected:
            self.run()

    def save_memory(self) -> None:
        """
        Saves the conversation memory to a file.
        """
        memory = (self.memory + self.chat)[-MEMORY_MAX:]
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f)

    def load_memory(self) -> None:
        """
        Loads the conversation memory from a file.
        """
        self.chat = []
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r") as f:
                self.memory = json.load(f)
        else:
            self.memory = []


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

PYTHON_EXECUTOR_TOOL = {
    "type": "function",
    "function": {
        "name": "python_executor",
        "description": "Executes Python code and returns the output. Useful for doing calculations, generating data, etc. In addition to standard libraries, you can use matplotlib, numpy, and pillow. Avoid using this for potentially harmful code.",
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
