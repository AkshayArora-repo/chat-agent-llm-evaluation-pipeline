#!/usr/bin/env python3
"""Web UI to review and correct LLM pre-labels for dietary adherence.

Serves on http://localhost:8889. Shows each trace with its pre-label,
reasoning, query, diet, and response. You can flip labels and save.
"""

import pandas as pd
import json
import html as html_mod
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "labeled_traces.csv"
PORT = 8889

df = pd.read_csv(CSV_PATH)

# Track manual overrides
if "manual_reviewed" not in df.columns:
    df["manual_reviewed"] = False


def build_html():
    # Stats
    total = len(df)
    passes = (df["label"] == "PASS").sum()
    fails = (df["label"] == "FAIL").sum()
    reviewed = df["manual_reviewed"].sum()

    fail_by_diet = df[df["label"] == "FAIL"].groupby("dietary_restriction").size().sort_values(ascending=False)
    diet_stats = "".join(
        f"<span class='diet-tag'>{d}: {c}</span>" for d, c in fail_by_diet.items()
    )

    rows = ""
    for i, row in df.iterrows():
        tid = html_mod.escape(str(row["trace_id"]))
        query = html_mod.escape(str(row["query"]))
        diet = html_mod.escape(str(row["dietary_restriction"]))
        resp = html_mod.escape(str(row["response"]))
        label = str(row["label"])
        reasoning = html_mod.escape(str(row.get("reasoning", "")))
        confidence = str(row.get("confidence", ""))
        reviewed_flag = bool(row.get("manual_reviewed", False))

        label_class = "pass" if label == "PASS" else "fail"
        reviewed_class = "reviewed" if reviewed_flag else ""

        query_short = query[:100] + "..." if len(query) > 100 else query
        resp_short = resp[:150] + "..." if len(resp) > 150 else resp
        reasoning_short = reasoning[:200] + "..." if len(reasoning) > 200 else reasoning

        rows += f"""
        <tr class="row-{label_class} {reviewed_class}" id="row-{i}">
            <td class="idx">{i}</td>
            <td><code>{tid}</code></td>
            <td><span class="diet">{diet}</span></td>
            <td class="query-cell" title="{query}">{query_short}</td>
            <td>
                <span class="badge {label_class}" id="badge-{i}">{label}</span>
                <span class="conf">{confidence}</span>
            </td>
            <td class="reasoning-cell" title="{reasoning}">{reasoning_short}</td>
            <td>
                <button class="btn-flip" onclick="flipLabel({i})">Flip</button>
                <button class="btn-detail" onclick="showDetail({i})">View</button>
            </td>
        </tr>"""

    # Build JSON data outside the f-string to avoid {{ }} conflicts
    json_data = json.dumps([
        {
            "idx": i,
            "trace_id": str(row["trace_id"]),
            "query": str(row["query"]),
            "dietary_restriction": str(row["dietary_restriction"]),
            "response": str(row["response"]),
            "label": str(row["label"]),
            "reasoning": str(row.get("reasoning", "")),
            "confidence": str(row.get("confidence", "")),
        }
        for i, row in df.iterrows()
    ])

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Label Review</title>
<style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ font-family: -apple-system, sans-serif; background:#0d1117; color:#c9d1d9; padding:16px; }}
    h1 {{ font-size:20px; margin-bottom:8px; }}
    .stats {{ margin-bottom:12px; padding:10px; background:#161b22; border-radius:6px; font-size:13px; }}
    .stats span {{ margin-right:16px; }}
    .diet-tag {{ background:#21262d; padding:2px 8px; border-radius:4px; margin:2px; display:inline-block; font-size:11px; }}
    table {{ width:100%; border-collapse:collapse; font-size:12px; }}
    th {{ background:#161b22; padding:8px 6px; text-align:left; position:sticky; top:0; z-index:10; }}
    td {{ padding:6px; border-bottom:1px solid #21262d; vertical-align:top; }}
    .idx {{ color:#484f58; width:30px; }}
    .badge {{ padding:2px 8px; border-radius:4px; font-weight:600; font-size:11px; }}
    .badge.pass {{ background:#1a7f37; color:#fff; }}
    .badge.fail {{ background:#da3633; color:#fff; }}
    .conf {{ font-size:10px; color:#484f58; margin-left:4px; }}
    .diet {{ background:#1f6feb22; color:#58a6ff; padding:2px 6px; border-radius:4px; font-size:11px; }}
    .query-cell {{ max-width:250px; }}
    .reasoning-cell {{ max-width:300px; color:#8b949e; }}
    .row-fail {{ background:#da363308; }}
    .reviewed td {{ border-left:3px solid #1f6feb; }}
    .btn-flip {{ background:#da3633; color:#fff; border:none; padding:3px 8px; border-radius:4px; cursor:pointer; font-size:11px; }}
    .btn-flip:hover {{ background:#f85149; }}
    .btn-detail {{ background:#21262d; color:#c9d1d9; border:none; padding:3px 8px; border-radius:4px; cursor:pointer; font-size:11px; margin-left:4px; }}
    .btn-detail:hover {{ background:#30363d; }}
    #modal {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:100; }}
    #modal-inner {{ margin:40px auto; max-width:900px; max-height:85vh; overflow-y:auto; background:#161b22; border-radius:8px; padding:20px; }}
    #modal-inner h2 {{ margin-bottom:12px; font-size:16px; }}
    #modal-inner pre {{ white-space:pre-wrap; font-size:12px; background:#0d1117; padding:12px; border-radius:6px; margin:8px 0; max-height:400px; overflow-y:auto; }}
    .close {{ float:right; cursor:pointer; font-size:20px; color:#8b949e; }}
    .close:hover {{ color:#fff; }}
    .filter-bar {{ margin-bottom:8px; }}
    .filter-bar button {{ background:#21262d; color:#c9d1d9; border:none; padding:4px 12px; border-radius:4px; cursor:pointer; margin-right:4px; font-size:12px; }}
    .filter-bar button.active {{ background:#1f6feb; }}
    .save-btn {{ background:#1a7f37; color:#fff; border:none; padding:6px 16px; border-radius:6px; cursor:pointer; font-size:13px; font-weight:600; }}
    .save-btn:hover {{ background:#2ea043; }}
    .save-bar {{ position:fixed; bottom:0; left:0; right:0; background:#161b22; padding:10px 16px; border-top:1px solid #30363d; display:flex; align-items:center; gap:12px; z-index:50; }}
</style></head><body>
<h1>Dietary Label Review ({total} traces)</h1>
<div class="stats">
    <span>PASS: {passes}</span> <span>FAIL: {fails}</span>
    <span>Reviewed: <strong id="reviewed-count">{reviewed}</strong>/{total}</span>
    <br>{diet_stats}
</div>
<div class="filter-bar">
    <button onclick="filterRows('all')" class="active" id="fAll">All ({total})</button>
    <button onclick="filterRows('fail')" id="fFail">FAIL ({fails})</button>
    <button onclick="filterRows('pass')" id="fPass">PASS ({passes})</button>
</div>
<table><thead><tr>
    <th>#</th><th>Trace</th><th>Diet</th><th>Query</th><th>Label</th><th>Reasoning</th><th>Actions</th>
</tr></thead><tbody id="tbody">{rows}</tbody></table>
<div id="modal" onclick="if(event.target===this)closeModal()">
    <div id="modal-inner"></div>
</div>
<div class="save-bar">
    <button class="save-btn" onclick="saveAll()">Save Changes</button>
    <span id="save-status" style="color:#8b949e;font-size:12px;"></span>
</div>
<script>
const data = {json_data};
let changes = {{}};
function flipLabel(idx) {{
    const badge = document.getElementById('badge-'+idx);
    const row = document.getElementById('row-'+idx);
    const cur = badge.textContent;
    const newLabel = cur === 'PASS' ? 'FAIL' : 'PASS';
    badge.textContent = newLabel;
    badge.className = 'badge ' + newLabel.toLowerCase();
    row.classList.add('reviewed');
    if(newLabel==='FAIL') {{ row.classList.add('row-fail'); row.classList.remove('row-pass'); }}
    else {{ row.classList.remove('row-fail'); }}
    changes[idx] = newLabel;
    document.getElementById('save-status').textContent = Object.keys(changes).length + ' unsaved changes';
}}
function showDetail(idx) {{
    const d = data[idx];
    document.getElementById('modal-inner').innerHTML = `
        <span class="close" onclick="closeModal()">&times;</span>
        <h2>Trace ${{d.trace_id}} | ${{d.dietary_restriction}}</h2>
        <p><strong>Label:</strong> ${{d.label}} (${{d.confidence}})</p>
        <p><strong>Query:</strong></p><pre>${{d.query}}</pre>
        <p><strong>Response:</strong></p><pre>${{d.response}}</pre>
        <p><strong>Reasoning:</strong></p><pre>${{d.reasoning}}</pre>
    `;
    document.getElementById('modal').style.display = 'block';
}}
function closeModal() {{ document.getElementById('modal').style.display='none'; }}
function filterRows(mode) {{
    document.querySelectorAll('.filter-bar button').forEach(b=>b.classList.remove('active'));
    document.getElementById(mode==='all'?'fAll':mode==='fail'?'fFail':'fPass').classList.add('active');
    document.querySelectorAll('#tbody tr').forEach(tr=>{{
        if(mode==='all') tr.style.display='';
        else {{
            const badge = tr.querySelector('.badge');
            tr.style.display = badge && badge.textContent.toLowerCase()===mode ? '' : 'none';
        }}
    }});
}}
function saveAll() {{
    fetch('/save', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify(changes)}})
    .then(r=>r.json()).then(d=>{{
        document.getElementById('save-status').textContent = d.message;
        changes = {{}};
    }});
}}
document.addEventListener('keydown', e=>{{ if(e.key==='Escape') closeModal(); }});
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(build_html().encode())

    def do_POST(self):
        global df
        if self.path == "/save":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            for idx_str, new_label in body.items():
                idx = int(idx_str)
                df.at[idx, "label"] = new_label
                df.at[idx, "manual_reviewed"] = True
            df.to_csv(CSV_PATH, index=False)
            count = len(body)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"message": f"Saved {count} changes to CSV"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    print(f"Label review UI at http://localhost:{PORT}")
    print(f"Reading from {CSV_PATH}")
    print(f"Total: {len(df)} | PASS: {(df['label']=='PASS').sum()} | FAIL: {(df['label']=='FAIL').sum()}")
    HTTPServer(("", PORT), Handler).serve_forever()
