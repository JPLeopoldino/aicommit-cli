#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import argparse
import google.generativeai as genai
from dotenv import load_dotenv
import re # Import re for branch name sanitization

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
# Try to get Gemini API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# List of allowed Gemini models
ALLOWED_MODELS = ["gemini-2.0-flash-lite", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
# Default Gemini model to use
DEFAULT_MODEL_NAME = "gemini-2.0-flash-lite"
# Instruction for the AI to generate the commit message
COMMIT_MESSAGE_PROMPT_TEMPLATE = """
Generate a concise and meaningful commit message in {language}, following the Conventional Commits standard (e.g., 'feat: add new feature X', 'fix: correct bug Y', 'docs: update documentation Z', 'style: format code', 'refactor: refactor component A', 'test: add tests for B', 'chore: update dependencies').

The message must have a maximum of 72 characters in the first line (title) and clearly describe the changes present in the following 'git diff':

{diff}

Generated commit message:
"""
# Instruction for the AI to generate the branch name
BRANCH_NAME_PROMPT_TEMPLATE = """
Generate a short, descriptive Git branch name based on the following 'git diff'.
The branch name should be suitable for use in a URL (kebab-case: lowercase, words separated by hyphens, no special characters other than hyphens).
Optionally, prefix the name with 'feat/', 'fix/', 'chore/', 'docs/', 'refactor/', etc., based on the primary nature of the changes.
Keep the total length concise, ideally under 50 characters.

Git Diff:
{diff}

Generated branch name:
"""

# --- Helper Functions ---
#

def run_git_command(command, verbose=False):
    """Executes a Git command and returns the output or raises an exception on error."""
    try:
        result = subprocess.run(command, text=True, capture_output=True, check=True, encoding='utf-8')
        return result.stdout.strip()
    except FileNotFoundError:
        print(f"Error: Command '{command[0]}' not found. Is Git installed and in PATH?")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        if verbose:
            print(f"Error executing Git command: {' '.join(command)}")
            print(f"Exit code: {e.returncode}")
            print(f"Error: {e.stderr.strip()}")
        else:
            print(f"Error executing Git command: {e.stderr.strip()}")
        if "not a git repository" in e.stderr:
            print("Make sure you are inside a Git repository.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while running Git: {e}")
        sys.exit(1)

def get_staged_diff(verbose=False):
    """Gets the 'staged' changes (added to the stage) in the repository."""
    if verbose:
        print("🔍 Checking staged changes (git diff --staged)...")
    diff = run_git_command(['git', 'diff', '--staged'], verbose=verbose)
    if diff and verbose:
        print(" Staged changes detected.")
    return diff

def get_unstaged_diff(verbose=False):
    """Gets the 'unstaged' changes (not added to the stage) in the repository."""
    if verbose:
        print("🔍 Checking unstaged changes (git diff)...")
    diff = run_git_command(['git', 'diff'], verbose=verbose)
    if diff and verbose:
        print(" Unstaged changes detected.")
    return diff

def sanitize_branch_name(name):
    """Sanitizes a string to be a valid Git branch name."""
    # Remove potential prefixes like ``` or `
    name = name.strip('` ')
    # Replace spaces and underscores with hyphens
    name = re.sub(r'[\s_]+', '-', name)
    # Remove any characters that are not alphanumeric, hyphen, or forward slash
    name = re.sub(r'[^a-zA-Z0-9\-/]', '', name)
    # Remove leading/trailing hyphens
    name = name.strip('-')
    # Ensure it's not empty
    if not name:
        return f"ai-generated-branch-{os.urandom(4).hex()}" # Fallback name
    return name.lower()

def generate_branch_name(diff, model_name=DEFAULT_MODEL_NAME, verbose=False, interactive=False):
    """Generates a branch name using the Gemini API, with optional interactive confirmation."""
    if not GEMINI_API_KEY:
        print("Error: Gemini API key (GEMINI_API_KEY) not found.")
        print("Check your .env file or system environment variables.")
        sys.exit(1)

    while True: # Loop for regeneration
        if verbose:
            print(f"🤖 Generating branch name with model {model_name}...")
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel(model_name)
            prompt = BRANCH_NAME_PROMPT_TEMPLATE.format(diff=diff)

            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            response = model.generate_content(prompt, safety_settings=safety_settings)

            branch_name = response.text.strip()
            sanitized_name = sanitize_branch_name(branch_name)

            if not sanitized_name:
                 raise ValueError("The API returned an empty or invalid branch name.")

            if verbose:
                if interactive:
                    print("✨ Branch name generated.")
                else:
                    print(f"✨ Branch name generated (sanitized): '{sanitized_name}' (Original: '{branch_name}')")

            if not interactive:
                return sanitized_name # Return directly if not interactive

            # --- Interactive Confirmation ---
            print(f"\nSuggested branch name: \033[1m{sanitized_name}\033[0m") # Bold text
            while True:
                choice = input("Accept this branch name? (y/n/r=regenerate): ").lower().strip()
                if choice == 'y':
                    return sanitized_name
                elif choice == 'n':
                    print("Aborted by user.")
                    sys.exit(0)
                elif choice == 'r':
                    if verbose:
                        print("🔄 Regenerating branch name...")
                    break # Break inner loop to regenerate
                else:
                    print("Invalid choice. Please enter 'y', 'n', or 'r'.")
            # If 'r' was chosen, the outer loop continues

        except Exception as e:
            print(f"Error generating branch name with Gemini API: {e}")
            if 'response' in locals() and hasattr(response, 'prompt_feedback'):
                print(f"Prompt feedback: {response.prompt_feedback}")
            # Ask if user wants to retry in interactive mode
            if interactive:
                retry_choice = input("Failed to generate. Retry? (y/n): ").lower().strip()
                if retry_choice != 'y':
                    print("Aborted.")
                    sys.exit(1)
                # Continue outer loop to retry
            else:
                sys.exit(1) # Exit if not interactive

def generate_commit_message(diff, model_name=DEFAULT_MODEL_NAME, lang='en', verbose=False, interactive=False):
    """Generates the commit message using the Gemini API, with optional interactive confirmation."""
    if not GEMINI_API_KEY:
        print("Error: Gemini API key (GEMINI_API_KEY) not found.")
        print("Check your .env file or system environment variables.")
        sys.exit(1)

    while True: # Loop for regeneration
        if verbose:
            print(f"🤖 Generating commit message with model {model_name}...")
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel(model_name)
            language_map = {'pt': 'Portuguese', 'en': 'English'}
            language_name = language_map.get(lang, 'English')
            prompt = COMMIT_MESSAGE_PROMPT_TEMPLATE.format(diff=diff, language=language_name)

            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            response = model.generate_content(prompt, safety_settings=safety_settings)

            commit_message = response.text.strip()
            commit_message = commit_message.replace('```', '').replace('`', '').replace('"', '').replace("'", "")
            if not commit_message:
                 raise ValueError("The API returned an empty message.")

            if verbose:
                if interactive:
                    print("✨ Commit message generated.")
                else:
                    print("✨ Commit message generated:")
                    print(f"   '{commit_message}'")

            if not interactive:
                return commit_message # Return directly if not interactive

            # --- Interactive Confirmation ---
            print(f"\nSuggested commit message:\n---\n\033[1m{commit_message}\033[0m\n---") # Bold text
            while True:
                choice = input("Accept this commit message? (y/n/r=regenerate): ").lower().strip()
                if choice == 'y':
                    return commit_message
                elif choice == 'n':
                    print("Aborted by user.")
                    sys.exit(0)
                elif choice == 'r':
                    if verbose:
                        print("🔄 Regenerating commit message...")
                    break # Break inner loop to regenerate
                else:
                    print("Invalid choice. Please enter 'y', 'n', or 'r'.")
            # If 'r' was chosen, the outer loop continues

        except Exception as e:
            print(f"Error generating commit message with Gemini API: {e}")
            if 'response' in locals() and hasattr(response, 'prompt_feedback'):
                print(f"Prompt feedback: {response.prompt_feedback}")
            # Ask if user wants to retry in interactive mode
            if interactive:
                retry_choice = input("Failed to generate. Retry? (y/n): ").lower().strip()
                if retry_choice != 'y':
                    print("Aborted.")
                    sys.exit(1)
                # Continue outer loop to retry
            else:
                sys.exit(1) # Exit if not interactive

def git_commit(message, verbose=False):
    """Commits with the provided message."""
    try:
        if verbose:
            print(f"🚀 Committing with message...")
        run_git_command(['git', 'commit', '-m', message], verbose=verbose)
        if verbose:
            print("🎉 Commit successful!")
    except Exception as e:
        print(f"Failed to commit changes.")
        sys.exit(1)

def git_add_all(verbose=False):
    """Adds all changes to the stage."""
    try:
        if verbose:
            print("➕ Adding all changes to stage (git add .)...")
        run_git_command(['git', 'add', '.'], verbose=verbose)
    except Exception as e:
        print(f"❌ Failed to stage changes (git add .).")
        sys.exit(1)

def git_create_and_checkout_branch(branch_name, verbose=False):
    """Creates and checks out a new Git branch."""
    try:
        if verbose:
            print(f"🌿 Creating and checking out new branch '{branch_name}'...") # Added branch name for clarity
        run_git_command(['git', 'checkout', '-b', branch_name], verbose=verbose)
        if verbose:
            print(f"✅ Switched to new branch '{branch_name}'.")
    except subprocess.CalledProcessError as e:
        if "already exists" in e.stderr:
             if verbose:
                 print(f"⚠️ Branch '{branch_name}' already exists. Attempting to checkout...")
             try:
                 run_git_command(['git', 'checkout', branch_name], verbose=verbose)
                 if verbose:
                     print(f"✅ Switched to existing branch '{branch_name}'.")
             except Exception as checkout_e:
                 print(f"❌ Failed to checkout existing branch '{branch_name}'.")
                 sys.exit(1)
        else:
            print(f"❌ Failed to create or checkout branch '{branch_name}'.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred during branch creation/checkout: {e}")
        sys.exit(1)

# --- Main Execution ---
def main():
    parser = argparse.ArgumentParser(description='Generate commit messages and optionally branch names using AI.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed messages during execution.')
    parser.add_argument('-l', '--lang', choices=['pt', 'en'], default='en', help='Commit message language (pt or en). Default: en.')
    parser.add_argument(
        '-m', 
        '--model', 
        default=DEFAULT_MODEL_NAME, 
        choices=ALLOWED_MODELS, 
        help=f'Gemini model to use. Default: {DEFAULT_MODEL_NAME}'
    )
    parser.add_argument(
        '-b',
        '--new-branch',
        action='store_true',
        help='Generate a branch name using AI, create and checkout the new branch before committing.'
    )
    parser.add_argument(
        '-i',
        '--interactive',
        action='store_true',
        help='Prompt for confirmation before using the generated branch name or commit message.'
    )
    args = parser.parse_args()

    diff_to_process = None
    is_staged_diff = False

    staged_diff = get_staged_diff(verbose=args.verbose)
    if staged_diff:
        diff_to_process = staged_diff
        is_staged_diff = True
        if args.verbose:
            print("ℹ️ Using staged changes for AI generation.")
    else:
        unstaged_diff = get_unstaged_diff(verbose=args.verbose)
        if unstaged_diff:
            diff_to_process = unstaged_diff
            is_staged_diff = False
            if args.verbose:
                print("ℹ️ No staged changes found. Using unstaged changes for AI generation.")
        else:
            print("✅ No changes (staged or unstaged) detected to process.")
            sys.exit(0)

    # --- Branch Creation (if requested) ---
    if args.new_branch:
        branch_name = generate_branch_name(diff_to_process, model_name=args.model, verbose=args.verbose, interactive=args.interactive)
        git_create_and_checkout_branch(branch_name, verbose=args.verbose)

    # --- Commit Message Generation ---
    if args.verbose:
        print("📝 Generating commit message...")
    commit_message = generate_commit_message(diff_to_process, model_name=args.model, lang=args.lang, verbose=args.verbose, interactive=args.interactive)

    # --- Staging and Committing ---
    if not is_staged_diff:
        # If we used unstaged diff, we always need to stage changes before commit
        git_add_all(verbose=args.verbose)

    # Commit the changes (either staged originally, or newly staged)
    git_commit(commit_message, verbose=args.verbose)


if __name__ == "__main__":
    main()