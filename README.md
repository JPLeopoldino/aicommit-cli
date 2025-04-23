# aicommit-cli

A command-line tool that uses Google Gemini AI to automatically generate commit messages based on your staged changes. It follows the Conventional Commits specification.

## Features

- Analyzes `git diff` output.
- Generates concise and meaningful commit messages using Google Gemini.
- Formats messages according to the Conventional Commits standard (e.g., `feat:`, `fix:`, `docs:`, etc.).
- Adds all unstaged files and commits them with the generated message.

## Installation

1.  **Clone the repository (or download the source code):**
    ```bash
    git clone https://github.com/JPLeopoldino/aicommit-cli.git
    cd aicommit-cli
    ```

2.  **Install the package:**
    It's recommended to install it in a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows use `venv\Scripts\activate`
    pip install .
    ```
    Alternatively, for development:
    ```bash
    pip install -e .
    ```

## Configuration

1.  **Get a Gemini API Key:**
    Obtain an API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

2.  **Set up Environment Variable:**
    Create a `.env` file in the root of your project (the one you want to commit in, *not* the `aicommit-cli` directory unless you are developing the tool itself):
    ```
    GEMINI_API_KEY=YOUR_API_KEY_HERE
    ```
    Replace `YOUR_API_KEY_HERE` with your actual Gemini API key. `aicommit-cli` will automatically load this key. Alternatively, you can set the `GEMINI_API_KEY` environment variable globally in your system.

## Usage

Navigate to your Git repository directory in the terminal and simply run:

```bash
aicommit
```

**Options:**

*   `-v` or `--verbose`: Show detailed messages during execution (e.g., diff checking, API call, staging, committing).
*   `-l <lang>` or `--lang <lang>`: Specify the language for the generated commit message. Supported languages: `en` (English, default), `pt` (Portuguese).
*   `-m <model_name>` or `--model <model_name>`: Specify the Gemini model to use. Defaults to `gemini-1.5-flash`. Check Google AI documentation for available models.
*   `-b` or `--new-branch`: Generate a branch name using AI, create and checkout the new branch before committing.
*   `-i` or `--interactive`: Prompt for confirmation before using the generated branch name or commit message. Allows regenerating if the suggestion is not suitable.

**Examples:**

*   Generate a commit message in English using the default model:
    ```bash
    aicommit
    ```
*   Generate a commit message in Portuguese, show verbose output, and use a specific model:
    ```bash
    aicommit -l pt -v -m gemini-pro
    ```

The tool will:
1. Check for staged changes (`git diff --staged`). If found, proceed to step 3 with these changes.
2. If no staged changes, check for unstaged changes (`git diff`). If found, proceed to step 3 with these changes.
3. Send the diff to the Gemini API (using the specified model) to generate a commit message in the specified language.
4. Display the generated message (and other steps if `--verbose` is used).
5. If unstaged changes were used, stage all changes (`git add .`).
6. Commit the changes with the generated message (`git commit -m "message"`).

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

## License

This project is licensed under the MIT License - see the LICENSE file for details (Note: LICENSE file needs to be created if desired).
