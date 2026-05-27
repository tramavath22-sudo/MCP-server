import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Error Log Analysis Agent")

BASE_DIR = Path(__file__).parent
PATTERN_FILE = BASE_DIR / "known_patterns.json"
REPORT_DIR = BASE_DIR / "reports"
ALLOWED_EXTENSIONS = {".log", ".txt", ".md"}

REPORT_DIR.mkdir(exist_ok=True)


def load_patterns() -> List[Dict[str, Any]]:
    with open(PATTERN_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def parse_log_line(line: str) -> Dict[str, str] | None:
    regex = (
        r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) "
        r"(?P<server>\S+) "
        r"(?P<status>\S+) "
        r"(?P<message>.*)"
    )
    match = re.match(regex, line.strip())
    return match.groupdict() if match else None


def analyze_logs(log_text: str) -> Dict[str, Any]:
    patterns = load_patterns()
    findings = []

    for line_number, line in enumerate(log_text.splitlines(), start=1):
        parsed = parse_log_line(line)
        if not parsed:
            continue

        for rule in patterns:
            if rule["pattern"] in parsed["message"]:
                findings.append({
                    "line_number": line_number,
                    "timestamp": parsed["timestamp"],
                    "server": parsed["server"],
                    "status": parsed["status"],
                    "message": parsed["message"],
                    "matched_pattern": rule["pattern"],
                    "severity": rule["severity"],
                    "category": rule["category"],
                    "prediction_rule": rule.get("prediction_rule", ""),
                    "root_cause": rule["root_cause"],
                    "suggested_action": rule["suggested_action"]
                })

    return build_summary(findings)


def build_summary(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "total_issues": len(findings),
        "severity_count": dict(Counter(item["severity"] for item in findings)),
        "category_count": dict(Counter(item["category"] for item in findings)),
        "server_count": dict(Counter(item["server"] for item in findings)),
        "status_count": dict(Counter(item["status"] for item in findings)),
        "findings": findings
    }


def generate_html_report(analysis: Dict[str, Any]) -> str:
    rows = ""

    for item in analysis["findings"]:
        rows += f"""
        <tr>
            <td>{item['line_number']}</td>
            <td>{item['timestamp']}</td>
            <td>{item['server']}</td>
            <td>{item['status']}</td>
            <td>{item['severity']}</td>
            <td>{item['category']}</td>
            <td>{item['matched_pattern']}</td>
            <td>{item['message']}</td>
            <td>{item['root_cause']}</td>
            <td>{item['suggested_action']}</td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Error Log Analysis Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 24px;
            background: #f8fafc;
            color: #111827;
        }}
        h1, h2 {{
            color: #1f2937;
        }}
        .card {{
            background: white;
            padding: 16px;
            margin-bottom: 16px;
            border-radius: 10px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
        }}
        th, td {{
            border: 1px solid #d1d5db;
            padding: 8px;
            font-size: 13px;
            text-align: left;
            vertical-align: top;
        }}
        th {{
            background: #e5e7eb;
        }}
    </style>
</head>
<body>
    <h1>Error Log Analysis Report</h1>

    <div class="card">
        <p><b>Generated At:</b> {datetime.now()}</p>
        <p><b>Total Issues Found:</b> {analysis["total_issues"]}</p>
    </div>

    <div class="card">
        <h2>Summary</h2>
        <p><b>Severity:</b> {analysis["severity_count"]}</p>
        <p><b>Category:</b> {analysis["category_count"]}</p>
        <p><b>Server:</b> {analysis["server_count"]}</p>
        <p><b>Status:</b> {analysis["status_count"]}</p>
    </div>

    <div class="card">
        <h2>Detailed Findings</h2>
        <table>
            <tr>
                <th>Line</th>
                <th>Timestamp</th>
                <th>Server</th>
                <th>Status</th>
                <th>Severity</th>
                <th>Category</th>
                <th>Pattern</th>
                <th>Message</th>
                <th>Root Cause Hint</th>
                <th>Suggested Action</th>
            </tr>
            {rows}
        </table>
    </div>
</body>
</html>"""


@mcp.tool()
def analyze_log_text(log_text: str) -> str:
    """
    Analyze pasted raw log text and return structured JSON findings.
    """
    analysis = analyze_logs(log_text)
    return json.dumps(analysis, indent=2)


@mcp.tool()
def analyze_log_file(file_path: str) -> str:
    """
    Analyze .log, .txt, or .md file and generate a self-contained HTML report.
    """
    path = Path(file_path)

    if not path.exists():
        return f"File not found: {file_path}"

    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        return f"Unsupported file type: {path.suffix}. Supported: .log, .txt, .md"

    log_text = path.read_text(encoding="utf-8", errors="ignore")
    analysis = analyze_logs(log_text)

    report_path = REPORT_DIR / "report.html"
    report_path.write_text(generate_html_report(analysis), encoding="utf-8")

    return json.dumps({
        "message": "Analysis completed",
        "total_issues": analysis["total_issues"],
        "severity_count": analysis["severity_count"],
        "category_count": analysis["category_count"],
        "server_count": analysis["server_count"],
        "status_count": analysis["status_count"],
        "report_path": str(report_path)
    }, indent=2)


@mcp.tool()
def generate_report_from_text(log_text: str) -> str:
    """
    Analyze pasted log text and generate a self-contained HTML report.
    """
    analysis = analyze_logs(log_text)
    report_path = REPORT_DIR / "pasted_log_report.html"
    report_path.write_text(generate_html_report(analysis), encoding="utf-8")

    return json.dumps({
        "message": "HTML report generated from pasted text",
        "total_issues": analysis["total_issues"],
        "report_path": str(report_path)
    }, indent=2)


if __name__ == "__main__":
    mcp.run()
