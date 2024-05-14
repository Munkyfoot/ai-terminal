import argparse

from utils import USER_STYLE_PREFIX, Agent, PrintStyle


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
        help="Automatically allow all file and directory reads and writes",
    )

    return parser


def initialize_agent(args):
    """
    Initialize and return an Agent instance based on script arguments.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.

    Returns:
        Agent: Configured Agent instance.
    """
    return Agent(
        model="gpt-4o",
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


def main():
    """
    Main function to run the chat application.
    """
    parser = create_argument_parser()
    args = parser.parse_args()

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
            print("\033[K", end="\r")
            break

        except Exception as e:
            # Handle any other exceptions
            print(f"Error (user): {e}")
            continue

    # Clear any styles before exiting
    print(PrintStyle.RESET.value, end="")


if __name__ == "__main__":
    main()
