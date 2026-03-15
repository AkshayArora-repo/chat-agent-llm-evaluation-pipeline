#!/usr/bin/env python3
"""Local web UI to review judge predictions from the dev/test evaluation.

Usage:
    python scripts/review_predictions.py                  # defaults to dev
    python scripts/review_predictions.py --split test
"""

import json
import argparse
import functools
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

print = functools.partial(print, flush=True)

SCRIPT_DIR = Path(__file__).resolve().parent
HW3_DIR = SCRIPT_DIR.parent
RESULTS_DIR = HW3_DIR / "results"

PORT = 8890


def build_html(predictions: list, split_name: str) -> str:
    total = len(predictions)
    correct = sum(1 for p in predictions if p["true_label"] == p["predicted_label"])
    fn = [p for p in predictions if p["true_label"] == "PASS" and p["predicted_label"] == "FAIL"]
    fp = [p for p in predictions if p["true_label"] == "FAIL" and p["predicted_label"] == "PASS"]

    tp = sum(1 for p in predictions if p["true_label"] == "PASS" and p["predicted_label"] == "PASS")
    tn = sum(1 for p in predictions if p["true_label"] == "FAIL" and p["predicted_label"] == "FAIL")
    n_pass = sum(1 for p in predictions if p["true_label"] == "PASS")
    n_fail = sum(1 for p in predictions if p["true_label"] == "FAIL")
    tpr = tp / n_pass if n_pass else 0
    tnr = tn / n_fail if n_fail else 0

    json_data = json.dumps(predictions)

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Judge Predictions — {split_name.upper()}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f1117; color: #e0e0e0; }}
  .header {{ background: #1a1d27; padding: 20px 30px; border-bottom: 1px solid #2a2d37; position: sticky; top: 0; z-index: 100; }}
  .header h1 {{ font-size: 20px; margin-bottom: 12px; color: #fff; }}
  .metrics {{ display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 12px; }}
  .metric {{ background: #252830; padding: 10px 16px; border-radius: 8px; min-width: 120px; }}
  .metric .val {{ font-size: 22px; font-weight: 700; }}
  .metric .lbl {{ font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }}
  .metric.good .val {{ color: #4ade80; }}
  .metric.warn .val {{ color: #fbbf24; }}
  .metric.bad .val {{ color: #f87171; }}
  .filters {{ display: flex; gap: 8px; flex-wrap: wrap; }}
  .filters button {{ padding: 6px 14px; border-radius: 6px; border: 1px solid #3a3d47; background: #252830; color: #ccc; cursor: pointer; font-size: 13px; }}
  .filters button.active {{ background: #3b82f6; color: #fff; border-color: #3b82f6; }}
  .filters button:hover {{ background: #333640; }}
  .filters button.active:hover {{ background: #2563eb; }}
  .container {{ padding: 20px 30px; }}
  .card {{ background: #1a1d27; border: 1px solid #2a2d37; border-radius: 10px; margin-bottom: 14px; overflow: hidden; }}
  .card.false-neg {{ border-left: 4px solid #fbbf24; }}
  .card.false-pos {{ border-left: 4px solid #f87171; }}
  .card.correct {{ border-left: 4px solid #4ade80; }}
  .card-header {{ padding: 14px 18px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; }}
  .card-header:hover {{ background: #22252f; }}
  .card-left {{ display: flex; gap: 12px; align-items: center; flex: 1; }}
  .badge {{ padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase; }}
  .badge.pass {{ background: #064e3b; color: #4ade80; }}
  .badge.fail {{ background: #7f1d1d; color: #fca5a5; }}
  .badge.fn {{ background: #78350f; color: #fbbf24; }}
  .badge.fp {{ background: #7f1d1d; color: #f87171; }}
  .trace-id {{ font-family: monospace; color: #888; font-size: 12px; min-width: 60px; }}
  .diet {{ color: #93c5fd; font-size: 13px; min-width: 140px; }}
  .query-preview {{ color: #ccc; font-size: 13px; flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .card-body {{ padding: 0 18px 16px 18px; display: none; }}
  .card.open .card-body {{ display: block; }}
  .field {{ margin-top: 12px; }}
  .field-label {{ font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }}
  .field-value {{ font-size: 13px; line-height: 1.6; color: #ddd; background: #252830; padding: 10px 14px; border-radius: 6px; white-space: pre-wrap; max-height: 300px; overflow-y: auto; }}
  .verdict {{ display: flex; gap: 16px; margin-top: 12px; }}
  .verdict-box {{ flex: 1; padding: 10px 14px; border-radius: 6px; }}
  .verdict-box.truth {{ background: #1e293b; }}
  .verdict-box.pred {{ background: #1e293b; }}
  .verdict-box .v-label {{ font-size: 11px; color: #888; text-transform: uppercase; }}
  .verdict-box .v-value {{ font-size: 16px; font-weight: 700; margin-top: 2px; }}
  .verdict-box .v-value.pass {{ color: #4ade80; }}
  .verdict-box .v-value.fail {{ color: #f87171; }}
  .count {{ color: #888; font-size: 13px; margin-left: 10px; }}
</style>
</head>
<body>
<div class="header">
  <h1>Judge Predictions — {split_name.upper()} Set</h1>
  <div class="metrics">
    <div class="metric {'good' if tpr > 0.9 else 'warn' if tpr > 0.75 else 'bad'}"><div class="val">{tpr:.1%}</div><div class="lbl">TPR</div></div>
    <div class="metric {'good' if tnr > 0.9 else 'warn' if tnr > 0.75 else 'bad'}"><div class="val">{tnr:.1%}</div><div class="lbl">TNR</div></div>
    <div class="metric"><div class="val">{correct}/{total}</div><div class="lbl">Correct</div></div>
    <div class="metric {'bad' if len(fp) > 0 else 'good'}"><div class="val">{len(fp)}</div><div class="lbl">False Pos (missed!)</div></div>
    <div class="metric {'warn' if len(fn) > 5 else 'good'}"><div class="val">{len(fn)}</div><div class="lbl">False Neg (strict)</div></div>
  </div>
  <div class="filters">
    <button class="active" onclick="filterCards('all')">All <span class="count" id="count-all">{total}</span></button>
    <button onclick="filterCards('false-neg')">False Negatives <span class="count">{len(fn)}</span></button>
    <button onclick="filterCards('false-pos')">False Positives <span class="count">{len(fp)}</span></button>
    <button onclick="filterCards('correct')">Correct <span class="count">{correct}</span></button>
  </div>
</div>
<div class="container" id="cards"></div>
<script>
const data = {json_data};

function getCategory(p) {{
  if (p.true_label === 'PASS' && p.predicted_label === 'FAIL') return 'false-neg';
  if (p.true_label === 'FAIL' && p.predicted_label === 'PASS') return 'false-pos';
  return 'correct';
}}

function renderCards(filter) {{
  const container = document.getElementById('cards');
  container.innerHTML = '';
  
  // Sort: false-pos first, then false-neg, then correct
  const order = {{'false-pos': 0, 'false-neg': 1, 'correct': 2}};
  const sorted = [...data].sort((a, b) => order[getCategory(a)] - order[getCategory(b)]);
  
  sorted.forEach((p, i) => {{
    const cat = getCategory(p);
    if (filter !== 'all' && cat !== filter) return;
    
    const catLabel = cat === 'false-neg' ? 'FN' : cat === 'false-pos' ? 'FP' : '';
    const catBadge = catLabel ? `<span class="badge ${{cat === 'false-neg' ? 'fn' : 'fp'}}">${{catLabel}}</span>` : '';
    
    const card = document.createElement('div');
    card.className = `card ${{cat}}`;
    card.dataset.category = cat;
    card.innerHTML = `
      <div class="card-header" onclick="this.parentElement.classList.toggle('open')">
        <div class="card-left">
          <span class="trace-id">${{p.trace_id}}</span>
          <span class="diet">${{p.dietary_restriction}}</span>
          ${{catBadge}}
          <span class="badge ${{p.true_label.toLowerCase()}}">${{p.true_label}}</span>
          <span style="color:#666">→</span>
          <span class="badge ${{p.predicted_label.toLowerCase()}}">${{p.predicted_label}}</span>
          <span class="query-preview">${{p.query}}</span>
        </div>
      </div>
      <div class="card-body">
        <div class="field">
          <div class="field-label">Query</div>
          <div class="field-value">${{p.query}}</div>
        </div>
        <div class="verdict">
          <div class="verdict-box truth">
            <div class="v-label">Ground Truth</div>
            <div class="v-value ${{p.true_label.toLowerCase()}}">${{p.true_label}}</div>
          </div>
          <div class="verdict-box pred">
            <div class="v-label">Judge Said</div>
            <div class="v-value ${{p.predicted_label.toLowerCase()}}">${{p.predicted_label}}</div>
          </div>
        </div>
        <div class="field">
          <div class="field-label">Judge Reasoning</div>
          <div class="field-value">${{p.reasoning}}</div>
        </div>
      </div>
    `;
    container.appendChild(card);
  }});
}}

function filterCards(filter) {{
  document.querySelectorAll('.filters button').forEach(b => b.classList.remove('active'));
  event.target.closest('button').classList.add('active');
  renderCards(filter);
}}

renderCards('all');
</script>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    html_content = ""

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(self.html_content.encode())

    def log_message(self, format, *args):
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    args = parser.parse_args()

    preds_path = RESULTS_DIR / f"{args.split}_predictions.json"
    if not preds_path.exists():
        print(f"ERROR: {preds_path} not found. Run evaluate_judge.py --split {args.split} first.")
        return

    with open(preds_path) as f:
        predictions = json.load(f)

    print(f"Loaded {len(predictions)} predictions from {preds_path.name}")

    Handler.html_content = build_html(predictions, args.split)

    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Review UI running at http://localhost:{PORT}")
    print("Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
