#!/usr/bin/env python3
"""SmartGrow Mini — Веб-дашборд"""

from flask import Flask, render_template_string, jsonify
from flask_socketio import SocketIO
import sqlite3, threading, time

app      = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")
DB       = "/home/smartgrow/data/smartgrow.db"

HTML = """<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SmartGrow Mini</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.6.1/socket.io.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Exo+2:wght@300;600&display=swap');
:root{--bg:#080f08;--bg2:#0d1a0d;--green:#00ff88;--blue:#44aaff;
      --purple:#cc44ff;--amber:#ffaa00;--red:#ff4444;--dim:#334433;}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--bg);color:var(--green);font-family:'Exo 2',sans-serif;min-height:100vh;}
body::before{content:'';position:fixed;inset:0;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,
  rgba(0,255,136,.015) 2px,rgba(0,255,136,.015) 4px);pointer-events:none;z-index:0;}
header{padding:16px 24px;border-bottom:1px solid #0d2010;
       display:flex;justify-content:space-between;align-items:center;position:relative;z-index:1;}
h1{font-family:'Share Tech Mono',monospace;font-size:1.3rem;
   color:var(--green);text-shadow:0 0 20px var(--green);letter-spacing:3px;}
.dot{width:9px;height:9px;border-radius:50%;background:var(--green);
     box-shadow:0 0 10px var(--green);animation:pulse 2s infinite;display:inline-block;margin-right:6px;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
      gap:14px;padding:20px;position:relative;z-index:1;}
.card{background:var(--bg2);border:1px solid var(--dim);border-radius:10px;
      padding:18px;transition:.3s;}
.card:hover{border-color:var(--green);box-shadow:0 0 18px rgba(0,255,136,.08);}
.lbl{font-size:.7rem;letter-spacing:2px;color:var(--dim);text-transform:uppercase;margin-bottom:8px;}
.val{font-family:'Share Tech Mono',monospace;font-size:2rem;font-weight:600;}
.unit{font-size:.8rem;color:var(--dim);margin-left:3px;}
.soil .val{color:var(--green);text-shadow:0 0 10px var(--green);}
.temp .val,.hum .val{color:var(--blue);text-shadow:0 0 10px var(--blue);}
.pump .val{color:var(--amber);text-shadow:0 0 10px var(--amber);}
.uv   .val{color:var(--purple);text-shadow:0 0 10px var(--purple);}
.bar-wrap{height:4px;background:#0d2010;border-radius:2px;margin-top:8px;}
.bar{height:100%;border-radius:2px;transition:width .5s;}
.badge{display:inline-block;padding:3px 10px;border-radius:16px;
       font-size:.75rem;font-family:'Share Tech Mono',monospace;letter-spacing:1px;margin-top:8px;}
.on{background:rgba(0,255,136,.12);color:var(--green);border:1px solid var(--green);}
.off{background:rgba(51,68,51,.2);color:var(--dim);border:1px solid var(--dim);}
.section{padding:0 20px 20px;position:relative;z-index:1;}
.box{background:var(--bg2);border:1px solid var(--dim);border-radius:10px;padding:18px;}
.box h3{font-size:.75rem;letter-spacing:2px;color:var(--dim);margin-bottom:14px;text-transform:uppercase;}
.ev-list{max-height:180px;overflow-y:auto;}
.ev{font-family:'Share Tech Mono',monospace;font-size:.78rem;padding:5px 0;
    border-bottom:1px solid #0d1a0d;color:#668866;}
.ev .t{color:var(--dim);margin-right:10px;}
.ev.pump{color:var(--amber)}.ev.uv{color:var(--purple)}
footer{text-align:center;padding:14px;color:var(--dim);font-size:.72rem;
       font-family:'Share Tech Mono',monospace;letter-spacing:1px;border-top:1px solid #0d2010;}
</style>
</head>
<body>
<header>
  <h1>🌱 SmartGrow Mini</h1>
  <div><span class="dot"></span><span id="time" style="font-size:.82rem;color:var(--dim)"></span></div>
</header>

<div class="grid">
  <div class="card soil">
    <div class="lbl">Ґрунт 1</div>
    <div><span class="val" id="s1">—</span><span class="unit">%</span></div>
    <div class="bar-wrap"><div class="bar" id="b1" style="background:var(--green);width:0"></div></div>
  </div>
  <div class="card soil">
    <div class="lbl">Ґрунт 2</div>
    <div><span class="val" id="s2">—</span><span class="unit">%</span></div>
    <div class="bar-wrap"><div class="bar" id="b2" style="background:var(--green);width:0"></div></div>
  </div>
  <div class="card temp">
    <div class="lbl">Температура</div>
    <div><span class="val" id="temp">—</span><span class="unit">°C</span></div>
  </div>
  <div class="card hum">
    <div class="lbl">Вологість повітря</div>
    <div><span class="val" id="hum">—</span><span class="unit">%</span></div>
  </div>
  <div class="card pump">
    <div class="lbl">Насос</div>
    <div class="val" id="pv">—</div>
    <div id="pb"></div>
    <div style="margin-top:6px;font-size:.72rem;color:var(--dim)">Полив: <span id="lw">—</span></div>
  </div>
  <div class="card uv">
    <div class="lbl">UV LED</div>
    <div class="val" id="uv">—</div>
    <div id="ub"></div>
  </div>
</div>

<div class="section">
  <div class="box">
    <h3>📊 Вологість ґрунту — остання година</h3>
    <canvas id="chart" height="75"></canvas>
  </div>
</div>

<div class="section">
  <div class="box">
    <h3>📋 Останні події</h3>
    <div class="ev-list" id="evs"></div>
  </div>
</div>

<footer>SmartGrow Mini · Infomatrix Ukraine 2026 · Raspberry Pi 4B + DietPi</footer>

<script>
const socket = io();
const chart  = new Chart(document.getElementById('chart').getContext('2d'), {
  type:'line',
  data:{
    labels:[],
    datasets:[
      {label:'Ґрунт 1',data:[],borderColor:'#00ff88',backgroundColor:'rgba(0,255,136,.04)',tension:.4,pointRadius:2,borderWidth:2},
      {label:'Ґрунт 2',data:[],borderColor:'#44aaff',backgroundColor:'rgba(68,170,255,.04)',tension:.4,pointRadius:2,borderWidth:2}
    ]
  },
  options:{
    responsive:true,animation:{duration:200},
    plugins:{legend:{labels:{color:'#00ff88',font:{family:'Share Tech Mono',size:11}}}},
    scales:{
      x:{ticks:{color:'#334433',font:{family:'Share Tech Mono',size:10}},grid:{color:'#0d1a0d'}},
      y:{min:0,max:100,ticks:{color:'#334433',font:{family:'Share Tech Mono',size:10}},grid:{color:'#0d1a0d'}}
    }
  }
});

setInterval(()=>{
  const t=new Date();
  document.getElementById('time').textContent=t.toLocaleTimeString('uk');
},1000);

socket.on('update', d => {
  document.getElementById('s1').textContent   = d.soil1;
  document.getElementById('s2').textContent   = d.soil2;
  document.getElementById('temp').textContent  = d.temp;
  document.getElementById('hum').textContent   = d.hum_air;
  document.getElementById('b1').style.width    = d.soil1+'%';
  document.getElementById('b2').style.width    = d.soil2+'%';
  document.getElementById('pv').textContent    = d.pump ? 'ON' : 'OFF';
  document.getElementById('uv').textContent    = d.uv   ? 'ON' : 'OFF';
  document.getElementById('pb').innerHTML      = `<span class="badge ${d.pump?'on':'off'}">${d.pump?'💧 АКТИВНИЙ':'⏹ ЗУПИНЕНО'}</span>`;
  document.getElementById('ub').innerHTML      = `<span class="badge ${d.uv?'on':'off'}">${d.uv?'💜 АКТИВНА':'⏹ ВИМКНЕНА'}</span>`;
  document.getElementById('lw').textContent    = d.last_water||'—';

  const t = new Date().toLocaleTimeString('uk',{hour:'2-digit',minute:'2-digit',second:'2-digit'});
  if(chart.data.labels.length>30){
    chart.data.labels.shift();
    chart.data.datasets.forEach(ds=>ds.data.shift());
  }
  chart.data.labels.push(t);
  chart.data.datasets[0].data.push(d.soil1);
  chart.data.datasets[1].data.push(d.soil2);
  chart.update('none');
});

socket.on('events', evs => {
  document.getElementById('evs').innerHTML = evs.map(e=>`
    <div class="ev ${e.event_type.toLowerCase().includes('pump')?'pump':e.event_type.toLowerCase().includes('uv')?'uv':''}">
      <span class="t">${(e.timestamp||'').slice(11,16)}</span>${e.message}
    </div>`).join('');
});
</script>
</body></html>
"""

def get_latest():
    try:
        con = sqlite3.connect(DB)
        con.row_factory = sqlite3.Row
        row = con.execute("SELECT * FROM sensor_data ORDER BY id DESC LIMIT 1").fetchone()
        con.close()
        return dict(row) if row else {"soil1":0,"soil2":0,"temp":0,"hum_air":0,"pump":0,"uv":0,"last_water":"—"}
    except: return {}

def get_events():
    try:
        con = sqlite3.connect(DB)
        con.row_factory = sqlite3.Row
        rows = con.execute("SELECT * FROM events ORDER BY id DESC LIMIT 20").fetchall()
        con.close()
        return [dict(r) for r in rows]
    except: return []

@app.route("/")
def index(): return render_template_string(HTML)

@app.route("/api/data")
def api_data(): return jsonify(get_latest())

@app.route("/api/events")
def api_events(): return jsonify(get_events())

def push_loop():
    while True:
        try:
            socketio.emit("update", get_latest())
            socketio.emit("events", get_events())
        except: pass
        time.sleep(3)

if __name__ == "__main__":
    threading.Thread(target=push_loop, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
