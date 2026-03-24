#!/usr/bin/env python3
"""Sandbox CLI - lightweight agent to execute tasks and integrate with NVIDIA APIs."""
import os
import sys
import json
import shlex
import subprocess
import time
from pathlib import Path

import click
import requests
from dotenv import load_dotenv
from rich import print

# Load config
HOME = Path.home()
INSTALL_DIR = HOME / '.nvidia-sandbox-agent'
CONFIG_FILE = INSTALL_DIR / 'config.json'

load_dotenv()

VERSION = '0.1.0'

def run_cmd(cmd, timeout=300):
    """Run a shell command safely with timeout and capture output."""
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, text=True)
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return 124, '', 'Command timed out'


@click.group()
@click.version_option(version=VERSION)
def cli():
    "Sandbox CLI"
    pass

@cli.command()
def health():
    "Check health of the sandbox environment"
    print('[green]Sandbox Health Check[/green]')
    python_ok = subprocess.call(['python3', '--version'])
    git_ok = subprocess.call(['git', '--version'])
    print(f'python3 status: {"ok" if python_ok==0 else "missing"}')
    print(f'git status: {"ok" if git_ok==0 else "missing"}')
    print(f'install dir: {INSTALL_DIR}')

@cli.command()
@click.argument('command', nargs=-1)
def exec(command):
    "Execute a shell command inside the sandbox"
    if not command:
        print('[red]No command provided[/red]')
        sys.exit(1)
    cmd = ' '.join(command)
    print(f'[blue]Executing:[/blue] {cmd}')
    code, out, err = run_cmd(cmd)
    print('--- stdout ---')
    print(out)
    print('--- stderr ---')
    print(err)
    sys.exit(code)

@cli.command()
@click.argument('task', nargs=-1)
def agent(task):
    "Ask the AI agent to perform a task. The agent will return shell commands to run." 
    if not task:
        print('[red]No task provided[/red]')
        sys.exit(1)
    task_text = ' '.join(task)
    print(f'[green]Agent received task:[/green] {task_text}')
    api_key = os.getenv('NVIDIA_API_KEY')
    if not api_key:
        print('[yellow]NVIDIA_API_KEY not set. Set it with export NVIDIA_API_KEY=...[/yellow]')
        sys.exit(1)
    # Minimal example calling a hypothetical NVIDIA Claude endpoint
    endpoint = 'https://api.nvidia.com/claude/generate'  # Placeholder; users must update
    payload = {'prompt': f'Act as a shell operator. For the task: {task_text}, produce a list of concise shell commands to accomplish it. Reply in JSON: {"commands": ["..."]}.'}
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    try:
        r = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        commands = data.get('commands') or []
    except Exception as e:
        print(f'[red]Failed to contact NVIDIA API: {e}[/red]')
        sys.exit(1)
    if not commands:
        print('[yellow]No commands returned by the agent.[/yellow]')
        sys.exit(1)
    for c in commands:
        print(f'[blue]Running:[/blue] {c}')
        code, out, err = run_cmd(c)
        print(out)
        if code != 0:
            print(f'[red]Command failed with code {code}[/red]\n{err}')
            break

@cli.command()
def models():
    "List available models (placeholder)"
    print('Available models:')
    print('- claude-3.5-sonnet (via NVIDIA)')
    print('- free-claude-code (local clone)')

if __name__ == '__main__':
    cli()