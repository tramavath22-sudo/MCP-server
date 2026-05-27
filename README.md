# Error Log MCP Agent

This project is a simple MCP server for hardware/test error log analysis.

## Features

- Accepts `.log`, `.txt`, and `.md` log files
- Accepts pasted log text through MCP tool
- Segregates issues by severity, category, server, and status
- Matches logs against `known_patterns.json`
- Generates a self-contained HTML report in `reports/report.html`

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Run MCP Server

```bash
python server.py
```

## MCP Tools

- `analyze_log_file(file_path: str)`
- `analyze_log_text(log_text: str)`
- `generate_report_from_text(log_text: str)`

## Sample File

Use:

```text
sample_hardware_log.txt
```

## GitHub Copilot CLI Note

If your organization blocks third-party MCP servers, Copilot CLI may show:

```text
Third-party MCP servers are disabled by your organization's Copilot policy.
```

In that case, you can still upload this repository to GitHub and explain that enterprise Copilot policy blocked custom MCP execution.
