css='''
/*---- Buttons ----*/
button,.btn-sm,a.btn-sm{font-family:var(--font-ui);font-size:.82rem;font-weight:500;padding:8px 16px;border:1px solid var(--border);border-radius:22px;background:var(--surface);color:var(--body-c);cursor:pointer;transition:all .2s ease;text-decoration:none;display:inline-block;white-space:nowrap}
button:hover,.btn-sm:hover{transform:translateY(-1px);box-shadow:var(--shadow-sm)}
button:active{transform:scale(.97)}
button.primary,.btn-primary{background:var(--accent);color:#fff;border-color:var(--accent);font-weight:600;padding:10px 20px}
button.primary:hover{background:var(--accent-hover)}
button.secondary{background:transparent;color:var(--accent);border:1.5px solid var(--accent);font-weight:600;padding:10px 20px}
button.secondary:hover{background:var(--accent-soft)}
button.ghost{background:transparent;color:var(--muted);border-color:var(--border)}
button.ghost:hover{background:var(--accent-soft);color:var(--accent);border-color:var(--accent)}
button:disabled{opacity:.35;cursor:not-allowed;transform:none}

/*---- Inputs ----*/
input[type=text],input[type=password],textarea,select,.form-control{font-family:var(--font-ui);font-size:.88rem;padding:10px 14px;border:1px solid var(--border);border-radius:10px;background:var(--surface);color:var(--body-c);outline:none;transition:border-color .2s;width:100%}
input:focus,textarea:focus,select:focus{border-color:var(--accent)}

/*---- Tags & Badges ----*/
.tag,.badge{display:inline-block;font-size:.75rem;font-weight:600;padding:4px 12px;border-radius:14px;font-family:var(--font-ui)}
.tag-accent{background:var(--accent-soft);color:var(--accent)}
.tag-success{background:rgba(76,175,132,.15);color:var(--success)}
.tag-warning{background:rgba(245,158,75,.15);color:var(--warning)}
.tag-danger{background:rgba(239,107,94,.15);color:var(--danger)}
.tag-muted{background:var(--surface-alt);color:var(--muted)}

/*---- Cards ----*/
.card,.panel{background:var(--surface);border:1px solid var(--border);border-radius:14px;box-shadow:var(--shadow-sm)}
.card:hover{box-shadow:var(--shadow-md)}

/*---- Navbar ----*/
.navbar{display:flex;align-items:center;gap:16px;padding:0 20px;height:50px;background:var(--surface);border-bottom:1px solid var(--border)}
.navbar .brand{font-size:1rem;font-weight:700;color:var(--accent);letter-spacing:-.02em}
.nav-links{display:flex;align-items:center;gap:4px;list-style:none;flex:1;padding:0}
.nav-links a{font-size:.82rem;font-weight:500;color:var(--muted);padding:6px 12px;border-radius:8px;text-decoration:none;transition:all .15s}
.nav-links a:hover{color:var(--title);background:var(--accent-soft)}
.nav-right{display:flex;align-items:center;gap:8px}
.user-tag{font-size:.78rem;color:var(--muted);font-family:JetBrains Mono,monospace}
.theme-btn{width:36px;height:36px;border-radius:50%;border:1px solid var(--border);background:transparent;cursor:pointer;font-size:1.1rem;display:flex;align-items:center;justify-content:center;transition:all .2s}
.theme-btn:hover{border-color:var(--accent);background:var(--accent-soft)}

/*---- Flash ----*/
.flash-wrap{max-width:1100px;margin:10px auto 0;padding:0 20px}
.flash{padding:10px 16px;border-radius:10px;font-size:.85rem;margin-bottom:8px;border-left:3px solid}
.flash.success{background:rgba(76,175,132,.08);border-color:var(--success);color:var(--success)}
.flash.danger{background:rgba(239,107,94,.08);border-color:var(--danger);color:var(--danger)}
.flash.warning{background:rgba(245,158,75,.08);border-color:var(--warning);color:var(--warning)}
.flash.info{background:var(--accent-soft);border-color:var(--accent);color:var(--accent)}

/*---- Tables ----*/
table{width:100%;border-collapse:collapse;font-size:.85rem}
th{font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);padding:10px 14px;text-align:left;border-bottom:1px solid var(--border)}
td{padding:8px 14px;border-bottom:1px solid var(--border);color:var(--body-c)}
tr:hover td{background:var(--accent-soft)}

/*---- CodeMirror ----*/
.CodeMirror{background:var(--code-bg)!important;font-family:JetBrains Mono,SF Mono,monospace!important;font-size:13px!important;line-height:1.6!important;border-radius:8px;border:1px solid var(--border)!important}

/*---- Editor Layout ----*/
.editor-layout{display:grid;grid-template-columns:1fr 1.2fr;gap:16px;min-height:calc(100vh - 100px)}
@media(max-width:820px){.editor-layout{grid-template-columns:1fr}}
.problem-sidebar{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:20px;overflow-y:auto}
.sidebar-header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px}
.sidebar-header h2{font-size:1.15rem;font-weight:700}
.btn-back{font-size:.78rem;color:var(--muted);padding:4px 10px;border-radius:8px;border:1px solid var(--border);text-decoration:none}
.btn-back:hover{color:var(--title);border-color:var(--accent)}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px}
.desc{font-size:.85rem;line-height:1.75;color:var(--body-c);white-space:pre-wrap;word-wrap:break-word}
.cases{margin-top:16px;padding-top:14px;border-top:1px solid var(--border)}
.cases h3{font-size:.75rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px}
.case-row{font-size:.82rem;margin-bottom:4px}
.case-row code{font-family:JetBrains Mono,monospace;font-size:.78rem;color:var(--accent);background:var(--accent-soft);padding:1px 5px;border-radius:4px}
.editor-main{display:flex;flex-direction:column;gap:12px}
.editor-panel{background:var(--surface);border:1px solid var(--border);border-radius:14px;overflow:hidden}
.panel-head{padding:12px 16px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:12px}
.panel-head .label{font-size:.8rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
.panel-head .hint{font-size:.78rem;color:var(--muted)}
.submit-row{display:flex;align-items:center;gap:10px;padding:12px 16px;border-top:1px solid var(--border)}
#submit-status{font-size:.8rem;color:var(--muted);font-family:JetBrains Mono,monospace}
.result-panel{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:16px 20px}
.result-head{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:10px}
.res-badge{font-size:.85rem;font-weight:600;padding:4px 14px;border-radius:14px;color:#fff}
.res-score{font-size:1rem;font-weight:700;color:var(--accent)}
.res-passed{font-size:.8rem;color:var(--muted)}
.res-algo{font-size:.78rem;background:var(--accent-soft);color:var(--accent);padding:3px 10px;border-radius:12px;font-family:JetBrains Mono,monospace}
.result-body{display:flex;flex-direction:column;gap:8px}
.feedback-box{padding:12px 16px;border-radius:10px;background:rgba(245,158,75,.06);border-left:3px solid var(--warning);font-size:.85rem;line-height:1.6}

/*---- Grade Report ----*/
.grade-report{margin-top:8px}
.grade-row{display:flex;align-items:center;gap:10px;padding:6px 0;font-size:.82rem;flex-wrap:wrap}
.grade-icon{font-size:1rem;min-width:22px;text-align:center}
.grade-label{min-width:56px;font-weight:600;color:var(--title);font-size:.8rem}
.grade-bar-wrap{flex:1;min-width:80px;height:6px;background:var(--border);border-radius:3px;overflow:hidden}
.grade-bar{height:100%;border-radius:3px;transition:width .5s ease}
.grade-score-num{font-family:JetBrains Mono,monospace;font-size:.82rem;font-weight:600;color:var(--accent);min-width:30px;text-align:right}
.grade-detail-text{font-size:.78rem;color:var(--muted);flex-basis:100%;padding-left:32px}
.example-code{margin-top:8px}
.example-code summary{cursor:pointer;font-size:.82rem;color:var(--accent);font-weight:500;padding:6px 0}
.example-code pre{background:var(--code-bg);padding:14px;border-radius:8px;font-family:JetBrains Mono,monospace;font-size:.78rem;line-height:1.6;color:var(--code-text);overflow:auto;margin-top:6px}

/*---- Login ----*/
.login-wrap{max-width:400px;margin:60px auto;padding:32px;background:var(--surface);border:1px solid var(--border);border-radius:14px;box-shadow:var(--shadow-sm)}
.login-wrap h2{text-align:center;margin-bottom:24px;font-size:1.3rem;font-weight:700}
.form-group{margin-bottom:14px}
.form-group label{display:block;font-size:.75rem;font-weight:600;color:var(--muted);margin-bottom:4px;text-transform:uppercase;letter-spacing:.05em}

/*---- Visualization ----*/
.viz-layout{display:grid;grid-template-columns:1fr 340px;gap:14px}
@media(max-width:820px){.viz-layout{grid-template-columns:1fr}}
.viz-main{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:20px;text-align:center}
.viz-steps{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:10px;overflow-y:auto;max-height:420px}
.viz-controls{display:flex;justify-content:center;align-items:center;gap:10px;margin-top:14px;flex-wrap:wrap}
.step-item{font-size:.78rem;padding:4px 10px;border-radius:6px;cursor:pointer;transition:all .15s;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-family:JetBrains Mono,monospace}
.step-item:hover{background:var(--accent-soft)}
.step-item.active{background:var(--accent-soft);border-left:2px solid var(--accent);font-weight:600}
#step-info{font-family:JetBrains Mono,monospace;font-size:.82rem;color:var(--accent);min-width:60px}

/*---- Slider ----*/
input[type=range]{-webkit-appearance:none;appearance:none;width:100px;height:4px;background:var(--border);border-radius:2px;outline:none}
input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:14px;height:14px;border-radius:50%;background:var(--accent);cursor:pointer}

/*---- Dropdown ----*/
.dropdown-menu{background:var(--surface);border:1px solid var(--border);border-radius:12px;box-shadow:var(--shadow-md);padding:4px}
.dropdown-item{font-size:.82rem;padding:8px 14px;border-radius:8px;color:var(--body-c);cursor:pointer}
.dropdown-item:hover{background:var(--accent-soft);color:var(--accent)}

/*---- Teacher bar ----*/
.teacher-bar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:10px 16px;margin-bottom:14px;background:var(--surface);border:1px solid var(--border);border-radius:14px;font-size:.82rem}
.teacher-bar .stat{font-family:JetBrains Mono,monospace;font-size:.78rem;padding:3px 10px;border-radius:12px;background:var(--accent-soft);color:var(--accent)}

/*---- Problem cards ----*/
.problem-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
.problem-card{padding:18px;background:var(--surface);border:1px solid var(--border);border-radius:14px;box-shadow:var(--shadow-sm);transition:all .25s ease}
.problem-card:hover{transform:translateY(-2px);box-shadow:var(--shadow-md);border-color:var(--accent)}
.problem-card h3{font-size:.95rem;font-weight:700;margin-bottom:8px;color:var(--title)}
.problem-card .meta{display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap}

/*---- Utilities ----*/
.text-muted{color:var(--muted)}
.text-center{text-align:center}
.bg-success{background:var(--success)!important}
.bg-danger{background:var(--danger)!important}
.bg-warning{background:var(--warning)!important;color:#000!important}
.bg-info{background:var(--accent)!important}
.bg-secondary{background:var(--muted)!important}
.mt-2{margin-top:8px}.mt-3{margin-top:12px}.mb-2{margin-bottom:8px}.mb-3{margin-bottom:12px}

/*---- Responsive ----*/
@media(max-width:820px){.viz-layout,.editor-layout{grid-template-columns:1fr}}
@media(max-width:480px){button,.btn-sm{font-size:.75rem;padding:6px 12px}.problem-grid{grid-template-columns:1fr}}
'''
with open('app/static/css/style.css','a',encoding='utf-8') as f: f.write(css)
print('CSS complete')
