#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import argparse
import google.generativeai as genai
from dotenv import load_dotenv

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

def generate_commit_message(diff, model_name=DEFAULT_MODEL_NAME, lang='en', verbose=False):
    """Generates the commit message using the Gemini API."""
    if not GEMINI_API_KEY:
        print("Error: Gemini API key (GEMINI_API_KEY) not found.")
        print("Check your .env file or system environment variables.")
        sys.exit(1)

    if verbose:
        print(f"🤖 Generating commit message with model {model_name}...")
    try:
        genai.configure(api_key=GEMINI_API_KEY)

        model = genai.GenerativeModel(model_name)

        language_map = {'pt': 'Portuguese', 'en': 'English'} # Capitalized language names
        language_name = language_map.get(lang, 'English') # Default to English

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
            print("✨ Commit message generated:")
            print(f"   '{commit_message}'")
        return commit_message

    except Exception as e:
        print(f"Error generating commit message with Gemini API: {e}")
        if 'response' in locals() and hasattr(response, 'prompt_feedback'):
            print(f"Prompt feedback: {response.prompt_feedback}")
        sys.exit(1)

def git_commit(message, verbose=False):
    """Commits with the provided message."""
    try:
        if verbose:
            print(f"🚀 Committing with message: '{message}'...")
        run_git_command(['git', 'commit', '-m', message], verbose=verbose)
        if verbose:
            print("🎉 Commit successful!")
    except Exception as e:
        print(f"Failed to commit changes.")
        sys.exit(1)

def git_add_and_commit(message, verbose=False):
    """Adds all unstaged changes to the stage and commits."""
    try:
        if verbose:
            print("➕ Adding unstaged files to stage (git add .)...")
        run_git_command(['git', 'add', '.'], verbose=verbose)

        # Call the separate commit function
        git_commit(message, verbose=verbose)

    except Exception as e:
        # Error message from git_commit will be printed by it
        # We can add a more generic message here if needed
        # print(f"Failed to add or commit unstaged changes.")
        sys.exit(1)

# --- Main Execution ---
def main():
    parser = argparse.ArgumentParser(description='Generate commit messages using AI.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed messages during execution.')
    parser.add_argument('-l', '--lang', choices=['pt', 'en'], default='en', help='Commit message language (pt or en). Default: en.')
    parser.add_argument(
        '-m', 
        '--model', 
        default=DEFAULT_MODEL_NAME, 
        choices=ALLOWED_MODELS, # Add choices constraint
        help=f'Gemini model to use. Allowed: {", ".join(ALLOWED_MODELS)}. Default: {DEFAULT_MODEL_NAME}'
    )
    args = parser.parse_args()

    staged_diff = get_staged_diff(verbose=args.verbose)

    if staged_diff:
        if args.verbose:
            print("📝 Generating message for staged changes...")
        commit_message = generate_commit_message(staged_diff, model_name=args.model, lang=args.lang, verbose=args.verbose)
        git_commit(commit_message, verbose=args.verbose)
    else:
        if args.verbose:
            print("ℹ️ No staged changes found. Checking unstaged changes...")
        unstaged_diff = get_unstaged_diff(verbose=args.verbose)

        if unstaged_diff:
            if args.verbose:
                print("📝 Generating message for unstaged changes...")
            commit_message = generate_commit_message(unstaged_diff, model_name=args.model, lang=args.lang, verbose=args.verbose)
            git_add_and_commit(commit_message, verbose=args.verbose)
        else:
            print("✅ No changes (staged or unstaged) detected to commit.")
            sys.exit(0)


if __name__ == "__main__":
    main()