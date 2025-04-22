#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import argparse
import google.generativeai as genai
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# --- Configuração ---
# Tenta obter a chave da API Gemini do ambiente
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Modelo Gemini a ser usado (verificar disponibilidade no nível gratuito)
# 'gemini-1.5-flash' é geralmente uma boa opção com nível gratuito.
MODEL_NAME = "gemini-1.5-flash"
# Instrução para a IA gerar a mensagem de commit
COMMIT_MESSAGE_PROMPT_TEMPLATE = """
Gere uma mensagem de commit concisa e significativa em {language}, seguindo o padrão Conventional Commits (ex: 'feat: adiciona nova funcionalidade X', 'fix: corrige bug Y', 'docs: atualiza documentação Z', 'style: formata código', 'refactor: refatora componente A', 'test: adiciona testes para B', 'chore: atualiza dependências').

A mensagem deve ter no máximo 72 caracteres na primeira linha (título) e descrever claramente as mudanças presentes no seguinte 'git diff':

{diff}

Mensagem de commit gerada:
"""
# --- Funções Auxiliares ---

def run_git_command(command, verbose=False):
    """Executa um comando Git e retorna a saída ou lança exceção em caso de erro."""
    try:
        result = subprocess.run(command, text=True, capture_output=True, check=True, encoding='utf-8')
        return result.stdout.strip()
    except FileNotFoundError:
        print(f"Erro: O comando '{command[0]}' não foi encontrado. O Git está instalado e no PATH?")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        if verbose:
            print(f"Erro ao executar o comando Git: {' '.join(command)}")
            print(f"Código de saída: {e.returncode}")
            print(f"Erro: {e.stderr.strip()}")
        else:
            print(f"Erro ao executar o comando Git: {e.stderr.strip()}")
        if "not a git repository" in e.stderr:
            print("Certifique-se de estar dentro de um repositório Git.")
        sys.exit(1)
    except Exception as e:
        print(f"Um erro inesperado ocorreu ao executar o Git: {e}")
        sys.exit(1)

def get_git_diff(verbose=False):
    """Obtém as mudanças 'unstaged' (não adicionadas ao stage) no repositório."""
    if verbose:
        print("🔍 Verificando mudanças nos arquivos...")
    diff = run_git_command(['git', 'diff'], verbose=verbose)
    if not diff:
        print("✅ Nenhuma mudança detectada para commitar.")
        sys.exit(0)
    if verbose:
        print(" mudanças detectadas.")
    return diff

def generate_commit_message(diff, lang='en', verbose=False):
    """Gera a mensagem de commit usando a API Gemini."""
    if not GEMINI_API_KEY:
        print("Erro: A chave da API Gemini (GEMINI_API_KEY) não foi encontrada.")
        print("Verifique seu arquivo .env ou as variáveis de ambiente do sistema.")
        sys.exit(1)

    if verbose:
        print(f"🤖 Gerando mensagem de commit com o modelo {MODEL_NAME}...")
    try:
        genai.configure(api_key=GEMINI_API_KEY)

        model = genai.GenerativeModel(MODEL_NAME)

        language_map = {'pt': 'português', 'en': 'english'}
        language_name = language_map.get(lang, 'english')

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
             raise ValueError("A API retornou uma mensagem vazia.")

        if verbose:
            print("✨ Mensagem de commit gerada:")
            print(f"   '{commit_message}'")
        return commit_message

    except Exception as e:
        print(f"Erro ao gerar mensagem de commit com a API Gemini: {e}")
        if 'response' in locals() and hasattr(response, 'prompt_feedback'):
            print(f"Feedback do prompt: {response.prompt_feedback}")
        sys.exit(1)

def git_add_and_commit(message, verbose=False):
    """Adiciona todas as mudanças ao stage e faz o commit."""
    try:
        if verbose:
            print("➕ Adicionando arquivos ao stage (git add .)...")
        run_git_command(['git', 'add', '.'], verbose=verbose)

        if verbose:
            print(f"🚀 Realizando commit com a mensagem: '{message}'...")
        run_git_command(['git', 'commit', '-m', message], verbose=verbose)

        if verbose:
            print("🎉 Commit realizado com sucesso!")
    except Exception as e:
        print(f"Falha ao adicionar ou commitar as mudanças.")
        sys.exit(1)

# --- Execução Principal ---
def main():
    parser = argparse.ArgumentParser(description='Gera mensagens de commit usando IA.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Exibe mensagens detalhadas durante a execução.')
    parser.add_argument('-l', '--lang', choices=['pt', 'en'], default='en', help='Idioma da mensagem de commit (pt ou en). Padrão: en.')
    args = parser.parse_args()

    diff_output = get_git_diff(verbose=args.verbose)

    commit_message = generate_commit_message(diff_output, lang=args.lang, verbose=args.verbose)

    git_add_and_commit(commit_message, verbose=args.verbose)

if __name__ == "__main__":
    main()