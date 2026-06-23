css='''/* SortJudge v2 — DeepSeek Minimal Design System */
:root{--bg:#f7f8fb;--surface:#fff;--surface-alt:#f1f3f8;--accent:#4c6ef5;--accent-hover:#3b5de7;--accent-soft:#eef2ff;--title:#1e293b;--body-c:#475569;--muted:#8b9aaf;--border:#e2e8f0;--success:#4caf84;--warning:#f59e4b;--danger:#ef6b5e;--code-bg:#f8f9fc;--code-text:#383a42}
[data-theme="dark"]{--bg:#0f1119;--surface:#1a1d2e;--surface-alt:#222640;--accent:#6c8cf5;--accent-hover:#8aa4f8;--accent-soft:#252a41;--title:#e2e8f0;--body-c:#a0aec0;--muted:#718096;--border:#2d3344;--success:#5ecf9c;--warning:#f7b06e;--danger:#f07b72;--code-bg:#1a1e2e;--code-text:#c9d1d9}
@media(prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0f1119;--surface:#1a1d2e;--surface-alt:#222640;--accent:#6c8cf5;--accent-hover:#8aa4f8;--accent-soft:#252a41;--title:#e2e8f0;--body-c:#a0aec0;--muted:#718096;--border:#2d3344;--success:#5ecf9c;--warning:#f7b06e;--danger:#f07b72;--code-bg:#1a1e2e;--code-text:#c9d1d9}}
*{margin:0;padding:0;box-sizing:border-box}
html,body{font-family:Inter,Segoe UI,PingFang SC,Microsoft YaHei,sans-serif;background:var(--bg);color:var(--body-c);font-size:.9rem;line-height:1.6;min-height:100vh;transition:background .35s,color .35s}
a{color:var(--accent);text-decoration:none;transition:color .2s}a:hover{color:var(--accent-hover)}
h1,h2,h3{color:var(--title);letter-spacing:-.02em}h1{font-size:1.5rem;font-weight:700}h2{font-size:1.25rem;font-weight:600}h3{font-size:1rem;font-weight:600}
code,pre,.mono{font-family:JetBrains Mono,SF Mono,Cascadia Code,Consolas,monospace}
.container{max-width:1100px;margin:0 auto;padding:20px}
'''
with open('app/static/css/style.css','w',encoding='utf-8') as f: f.write(css)
print('Part 1 done')
