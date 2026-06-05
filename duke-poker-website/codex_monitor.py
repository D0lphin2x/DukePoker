import argparse
import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_STATUS_FILE = BASE_DIR / "codex_status.json"


def load_status(status_file):
    try:
        return json.loads(status_file.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {
            "title": "Codex Local Monitor",
            "updated": "unknown",
            "lead": {
                "name": "Manager",
                "status": "missing status file",
                "current_task": "Create codex_status.json",
            },
            "agents": [],
            "activity": [],
            "notes": [f"Missing status file: {status_file}"],
        }
    except json.JSONDecodeError as exc:
        return {
            "title": "Codex Local Monitor",
            "updated": "invalid JSON",
            "lead": {
                "name": "Manager",
                "status": "status file error",
                "current_task": str(exc),
            },
            "agents": [],
            "activity": [],
            "notes": [f"Fix JSON syntax in {status_file}."],
        }


def esc(value):
    return html.escape(str(value), quote=True)


def badge(status):
    normalized = str(status or "unknown").strip().lower()
    class_name = "neutral"
    if normalized in {"online", "active", "running", "working"}:
        class_name = "good"
    elif normalized in {"blocked", "error", "failed"}:
        class_name = "bad"
    elif normalized in {"done", "complete", "completed"}:
        class_name = "done"
    return f'<span class="badge {class_name}">{esc(status or "unknown")}</span>'


def render_html(data):
    lead = data.get("lead", {})
    agents = data.get("agents", [])
    activity = data.get("activity", [])
    notes = data.get("notes", [])

    agent_cards = []
    if agents:
        for agent in agents:
            agent_cards.append(
                "<article class=\"agent\">"
                f"<div><h2>{esc(agent.get('name', 'Unnamed Agent'))}</h2>"
                f"{badge(agent.get('status'))}</div>"
                f"<p>{esc(agent.get('task', 'No task recorded.'))}</p>"
                f"<small>{esc(agent.get('updated', ''))}</small>"
                "</article>"
            )
    else:
        agent_cards.append(
            "<article class=\"agent empty\"><h2>No sub-agents</h2>"
            "<p>When I spawn managed agents, I can record their labels and tasks here.</p></article>"
        )

    activity_items = "".join(
        f"<li><time>{esc(item.get('time', ''))}</time><span>{esc(item.get('message', ''))}</span></li>"
        for item in activity[-12:]
    )
    notes_items = "".join(f"<li>{esc(note)}</li>" for note in notes)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="10">
  <title>{esc(data.get('title', 'Codex Local Monitor'))}</title>
  <style>
    :root {{
      color-scheme: light dark;
      --bg: #f7f5ef;
      --panel: #ffffff;
      --text: #1e2228;
      --muted: #667085;
      --line: #d8d4c9;
      --accent: #0f766e;
      --good: #047857;
      --bad: #b42318;
      --done: #3157a4;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        --bg: #181a1f;
        --panel: #22252c;
        --text: #f2f4f7;
        --muted: #a8b0bd;
        --line: #363b45;
      }}
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }}
    main {{
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
      padding: 32px 0;
    }}
    header {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
      padding-bottom: 24px;
      border-bottom: 1px solid var(--line);
    }}
    h1, h2, p {{ margin: 0; }}
    h1 {{ font-size: clamp(1.8rem, 4vw, 3.2rem); line-height: 1.05; letter-spacing: 0; }}
    h2 {{ font-size: 1rem; letter-spacing: 0; }}
    .muted {{ color: var(--muted); }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(12, 1fr);
      gap: 16px;
      margin-top: 20px;
    }}
    .panel, .agent {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }}
    .lead {{ grid-column: span 5; }}
    .activity {{ grid-column: span 7; }}
    .agents {{ grid-column: 1 / -1; }}
    .agent-list {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
      margin-top: 12px;
    }}
    .agent div {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-bottom: 10px;
    }}
    .agent small {{ display: block; color: var(--muted); margin-top: 10px; }}
    .badge {{
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      padding: 2px 9px;
      border: 1px solid currentColor;
      border-radius: 999px;
      font-size: .78rem;
      font-weight: 700;
      white-space: nowrap;
    }}
    .good {{ color: var(--good); }}
    .bad {{ color: var(--bad); }}
    .done {{ color: var(--done); }}
    .neutral {{ color: var(--muted); }}
    ul {{ list-style: none; padding: 0; margin: 12px 0 0; }}
    li {{
      display: grid;
      grid-template-columns: minmax(120px, 170px) 1fr;
      gap: 12px;
      padding: 9px 0;
      border-top: 1px solid var(--line);
    }}
    time {{ color: var(--muted); font-size: .9rem; }}
    .notes {{ margin-top: 20px; color: var(--muted); }}
    .notes li {{ display: list-item; list-style: disc; margin-left: 20px; border: 0; padding: 3px 0; }}
    @media (max-width: 780px) {{
      header {{ display: block; }}
      .lead, .activity {{ grid-column: 1 / -1; }}
      li {{ grid-template-columns: 1fr; gap: 2px; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>{esc(data.get('title', 'Codex Local Monitor'))}</h1>
        <p class="muted">Auto-refreshes every 10 seconds.</p>
      </div>
      <p class="muted">Updated: {esc(data.get('updated', 'unknown'))}</p>
    </header>
    <section class="grid">
      <article class="panel lead">
        <h2>{esc(lead.get('name', 'Manager'))}</h2>
        <p>{badge(lead.get('status'))}</p>
        <p>{esc(lead.get('current_task', 'No task recorded.'))}</p>
      </article>
      <article class="panel activity">
        <h2>Activity</h2>
        <ul>{activity_items or '<li><span>No activity yet.</span></li>'}</ul>
      </article>
      <section class="agents">
        <h2>Managed Agents</h2>
        <div class="agent-list">{''.join(agent_cards)}</div>
      </section>
    </section>
    <ul class="notes">{notes_items}</ul>
  </main>
</body>
</html>"""


class MonitorHandler(BaseHTTPRequestHandler):
    status_file = DEFAULT_STATUS_FILE

    def do_HEAD(self):
        path = urlparse(self.path).path
        if path == "/api/status":
            data = load_status(self.status_file)
            body = json.dumps(data, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            return
        if path not in {"/", "/index.html"}:
            self.send_error(404)
            return

        data = load_status(self.status_file)
        body = render_html(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        data = load_status(self.status_file)
        if path == "/api/status":
            body = json.dumps(data, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path not in {"/", "/index.html"}:
            self.send_error(404)
            return

        body = render_html(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


def main():
    parser = argparse.ArgumentParser(description="Run the local Codex monitor.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--status-file", type=Path, default=DEFAULT_STATUS_FILE)
    args = parser.parse_args()

    MonitorHandler.status_file = args.status_file
    server = ThreadingHTTPServer((args.host, args.port), MonitorHandler)
    print(f"Codex monitor running at http://{args.host}:{args.port}")
    print(f"Reading status from {args.status_file}")
    server.serve_forever()


if __name__ == "__main__":
    main()
