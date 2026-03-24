# NVIDIA Sandbox Agent

Lightweight sandbox CLI to run shell commands and integrate with NVIDIA Claude-style APIs.

## Quick install

```bash
curl -fsSL https://raw.githubusercontent.com/fugtailer/nvidia-sandbox-agent/main/install.sh | bash
```

## Usage

Set your NVIDIA API key:

```bash
export NVIDIA_API_KEY='...'
```

Run health check:

```bash
sandbox health
```

Execute a command:

```bash
sandbox exec ls -la /tmp
```

Ask the agent to perform a task (requires a valid NVIDIA endpoint in sandbox-cli.py):

```bash
sandbox agent 'install python3 and pip'
```