import argparse
import json
import os

from utils import USER_STYLE_PREFIX, Agent, PrintStyle

DEFAULTS_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "defaults.json")
)

AVAILABLE_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
    "claude-3-5-sonnet-20240620",
]


def create_argument_parser():
    """
    Create and return the argument parser for the script.

    Returns:
        argparse.ArgumentParser: Configured argument parser.
    """
    parser = argparse.ArgumentParser(description="Chat with an AI.")

    parser.add_argument("query", nargs="*", default=None, help="Optional initial query")
    parser.add_argument(
        "--memory", "-m", action="store_true", help="Use history to improve responses"
    )
    parser.add_argument(
        "--ls",
        "-l",
        action="store_true",
        help="Show GPT all files and directories in the current directory (except those specified in the .gitignore file)",
    )
    parser.add_argument(
        "--always-allow",
        "-a",
        action="store_true",
        help="Automatically allow all tools and commands (use with caution)",
    )
    parser.add_argument(
        "--save-defaults",
        "-S",
        action="store_true",
        help="Save the current flag values as defaults for future runs",
    )
    parser.add_argument(
        "--reset-defaults",
        "-R",
        action="store_true",
        help="Reset the flags to their original defaults",
    )
    parser.add_argument(
        "--show-models",
        action="store_true",
        help="Show available AI models",
    )
    parser.add_argument(
        "--model",
        choices=AVAILABLE_MODELS,
        help="Choose the AI model to use (default: gpt-4o)",
    )
    parser.add_argument(
        "--hide-splash",
        action="store_true",
        help="Hide the ASCII art splash screen and settings display",
    )

    return parser


def load_defaults():
    """Load default values from the defaults file."""
    if os.path.exists(DEFAULTS_FILE):
        with open(DEFAULTS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_defaults(flags):
    """Save the current flag values as defaults."""
    with open(DEFAULTS_FILE, "w") as f:
        json.dump(flags, f)


def initialize_agent(args):
    """
    Initialize and return an Agent instance based on script arguments.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.

    Returns:
        Agent: Configured Agent instance.
    """
    return Agent(
        model=args.model,
        use_memory=args.memory,
        view_list_dir=args.ls,
        always_allow=args.always_allow,
    )


def handle_query(agent, query):
    """
    Process the user's query with the agent.

    Args:
        agent (Agent): The agent instance to handle the query.
        query (str): The user's query.

    Returns:
        str: The agent's response.
    """
    return agent.run(query)


def print_ascii_art():
    """Print the AI TERMINAL ASCII art."""
    ascii_art = r"""
    _    ___   _____ _____ ____  __  __ ___ _   _    _    _     
   / \  |_ _| |_   _| ____|  _ \|  \/  |_ _| \ | |  / \  | |    
  / _ \  | |    | | |  _| | |_) | |\/| || ||  \| | / _ \ | |    
 / ___ \ | |    | | | |___|  _ <| |  | || || |\  |/ ___ \| |___ 
/_/   \_\___|   |_| |_____|_| \_\_|  |_|___|_| \_/_/   \_\_____|
"""
    print(f"{PrintStyle.BRIGHT_CYAN.value}{ascii_art}{PrintStyle.RESET.value}")


def main():
    """
    Main function to run the chat application.
    """
    parser = create_argument_parser()
    args = parser.parse_args()

    if args.show_models:
        print("Available AI models:")
        for model in AVAILABLE_MODELS:
            print(f"- {model}")
        return

    defaults = load_defaults()

    # Apply defaults if they exist and flags are not explicitly set
    for flag in ["memory", "ls", "always_allow", "model", "hide_splash"]:
        if flag in defaults and not getattr(args, flag):
            setattr(args, flag, defaults[flag])

    # Set the default model if not provided
    if not args.model:
        args.model = "gpt-4o"

    if args.reset_defaults:
        if os.path.exists(DEFAULTS_FILE):
            os.remove(DEFAULTS_FILE)
        print(
            f"{PrintStyle.BRIGHT_CYAN.value}Defaults have been reset.{PrintStyle.RESET.value}"
        )

    if args.save_defaults:
        current_flags = {
            "memory": args.memory,
            "ls": args.ls,
            "always_allow": args.always_allow,
            "model": args.model,
            "hide_splash": args.hide_splash,
        }
        save_defaults(current_flags)
        print(
            f"{PrintStyle.BRIGHT_CYAN.value}Defaults have been set to current flags.{PrintStyle.RESET.value}"
        )

    if not args.hide_splash:
        # Print ASCII art and current settings
        print_ascii_art()
        print(
            f"{PrintStyle.CYAN.value}         Model  {PrintStyle.RESET.value}{args.model}"
        )
        print(
            f"{PrintStyle.CYAN.value}        Memory  {f'{PrintStyle.RESET.value}Enabled' if args.memory else f'{PrintStyle.GRAY.value}Disabled'}"
        )
        print(
            f"{PrintStyle.CYAN.value}List Directory  {f'{PrintStyle.RESET.value}Enabled' if args.ls else f'{PrintStyle.GRAY.value}Disabled'}"
        )
        print(
            f"{PrintStyle.CYAN.value}  Always Allow  {f'{PrintStyle.RESET.value}Enabled' if args.always_allow else f'{PrintStyle.GRAY.value}Disabled'}"
        )
        print(PrintStyle.RESET.value)

    has_initial_query = bool(args.query)
    agent = initialize_agent(args)

    while True:
        try:
            if has_initial_query:
                # If an initial query was provided, use it as the first query
                query = " ".join(args.query)
                print(f"{USER_STYLE_PREFIX}> {query}{PrintStyle.RESET.value}")
                has_initial_query = False
            else:
                # Prompt the user for input
                query = input(f"{USER_STYLE_PREFIX}> ")
                if query.lower() in ["exit", "quit"] or query == "":
                    break
                print(PrintStyle.RESET.value, end="")

            # Handle the user's query
            handle_query(agent, query)

        except KeyboardInterrupt:
            # Handle keyboard interruption (Ctrl+C)
            # Clear the line and any styles and exit
            print("\033[K", end="")
            break

        except Exception as e:
            # Handle any other exceptions
            print(
                f"{PrintStyle.BRIGHT_RED.value}⚠ Error getting response: {e}{PrintStyle.RESET.value}"
            )
            continue

    # Clear any styles before exiting
    print(PrintStyle.RESET.value, end="")


if __name__ == "__main__":
    main()
