#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
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
Gere uma mensagem de commit concisa e significativa em português, seguindo o padrão Conventional Commits (ex: 'feat: adiciona nova funcionalidade X', 'fix: corrige bug Y', 'docs: atualiza documentação Z', 'style: formata código', 'refactor: refatora componente A', 'test: adiciona testes para B', 'chore: atualiza dependências').

A mensagem deve ter no máximo 72 caracteres na primeira linha (título) e descrever claramente as mudanças presentes no seguinte 'git diff':

{diff}

Mensagem de commit gerada:
"""
# --- Funções Auxiliares ---

def run_git_command(command):
    """Executa um comando Git e retorna a saída ou lança exceção em caso de erro."""
    try:
        # Executa o comando. text=True decodifica stdout/stderr como texto.
        # capture_output=True captura stdout/stderr.
        # check=True lança CalledProcessError se o comando retornar um código diferente de zero.
        # stderr=subprocess.PIPE captura erros separadamente
        result = subprocess.run(command, text=True, capture_output=True, check=True, encoding='utf-8')
        return result.stdout.strip()
    except FileNotFoundError:
        print(f"Erro: O comando '{command[0]}' não foi encontrado. O Git está instalado e no PATH?")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar o comando Git: {' '.join(command)}")
        print(f"Código de saída: {e.returncode}")
        print(f"Erro: {e.stderr.strip()}")
        # Verifica se é um repositório git válido
        if "not a git repository" in e.stderr:
            print("Certifique-se de estar dentro de um repositório Git.")
        sys.exit(1)
    except Exception as e:
        print(f"Um erro inesperado ocorreu ao executar o Git: {e}")
        sys.exit(1)

def get_git_diff():
    """Obtém as mudanças 'unstaged' (não adicionadas ao stage) no repositório."""
    print("🔍 Verificando mudanças nos arquivos...")
    # Usa 'git diff' para pegar mudanças que ainda não foram para o stage
    diff = run_git_command(['git', 'diff'])
    print(diff)
    if not diff:
        print("✅ Nenhuma mudança detectada para commitar.")
        sys.exit(0)
    print(" mudanças detectadas.")
    return diff

def generate_commit_message(diff):
    """Gera a mensagem de commit usando a API Gemini."""
    if not GEMINI_API_KEY:
        print("Erro: A chave da API Gemini (GEMINI_API_KEY) não foi encontrada.")
        print("Verifique seu arquivo .env ou as variáveis de ambiente do sistema.")
        sys.exit(1)

    print(f"🤖 Gerando mensagem de commit com o modelo {MODEL_NAME}...")
    try:
        # Configura a API Gemini
        genai.configure(api_key=GEMINI_API_KEY)

        # Cria o modelo generativo
        model = genai.GenerativeModel(MODEL_NAME)

        # Prepara o prompt final
        prompt = COMMIT_MESSAGE_PROMPT_TEMPLATE.format(diff=diff)

        # Gera o conteúdo (mensagem de commit)
        # Adicionando configuração de segurança para evitar bloqueios comuns
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        response = model.generate_content(prompt, safety_settings=safety_settings)

        # Extrai e limpa a mensagem gerada
        commit_message = response.text.strip()
        # Remove possíveis cercas de código (```) ou aspas que a IA possa adicionar
        commit_message = commit_message.replace('```', '').replace('`', '').replace('"', '').replace("'", "")
        # Garante que a mensagem não esteja vazia
        if not commit_message:
             raise ValueError("A API retornou uma mensagem vazia.")

        print("✨ Mensagem de commit gerada:")
        print(f"   '{commit_message}'")
        return commit_message

    except Exception as e:
        print(f"Erro ao gerar mensagem de commit com a API Gemini: {e}")
        # Imprime a resposta completa em caso de erro para depuração, se disponível
        if 'response' in locals() and hasattr(response, 'prompt_feedback'):
            print(f"Feedback do prompt: {response.prompt_feedback}")
        sys.exit(1)

def git_add_and_commit(message):
    """Adiciona todas as mudanças ao stage e faz o commit."""
    try:
        print("➕ Adicionando arquivos ao stage (git add .)...")
        run_git_command(['git', 'add', '.'])

        print(f"🚀 Realizando commit com a mensagem: '{message}'...")
        run_git_command(['git', 'commit', '-m', message])

        print("🎉 Commit realizado com sucesso!")
    except Exception as e:
        # A função run_git_command já imprime erros detalhados
        print(f"Falha ao adicionar ou commitar as mudanças.")
        sys.exit(1)

# --- Execução Principal ---
if __name__ == "__main__":
    # 1. Pega o diff das mudanças não adicionadas
    diff_output = get_git_diff()

    # 2. Gera a mensagem de commit usando a IA
    commit_message = generate_commit_message(diff_output)

    # 3. Adiciona os arquivos e faz o commit
    git_add_and_commit(commit_message)