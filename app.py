"""Flask web server — Lab 20 Multi-Agent Research System.
Run:  python app.py
Open: http://localhost:5000
"""
from __future__ import annotations
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)
_running = False

HTML = r"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Lab 20 — Multi-Agent vs Single-Agent</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f0f4f8;color:#1e2a3a;min-height:100vh}

/* Header */
header{background:#1e2a3a;padding:14px 28px;display:flex;align-items:center;gap:12px}
header h1{font-size:17px;color:#fff;flex:1;font-weight:700}
.hbadge{font-size:11px;padding:3px 10px;border-radius:10px;font-weight:600}
.hbadge.green{background:#064e3b;color:#6ee7b7;border:1px solid #065f46}
.hbadge.blue{background:#1e3a5f;color:#93c5fd;border:1px solid #1e40af}

.main{max-width:1100px;margin:0 auto;padding:24px}

/* Config card */
.card{background:#fff;border-radius:12px;padding:20px;margin-bottom:18px;box-shadow:0 1px 4px rgba(0,0,0,.08)}
.section-label{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1.2px;color:#64748b;margin-bottom:12px}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:flex-end}
.field{display:flex;flex-direction:column;gap:4px;flex:1;min-width:160px}
.field label{font-size:11px;color:#64748b;font-weight:600}
input[type=text],select{background:#f8fafc;border:1px solid #e2e8f0;border-radius:7px;color:#1e2a3a;padding:8px 11px;font-size:13px;width:100%;transition:border .15s}
input[type=text]:focus,select:focus{outline:none;border-color:#6366f1;background:#fff}
.btn-run{padding:9px 22px;border-radius:7px;border:none;cursor:pointer;font-size:13px;font-weight:700;background:#6366f1;color:#fff;transition:background .15s}
.btn-run:hover{background:#4f46e5}.btn-run:disabled{background:#e2e8f0;color:#94a3b8;cursor:not-allowed}
.warn{background:#fffbeb;border:1px solid #fbbf24;border-radius:7px;padding:8px 12px;font-size:12px;color:#92400e;margin-top:8px;display:none}
.status-row{display:flex;align-items:center;gap:8px;font-size:12px;color:#94a3b8;margin-top:10px}
.dot{width:8px;height:8px;border-radius:50%;background:#e2e8f0;flex-shrink:0}
.dot.spin{background:#f59e0b;animation:pulse .9s infinite}
.dot.ok{background:#10b981}.dot.err{background:#ef4444}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}

/* KPI strip */
.kpi-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-bottom:18px}
.kpi{background:#fff;border-radius:10px;padding:14px 12px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.07)}
.kpi .v{font-size:22px;font-weight:800;line-height:1;margin-bottom:3px}
.kpi .l{font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:.7px}
.kpi.win .v{color:#10b981}.kpi.lose .v{color:#f59e0b}.kpi.neutral .v{color:#6366f1}

/* Tabs */
.tabs{display:flex;gap:0;border-bottom:2px solid #f1f5f9;margin-bottom:18px}
.tab{padding:9px 18px;cursor:pointer;font-size:13px;font-weight:600;color:#94a3b8;border-bottom:2px solid transparent;margin-bottom:-2px;transition:all .15s}
.tab.active{color:#6366f1;border-bottom-color:#6366f1}
.tab-panel{display:none}.tab-panel.active{display:block}

/* Trace flow */
.trace-scroll{overflow-x:auto;padding-bottom:8px}
.trace{display:flex;align-items:center;gap:0;min-width:600px}
.t-node{display:flex;flex-direction:column;align-items:center;gap:4px}
.t-box{border-radius:9px;padding:9px 14px;font-size:12px;font-weight:700;text-align:center;min-width:86px;cursor:pointer;border:2px solid;transition:transform .15s,box-shadow .15s;position:relative}
.t-box:hover{transform:translateY(-2px);box-shadow:0 6px 18px rgba(0,0,0,.12)}
.t-box .hint{font-size:9px;font-weight:400;opacity:.6;margin-top:2px;display:block}
.t-box.sup{border-color:#8b5cf6;color:#7c3aed;background:#f5f3ff}
.t-box.res{border-color:#0ea5e9;color:#0369a1;background:#f0f9ff}
.t-box.ana{border-color:#f59e0b;color:#b45309;background:#fffbeb}
.t-box.wri{border-color:#10b981;color:#047857;background:#f0fdf4}
.t-box.cri{border-color:#ec4899;color:#be185d;background:#fdf2f8}
.t-box.done{border-color:#94a3b8;color:#475569;background:#f8fafc}
.t-box.fail{border-color:#ef4444;color:#dc2626;background:#fef2f2}
.t-box.fb{border-color:#a855f7;color:#9333ea;background:#faf5ff}
.t-sub{font-size:9px;color:#94a3b8;text-align:center;line-height:1.4}
.t-arrow{font-size:20px;color:#cbd5e1;padding:0 2px;padding-bottom:22px}

/* Steps (prompt+output cards) */
.step-card{background:#fff;border-radius:10px;overflow:hidden;margin-bottom:10px;box-shadow:0 1px 3px rgba(0,0,0,.07)}
.step-header{display:flex;align-items:center;gap:10px;padding:10px 14px;cursor:pointer;user-select:none;transition:background .1s}
.step-header:hover{background:#f8fafc}
.step-icon{font-size:15px;flex-shrink:0}
.step-name{font-size:13px;font-weight:700;flex:1}
.step-pills{display:flex;gap:6px}
.pill{font-size:10px;font-weight:700;padding:2px 8px;border-radius:8px}
.pill.ok{background:#dcfce7;color:#166534}
.pill.fail{background:#fee2e2;color:#991b1b}
.pill.fb{background:#f3e8ff;color:#6b21a8}
.pill.gray{background:#f1f5f9;color:#475569}
.chev{color:#94a3b8;font-size:11px;transition:transform .2s;flex-shrink:0}
.chev.open{transform:rotate(90deg)}
.step-body{display:none;border-top:1px solid #f1f5f9}
.step-body.open{display:block}

/* Prompt/output sections inside step */
.psec{border-bottom:1px solid #f8fafc}
.psec-title{padding:7px 14px;font-size:11px;font-weight:700;display:flex;justify-content:space-between;cursor:pointer;transition:background .1s}
.psec-title:hover{background:#fafafa}
.psec-title.sys{color:#6366f1;background:#f8f7ff}
.psec-title.usr{color:#8b5cf6;background:#faf8ff}
.psec-title.out{color:#059669;background:#f0fdf8}
.psec-title.fb-info{color:#9333ea;background:#faf5ff}
.psec-body{display:none;padding:12px 14px;font-size:12px;font-family:'Consolas','Courier New',monospace;white-space:pre-wrap;line-height:1.6;background:#fdfdfe;max-height:360px;overflow-y:auto;color:#334155}
.psec-body.open{display:block}

/* Bar chart comparison */
.bar-section{background:#fff;border-radius:10px;padding:18px;box-shadow:0 1px 3px rgba(0,0,0,.07);margin-bottom:14px}
.metric-row{display:flex;align-items:center;gap:10px;margin-bottom:12px}
.metric-row:last-child{margin-bottom:0}
.m-label{font-size:11px;width:110px;flex-shrink:0;color:#475569;font-weight:600}
.bars-col{flex:1;display:flex;flex-direction:column;gap:4px}
.bar-line{display:flex;align-items:center;gap:8px}
.bar-track{flex:1;height:9px;background:#f1f5f9;border-radius:5px;overflow:hidden}
.bar-fill{height:100%;border-radius:5px;transition:width .4s}
.bar-fill.sg{background:#94a3b8}
.bar-fill.ma{background:#6366f1}
.bar-val{font-size:11px;font-weight:700;width:90px;text-align:right;white-space:nowrap}
.bar-win{color:#10b981}
.legend-row{display:flex;gap:16px;margin-top:12px}
.legend-item{font-size:10px;color:#64748b;display:flex;align-items:center;gap:5px}
.legend-dot{width:10px;height:4px;border-radius:2px}

/* Token table */
.token-table{width:100%;border-collapse:collapse;font-size:12px}
.token-table th{background:#f8fafc;padding:8px 12px;text-align:left;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#64748b;border-bottom:2px solid #e2e8f0}
.token-table td{padding:9px 12px;border-bottom:1px solid #f1f5f9}
.token-table tr:last-child td{font-weight:700;background:#fafbfc;border-bottom:none}
.agent-chip{display:inline-flex;align-items:center;gap:5px;font-weight:600}
.chip-dot{width:8px;height:8px;border-radius:2px}
.mini-track{display:inline-block;width:56px;height:6px;background:#f1f5f9;border-radius:3px;vertical-align:middle;overflow:hidden;margin-right:4px}
.mini-fill{height:100%;border-radius:3px}

/* Output panels */
.compare-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.out-panel{border-radius:10px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.07)}
.out-header{padding:10px 14px}
.out-header.sg{background:#f1f5f9;border-bottom:2px solid #cbd5e1}
.out-header.ma{background:#eef2ff;border-bottom:2px solid #a5b4fc}
.out-title{font-size:13px;font-weight:700}
.out-meta{font-size:10px;color:#64748b;margin-top:2px}
.out-body{background:#fff;padding:16px;height:460px;overflow-y:auto;font-size:12.5px;line-height:1.75;color:#374151}
.out-body h1,.out-body h2,.out-body h3{font-size:12.5px;font-weight:700;margin:12px 0 5px;color:#111}
.out-body h1:first-child,.out-body h2:first-child,.out-body h3:first-child{margin-top:0}
.out-body p{margin-bottom:8px}
.out-body ul,.out-body ol{padding-left:18px;margin-bottom:8px}
.out-body li{margin-bottom:3px}
.out-body strong{font-weight:700}
.out-body em{font-style:italic}
.out-body table{width:100%;border-collapse:collapse;font-size:11px;margin:8px 0}
.out-body th{background:#f8fafc;padding:5px 8px;text-align:left;font-size:10px;font-weight:700;border:1px solid #e2e8f0}
.out-body td{padding:5px 8px;border:1px solid #e2e8f0}

/* Verdict */
.verdict-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.verdict-card{border-radius:10px;padding:16px;font-size:13px;line-height:1.6}
.verdict-card.sg{background:#f8fafc;border:1px solid #e2e8f0}
.verdict-card.ma{background:#eef2ff;border:1px solid #a5b4fc}
.verdict-title{font-weight:800;font-size:14px;margin-bottom:8px}
.verdict-title.sg{color:#475569}.verdict-title.ma{color:#6366f1}
.note{font-size:10px;color:#94a3b8;margin-top:14px;line-height:1.5}

/* Report */
.report-pre{background:#fff;border-radius:10px;padding:20px;font-size:12px;font-family:'Consolas',monospace;white-space:pre-wrap;line-height:1.7;max-height:700px;overflow-y:auto;box-shadow:0 1px 3px rgba(0,0,0,.07)}

/* Errors */
.err-item{border-radius:8px;padding:10px 14px;margin-bottom:8px;font-size:12px;font-family:monospace}
.err-item.hard{background:#fef2f2;border:1px solid #fecaca;color:#991b1b}
.err-item.soft{background:#faf5ff;border:1px solid #e9d5ff;color:#7e22ce}
.empty-state{text-align:center;padding:40px;color:#94a3b8;font-size:13px}

hr.divider{border:none;border-top:1px solid #f1f5f9;margin:18px 0}
</style>
</head>
<body>

<header>
  <h1>🤖 Lab 20 — Multi-Agent Research System</h1>
  <span class="hbadge green">localhost:5000</span>
  <span class="hbadge blue">GPT-4o Ready</span>
</header>

<div class="main">

<!-- CONFIG -->
<div class="card">
  <div class="section-label">⚙️ Configuration</div>
  <div class="row" style="margin-bottom:10px">
    <div class="field" style="flex:3;min-width:300px">
      <label>Research Query</label>
      <input type="text" id="query" value="Research GraphRAG state-of-the-art, write a 500-word summary">
    </div>
  </div>
  <div class="row">
    <div class="field">
      <label>Mode</label>
      <select id="mode" onchange="onMode()">
        <option value="mock">🧪 Mock — no API cost</option>
        <option value="real">🌐 Real — GPT-4o</option>
      </select>
    </div>
    <div class="field">
      <label>Inject Failure (mock only)</label>
      <select id="fail_mode">
        <option value="none">✅ None — happy path</option>
        <option value="researcher">❌ Researcher fails → fallback</option>
        <option value="analyst">❌ Analyst fails → fallback</option>
        <option value="writer">❌ Writer fails → emergency</option>
        <option value="timeout">⏱ Timeout — all calls fail</option>
        <option value="bad_output">🚫 Bad output — empty string</option>
      </select>
    </div>
    <div class="field">
      <label>Critic Agent (bonus)</label>
      <select id="run_critic">
        <option value="true">✅ Run fact-check</option>
        <option value="false">⬜ Skip</option>
      </select>
    </div>
    <div style="display:flex;flex-direction:column;justify-content:flex-end">
      <button class="btn-run" id="run_btn" onclick="run()">▶ Run Benchmark</button>
    </div>
  </div>
  <div id="mode_warn" class="warn">⚠️ Real mode needs OPENAI_API_KEY in your .env file (or env variable). Mock mode is free.</div>
  <div class="status-row"><div class="dot" id="dot"></div><span id="status">Ready — choose mode and click Run</span></div>
</div>

<!-- KPI STRIP (hidden until run) -->
<div id="kpi_wrap" style="display:none">
  <div class="kpi-grid" id="kpi_grid"></div>
</div>

<!-- RESULTS -->
<div class="card" id="results" style="display:none;padding-bottom:0">
  <div class="tabs">
    <div class="tab active" onclick="tab('compare')">📄 Outputs</div>
    <div class="tab" onclick="tab('trace')">🔍 Trace</div>
    <div class="tab" onclick="tab('tokens')">💰 Tokens & Cost</div>
    <div class="tab" onclick="tab('verdict')">⚖️ Verdict</div>
    <div class="tab" onclick="tab('report')">📊 Report</div>
    <div class="tab" onclick="tab('errors')">🚨 Errors</div>
  </div>

  <!-- OUTPUTS TAB -->
  <div class="tab-panel active" id="tab-compare" style="padding:0 0 20px">
    <div class="compare-grid" style="padding:0 0 4px">
      <div class="out-panel">
        <div class="out-header sg">
          <div class="out-title">🔵 Single-Agent Output</div>
          <div class="out-meta" id="sg_meta"></div>
        </div>
        <div class="out-body" id="sg_body"></div>
      </div>
      <div class="out-panel">
        <div class="out-header ma">
          <div class="out-title">🟣 Multi-Agent Output</div>
          <div class="out-meta" id="ma_meta"></div>
        </div>
        <div class="out-body" id="ma_body"></div>
      </div>
    </div>
  </div>

  <!-- TRACE TAB -->
  <div class="tab-panel" id="tab-trace" style="padding-bottom:20px">
    <div class="section-label" style="margin-bottom:12px">Supervisor Routing Loop</div>
    <div class="trace-scroll"><div class="trace" id="trace_flow"></div></div>
    <hr class="divider">
    <div class="section-label" style="margin-bottom:12px">Step Details — System Prompt · User Prompt · Output</div>
    <div id="steps"></div>
  </div>

  <!-- TOKENS TAB -->
  <div class="tab-panel" id="tab-tokens" style="padding-bottom:20px">
    <div class="bar-section" style="margin-bottom:16px">
      <div class="section-label" style="margin-bottom:14px">Metric Comparison</div>
      <div id="bar_chart"></div>
      <div class="legend-row">
        <div class="legend-item"><div class="legend-dot" style="background:#94a3b8"></div>Single-Agent</div>
        <div class="legend-item"><div class="legend-dot" style="background:#6366f1"></div>Multi-Agent</div>
      </div>
    </div>
    <div class="section-label" style="margin-bottom:10px">Per-Agent Token & Cost Breakdown</div>
    <div style="background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.07)">
      <table class="token-table" id="token_table"></table>
    </div>
  </div>

  <!-- VERDICT TAB -->
  <div class="tab-panel" id="tab-verdict" style="padding-bottom:20px">
    <div class="verdict-grid" id="verdict_grid"></div>
    <p class="note" id="verdict_note"></p>
  </div>

  <!-- REPORT TAB -->
  <div class="tab-panel" id="tab-report" style="padding-bottom:20px">
    <pre class="report-pre" id="report_pre"></pre>
  </div>

  <!-- ERRORS TAB -->
  <div class="tab-panel" id="tab-errors" style="padding-bottom:20px">
    <div id="errors_div"></div>
  </div>

</div><!-- /results -->
</div><!-- /main -->

<script>
const AGENT_COLORS = {researcher:'#0ea5e9',analyst:'#f59e0b',writer:'#10b981',critic:'#ec4899',supervisor:'#8b5cf6'};
const AGENT_CLASS  = {researcher:'res',analyst:'ana',writer:'wri',critic:'cri',supervisor:'sup'};
const AGENT_EMOJI  = {researcher:'🔍',analyst:'📊',writer:'✍️',critic:'🔬',supervisor:'🎯'};

let _d = null;

function onMode(){
  const real = document.getElementById('mode').value==='real';
  document.getElementById('mode_warn').style.display = real?'block':'none';
  document.getElementById('fail_mode').disabled = real;
}

function tab(name){
  const names=['compare','trace','tokens','verdict','report','errors'];
  document.querySelectorAll('.tab').forEach((t,i)=>t.classList.toggle('active',names[i]===name));
  document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));
  document.getElementById('tab-'+name).classList.add('active');
}

async function run(){
  const btn=document.getElementById('run_btn');
  const dot=document.getElementById('dot');
  const status=document.getElementById('status');
  btn.disabled=true; dot.className='dot spin';
  status.textContent='Running pipeline… (real mode may take 30–60s)';
  document.getElementById('results').style.display='none';
  document.getElementById('kpi_wrap').style.display='none';
  try{
    const resp=await fetch('/api/run',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        query:document.getElementById('query').value,
        mode:document.getElementById('mode').value,
        fail_mode:document.getElementById('fail_mode').value,
        run_critic:document.getElementById('run_critic').value==='true'
      })
    });
    const d=await resp.json();
    if(d.error) throw new Error(d.error);
    _d=d; render(d);
    dot.className='dot ok'; status.textContent='Done ✓';
  }catch(e){
    dot.className='dot err'; status.textContent='Error: '+e.message;
  } finally{btn.disabled=false;}
}

function wc(t){return (t||'').trim().split(/\s+/).filter(Boolean).length;}
function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

function md2html(text){
  if(!text) return '';
  let t = text
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,'<em>$1</em>')
    .replace(/^### (.+)$/gm,'<h3>$1</h3>')
    .replace(/^## (.+)$/gm,'<h2>$1</h2>')
    .replace(/^# (.+)$/gm,'<h1>$1</h1>')
    .replace(/^\- (.+)$/gm,'<li>$1</li>')
    .replace(/^\d+\. (.+)$/gm,'<li>$1</li>');
  // wrap consecutive <li> in <ul>
  t = t.replace(/(<li>.*<\/li>\n?)+/g, m => '<ul>'+m+'</ul>');
  // paragraphs
  t = t.split(/\n\n+/).map(p=>{
    if(p.startsWith('<h')||p.startsWith('<ul')) return p;
    if(!p.trim()) return '';
    return '<p>'+p.replace(/\n/g,' ')+'</p>';
  }).join('');
  return t;
}

function render(d){
  renderKPI(d);
  renderOutputs(d);
  renderTrace(d);
  renderTokens(d);
  renderVerdict(d);
  document.getElementById('report_pre').textContent = d.report_md||'';
  renderErrors(d);
  document.getElementById('kpi_wrap').style.display='block';
  document.getElementById('results').style.display='block';
  tab('compare');
}

function renderKPI(d){
  const sm=d.single_metrics, mm=d.multi_metrics;
  const sgTok = d.sg_tokens||{in:sm.estimated_cost_usd?Math.round(sm.estimated_cost_usd/0.00015*1000):0,out:wc(d.single_answer)*4/3|0};
  const maTotal = d.agent_results.reduce((a,r)=>({in:a.in+(r.metadata.input_tokens||0),out:a.out+(r.metadata.output_tokens||0)}),{in:0,out:0});
  const qd = (mm.quality_score-sm.quality_score).toFixed(1);
  document.getElementById('kpi_grid').innerHTML=`
    <div class="kpi ${sm.latency_seconds<mm.latency_seconds?'win':'lose'}">
      <div class="v">${sm.latency_seconds.toFixed(1)}s</div><div class="l">Single latency</div></div>
    <div class="kpi ${mm.latency_seconds<sm.latency_seconds?'win':'lose'}">
      <div class="v">${mm.latency_seconds.toFixed(1)}s</div><div class="l">Multi latency</div></div>
    <div class="kpi ${sm.quality_score>mm.quality_score?'win':'neutral'}">
      <div class="v">${sm.quality_score}</div><div class="l">Single quality</div></div>
    <div class="kpi ${mm.quality_score>=sm.quality_score?'win':'neutral'}">
      <div class="v">${mm.quality_score}</div><div class="l">Multi quality</div></div>
    <div class="kpi ${parseFloat(qd)>0?'win':'lose'}">
      <div class="v">${parseFloat(qd)>0?'+':''}${qd}</div><div class="l">Quality delta</div></div>
    <div class="kpi neutral">
      <div class="v">${mm.estimated_cost_usd?'$'+mm.estimated_cost_usd.toFixed(4):'—'}</div><div class="l">Multi cost</div></div>
  `;
}

function renderOutputs(d){
  const sm=d.single_metrics, mm=d.multi_metrics;
  const sgW=wc(d.single_answer), maW=wc(d.multi_answer);
  document.getElementById('sg_meta').textContent =
    `1 LLM call · ${sm.latency_seconds.toFixed(1)}s · ${sgW} words · quality=${sm.quality_score}/10`;
  document.getElementById('ma_meta').textContent =
    `${d.agent_results.length} agents · ${mm.latency_seconds.toFixed(1)}s · ${maW} words · quality=${mm.quality_score}/10`;
  document.getElementById('sg_body').innerHTML = md2html(d.single_answer||'(no answer)');
  document.getElementById('ma_body').innerHTML = md2html(d.multi_answer||'(no answer)');
}

function renderTrace(d){
  const route = d.route||[];
  const errs = new Set((d.multi_errors||[]).map(e=>{const m=e.match(/^(\w+) FAILED/);return m?m[1]:null;}).filter(Boolean));
  let flow='';
  const box=(cls,label,sub,key)=>
    `<div class="t-node"><div class="t-box ${cls}" onclick="openStep('${key}')">${label}<span class="hint">click</span></div><div class="t-sub">${sub}</div></div>`;
  const arrow=`<span class="t-arrow">→</span>`;

  // Supervisor iter 0
  flow += box('sup','🎯 Sup','iter 0<br>routing','sup_0');
  const pipeline = route.length ? route : ['researcher','analyst','writer'];
  pipeline.forEach((ag,i)=>{
    const failed=errs.has(ag);
    flow+=arrow;
    if(failed){
      flow+=`<div class="t-node">
        <div class="t-box fail" onclick="openStep('${ag}')">${AGENT_EMOJI[ag]||'🤖'} ${ag}<span class="hint">click</span></div>
        <div class="t-sub">FAILED<br>↩ fallback</div></div>`;
    } else {
      const meta=(d.agent_results||[]).find(r=>r.agent===ag)?.metadata||{};
      const sub=meta.input_tokens?`in=${meta.input_tokens}<br>out=${meta.output_tokens}`:`success`;
      flow+=box(AGENT_CLASS[ag]||'res',`${AGENT_EMOJI[ag]||'🤖'} ${ag}`,sub,ag);
    }
    flow+=arrow;
    flow+=box('sup',`🎯 Sup`,`iter ${i+1}<br>routing`,`sup_${i+1}`);
  });
  flow+=arrow;
  flow+=box('done','🏁 Done','all complete','done');
  document.getElementById('trace_flow').innerHTML=flow;

  // Step cards
  let html='';
  const agentResults=d.agent_results||[];
  agentResults.forEach((r,i)=>{
    const meta=r.metadata||{};
    const failed=errs.has(r.agent);
    const isFb=(r.content||'').includes('[FALLBACK');
    const cls=failed?'fail':isFb?'fb':'ok';
    const label=failed?'FAILED':isFb?'FALLBACK':'SUCCESS';
    const cost=meta.cost_usd!=null?`$${meta.cost_usd.toFixed(5)}`:'—';
    const inTok=meta.input_tokens!=null?`in=${meta.input_tokens}`:'';
    const outTok=meta.output_tokens!=null?`out=${meta.output_tokens}`:'';

    html+=`<div class="step-card" id="step-${r.agent}">
      <div class="step-header" onclick="toggleStep(${i})">
        <span class="step-icon">${AGENT_EMOJI[r.agent]||'🤖'}</span>
        <span class="step-name">${r.agent.toUpperCase()}</span>
        <div class="step-pills">
          <span class="pill ${cls}">${label}</span>
          ${inTok?`<span class="pill gray">${inTok} / ${outTok}</span>`:''}
          ${cost!=='—'?`<span class="pill gray">${cost}</span>`:''}
          ${meta.latency_s!=null?`<span class="pill gray">${meta.latency_s}s</span>`:''}
        </div>
        <span class="chev" id="chev-${i}">▶</span>
      </div>
      <div class="step-body" id="body-${i}">
        ${meta.system_prompt?`
        <div class="psec">
          <div class="psec-title sys" onclick="toggleSec('sp${i}')">
            🔵 System Prompt <span style="font-weight:400;color:#94a3b8">${wc(meta.system_prompt)} words</span><span>▼</span>
          </div>
          <div class="psec-body" id="sp${i}">${esc(meta.system_prompt)}</div>
        </div>`:''}
        ${meta.user_prompt?`
        <div class="psec">
          <div class="psec-title usr" onclick="toggleSec('up${i}')">
            🟣 User Prompt <span style="font-weight:400;color:#94a3b8">${wc(meta.user_prompt)} words — includes previous agent output</span><span>▼</span>
          </div>
          <div class="psec-body" id="up${i}">${esc(meta.user_prompt)}</div>
        </div>`:''}
        <div class="psec">
          <div class="psec-title out" onclick="toggleSec('out${i}')">
            🟢 Output <span style="font-weight:400;color:#94a3b8">${wc(r.content)} words</span><span>▼</span>
          </div>
          <div class="psec-body open" id="out${i}">${esc(r.content||'(empty)')}</div>
        </div>
        ${(failed||isFb)?`
        <div class="psec">
          <div class="psec-title fb-info">↩️ Fallback triggered — pipeline injected placeholder and continued</div>
        </div>`:''}
      </div>
    </div>`;
  });
  document.getElementById('steps').innerHTML=html||'<div class="empty-state">No agent steps</div>';
}

function toggleStep(i){
  document.getElementById('body-'+i).classList.toggle('open');
  document.getElementById('chev-'+i).classList.toggle('open');
}
function toggleSec(id){ document.getElementById(id).classList.toggle('open'); }

function openStep(key){
  // find and open the step card for this agent
  const el=document.getElementById('step-'+key);
  if(el){ tab('trace'); el.scrollIntoView({behavior:'smooth',block:'center'}); el.querySelector('.step-header')?.click(); }
}

function renderTokens(d){
  const sm=d.single_metrics, mm=d.multi_metrics;
  const sgLat=sm.latency_seconds, maLat=mm.latency_seconds;
  const maxLat=Math.max(sgLat,maLat)||1;
  const sgCost=sm.estimated_cost_usd||0, maCost=mm.estimated_cost_usd||0;
  const maxCost=Math.max(sgCost,maCost)||1;
  const agentResults=d.agent_results||[];
  const maOut=agentResults.reduce((a,r)=>a+(r.metadata.output_tokens||0),0);
  const sgOut=wc(d.single_answer)*4/3|0;
  const maxOut=Math.max(sgOut,maOut)||1;
  document.getElementById('bar_chart').innerHTML=`
    <div class="metric-row">
      <span class="m-label">Latency (s)</span>
      <div class="bars-col">
        <div class="bar-line"><div class="bar-track"><div class="bar-fill sg" style="width:${sgLat/maxLat*100}%"></div></div>
          <span class="bar-val ${sgLat<maLat?'bar-win':''}">${sgLat.toFixed(2)}s ${sgLat<maLat?'✓':''}</span></div>
        <div class="bar-line"><div class="bar-track"><div class="bar-fill ma" style="width:${maLat/maxLat*100}%"></div></div>
          <span class="bar-val ${maLat<sgLat?'bar-win':''}">${maLat.toFixed(2)}s ${maLat<sgLat?'✓':''}</span></div>
      </div>
    </div>
    <div class="metric-row">
      <span class="m-label">Cost (USD)</span>
      <div class="bars-col">
        <div class="bar-line"><div class="bar-track"><div class="bar-fill sg" style="width:${sgCost/maxCost*100}%"></div></div>
          <span class="bar-val ${sgCost<maCost?'bar-win':''}">${sgCost?'$'+sgCost.toFixed(4):'—'} ${sgCost&&sgCost<maCost?'✓':''}</span></div>
        <div class="bar-line"><div class="bar-track"><div class="bar-fill ma" style="width:${maCost/maxCost*100}%"></div></div>
          <span class="bar-val">${maCost?'$'+maCost.toFixed(4):'—'}</span></div>
      </div>
    </div>
    <div class="metric-row">
      <span class="m-label">Tokens Out</span>
      <div class="bars-col">
        <div class="bar-line"><div class="bar-track"><div class="bar-fill sg" style="width:${sgOut/maxOut*100}%"></div></div>
          <span class="bar-val">~${sgOut.toLocaleString()}</span></div>
        <div class="bar-line"><div class="bar-track"><div class="bar-fill ma" style="width:${maOut/maxOut*100}%"></div></div>
          <span class="bar-val bar-win">${maOut.toLocaleString()} ✓</span></div>
      </div>
    </div>
    <div class="metric-row">
      <span class="m-label">Quality /10</span>
      <div class="bars-col">
        <div class="bar-line"><div class="bar-track"><div class="bar-fill sg" style="width:${sm.quality_score*10}%"></div></div>
          <span class="bar-val">${sm.quality_score}</span></div>
        <div class="bar-line"><div class="bar-track"><div class="bar-fill ma" style="width:${mm.quality_score*10}%"></div></div>
          <span class="bar-val bar-win">${mm.quality_score} ✓</span></div>
      </div>
    </div>
  `;
  // Token table
  const totalIn=agentResults.reduce((a,r)=>a+(r.metadata.input_tokens||0),0);
  const totalOut=agentResults.reduce((a,r)=>a+(r.metadata.output_tokens||0),0);
  const totalCost=agentResults.reduce((a,r)=>a+(r.metadata.cost_usd||0),0);
  let rows='<thead><tr><th>Agent</th><th>Tokens In</th><th>Tokens Out</th><th>Cost (USD)</th><th>% of cost</th></tr></thead><tbody>';
  agentResults.forEach(r=>{
    const meta=r.metadata||{};
    const pct=totalCost>0?Math.round((meta.cost_usd||0)/totalCost*100):0;
    const col=AGENT_COLORS[r.agent]||'#94a3b8';
    rows+=`<tr>
      <td><span class="agent-chip"><span class="chip-dot" style="background:${col}"></span>${r.agent}</span></td>
      <td>${(meta.input_tokens||'—').toLocaleString()}</td>
      <td>${(meta.output_tokens||'—').toLocaleString()}</td>
      <td>${meta.cost_usd!=null?'$'+meta.cost_usd.toFixed(5):'—'}</td>
      <td><span class="mini-track"><span class="mini-fill" style="background:${col};width:${pct}%"></span></span>${pct}%</td>
    </tr>`;
  });
  rows+=`<tr><td>Total</td><td>${totalIn.toLocaleString()}</td><td>${totalOut.toLocaleString()}</td><td>$${totalCost.toFixed(5)}</td><td>100%</td></tr>`;
  rows+='</tbody>';
  document.getElementById('token_table').innerHTML=rows;
}

function renderVerdict(d){
  const sm=d.single_metrics, mm=d.multi_metrics;
  const sgW=wc(d.single_answer), maW=wc(d.multi_answer);
  const latRatio=(mm.latency_seconds/Math.max(sm.latency_seconds,.01)).toFixed(1);
  const costRatio=sm.estimated_cost_usd&&mm.estimated_cost_usd?(mm.estimated_cost_usd/sm.estimated_cost_usd).toFixed(1):'N/A';
  document.getElementById('verdict_grid').innerHTML=`
    <div class="verdict-card sg">
      <div class="verdict-title sg">🔵 Single-Agent thắng về</div>
      Latency nhanh hơn <strong>${latRatio}×</strong> (${sm.latency_seconds.toFixed(1)}s vs ${mm.latency_seconds.toFixed(1)}s)<br>
      ${costRatio!=='N/A'?`Cost thấp hơn <strong>${costRatio}×</strong><br>`:''}
      Phù hợp: query nhanh, cost-sensitive, single-hop
    </div>
    <div class="verdict-card ma">
      <div class="verdict-title ma">🟣 Multi-Agent thắng về</div>
      Output dài hơn: <strong>${maW} vs ${sgW} words</strong><br>
      Quality score cao hơn: <strong>${mm.quality_score} vs ${sm.quality_score}</strong>/10<br>
      Có analyst layer — insight sâu hơn, dễ debug qua trace
    </div>
  `;
  document.getElementById('verdict_note').textContent =
    '⚠ Trade-off: multi-agent tốt hơn cho sensemaking queries cần tổng hợp đa nguồn và phân tích sâu. '
    +'Single-agent đủ cho factual Q&A ngắn hoặc khi latency/cost là ưu tiên.';
}

function renderErrors(d){
  const all=[
    ...(d.single_errors||[]).map(e=>({src:'single',msg:e})),
    ...(d.multi_errors||[]).map(e=>({src:'multi',msg:e}))
  ];
  if(!all.length){
    document.getElementById('errors_div').innerHTML='<div class="empty-state">✅ No errors — all agents completed successfully</div>';
    return;
  }
  document.getElementById('errors_div').innerHTML=all.map(({src,msg})=>{
    const isFb=msg.includes('Simulated')||msg.includes('injected')||msg.includes('FALLBACK');
    return `<div class="err-item ${isFb?'soft':'hard'}"><strong>[${src}]</strong> ${esc(msg)}${isFb?'<br><small>↩️ Fallback was injected — pipeline continued in degraded mode</small>':''}</div>`;
  }).join('');
}
</script>
</body>
</html>"""

# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/run", methods=["POST"])
def api_run():
    global _running
    if _running:
        return jsonify({"error": "Already running — please wait"}), 429
    _running = True
    try:
        body       = request.get_json(force=True)
        query      = body.get("query", "Research GraphRAG state-of-the-art")
        use_mock   = body.get("mode", "mock") == "mock"
        fail_mode  = body.get("fail_mode", "none")
        run_critic = body.get("run_critic", True)
        model      = "gpt-4o"  # always gpt-4o for real mode

        from multi_agent_research_lab.core.schemas import ResearchQuery
        from multi_agent_research_lab.core.state import ResearchState
        from multi_agent_research_lab.evaluation.benchmark import run_benchmark
        from multi_agent_research_lab.evaluation.report import render_markdown_report
        from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow, SingleAgentWorkflow

        openai_key  = os.getenv("OPENAI_API_KEY") if not use_mock else None
        tavily_key  = os.getenv("TAVILY_API_KEY")  if not use_mock else None

        if not use_mock and not openai_key:
            return jsonify({"error": "OPENAI_API_KEY not set. Use mock mode or add key to .env"}), 400

        # --- Single-agent ---
        sw = SingleAgentWorkflow(use_mock=use_mock, openai_api_key=openai_key,
                                  model=model)
        ss, sm = run_benchmark("Single-Agent", query,
            lambda q: sw.run(ResearchState(request=ResearchQuery(query=q))),
            notes="1 LLM call")

        # --- Multi-agent ---
        mw = MultiAgentWorkflow(use_mock=use_mock, fail_mode=fail_mode,
                                run_critic=run_critic, openai_api_key=openai_key,
                                tavily_api_key=tavily_key,
                                model=model)
        ms, mm = run_benchmark("Multi-Agent", query,
            lambda q: mw.run(ResearchState(request=ResearchQuery(query=q))),
            notes=f"fail_mode={fail_mode}" if fail_mode != "none" else "researcher+analyst+writer")

        ss._run_name = "single"   # type: ignore[attr-defined]
        ms._run_name = "multi"    # type: ignore[attr-defined]

        report_md = render_markdown_report([sm, mm], states=[ss, ms])
        os.makedirs("reports", exist_ok=True)
        with open("reports/benchmark_report.md", "w", encoding="utf-8") as f:
            f.write(report_md)

        return jsonify({
            "single_metrics": sm.model_dump(mode="json"),
            "multi_metrics":  mm.model_dump(mode="json"),
            "single_answer":  ss.final_answer,
            "multi_answer":   ms.final_answer,
            "single_errors":  ss.errors,
            "multi_errors":   ms.errors,
            "route": [r.value if hasattr(r,"value") else str(r) for r in ms.route_history],
            "multi_trace":    ms.trace,
            "agent_results":  [r.model_dump(mode="json") for r in ms.agent_results],
            "report_md":      report_md,
        })
    except Exception as exc:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(exc)}), 500
    finally:
        _running = False


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"\n🚀  http://localhost:{port}")
    print("   Mock  → fail_mode injection, zero cost")
    print("   Real  → set OPENAI_API_KEY in .env, uses gpt-4o\n")
    app.run(host="0.0.0.0", port=port, debug=False)
