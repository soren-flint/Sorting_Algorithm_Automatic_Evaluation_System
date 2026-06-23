# SortJudge — 排序算法学习与评测系统

> 浏览器内编写排序算法 → 一键自动评测 → 可视化回放  
> 实践周题目二 | Python 3.12+ / Flask / SQLite / Canvas

---

## 🚀 快速启动

```bash
# 方式一：双击 AAA启动器.bat（自动安装依赖 + 建库 + 启动）

# 方式二：命令行
pip install -r requirements.txt
python seed.py       # 初始化数据（4用户 + 10题 + ~40用例）
python run.py        # 启动 http://127.0.0.1:5000
```

**演示账号**：`student1 / 123456`（学生）| `teacher1 / 123456`（教师）

---

## 🎯 功能概览

### 学生端
- **6 种排序算法**：冒泡、选择、插入、快速、归并、堆排序
- **CodeMirror IDE**：浏览器内置 Python 编辑器
- **一键评测**：沙箱执行 → 算法识别 → 输出判定 → 步骤采集 → 评分
- **可视化回放**：DOM bar + CSS 过渡动画，支持播放/暂停/单步/变速/音效
- **复杂度分析**：多规模实测反推 O(n)/O(n log n)/O(n²)
- **智能反馈**：纯规则驱动，无 LLM 依赖
- **整活专区**：斯大林排序、猴子排序、睡眠排序、仁慈斯大林

### 教师端
- **题目管理**：创建/编辑/删除题目（含测试用例）
- **代码查重**：AST 余弦相似度检测
- **仪表盘**：统计概览

---

## 🏗️ 架构

```
表现层 (Jinja2 + CodeMirror + Canvas)
     │
业务层 (auth / problem / submit / teacher)
     │
核心引擎层 ⭐ (纯 Python，与 Flask 解耦)
  ├── sandbox.py          沙箱执行器
  ├── recognizer.py       AST 算法识别
  ├── validator.py        多规则排序判定
  ├── comparator.py       输出比对
  ├── feedback.py         智能反馈引擎
  ├── step_collector.py   步骤采集（三策略）
  ├── algo_simulators.py  排序模拟器（8 种算法 Python 生成器）
  ├── code_marker.py      AST 代码行号标记（6 种算法）
  ├── algo_semantic_check.py  白盒语义验证
  ├── tracked_list.py     list 子类 (步骤拦截)
  ├── grader.py           10分制评分
  ├── complexity.py       复杂度估算
  ├── similarity.py       代码查重
  └── algo_profiles.py    算法档案
     │
数据层 (SQLite WAL + SQLAlchemy ORM)
```

---

## 📊 数据库 E-R

```
user ──1──0..*── submission ──1──0..*── submission_detail ──1──0..*── sort_step
  │                    │                        │
problem ──1──0..*── test_case           complexity_analysis (0..1)
```

详见 `docs/` 和 `图/` 目录下的架构文档（ER图、核心引擎类图、路由蓝图架构图）。

---

## 🧪 测试

```bash
pytest tests/ -v    # 172+ 个测试用例，覆盖核心引擎 100%
```

---

## 📝 开发日志

### 2026-06-18 (v1.0 打磨)

**Bug 修复**：
- 🐛 CSRF 检查从仅读 `request.form` 改为同时支持 `X-CSRF-Token` 请求头 (A1)
- 🐛 `complexity.py` 的 `_wrap_code` 从 f-string 改为拼接模板，避免用户代码中的 `{}` 导致 SyntaxError (A2)
- 🐛 `editor.html` 的 `analyzeComplexity()` fetch 补上 CSRF token (A3)
- 🐛 反馈引擎 NameError 处理重写：区分「函数名错误」(如 `wrong_bubble_sort`) 和「真正未定义变量」，删除误导性 "temp 变量" 提示 (T-20260618-001)

**UI 优化**：
- ✨ CSS 新增 `--font-ui`、`--font-mono`、`--shadow-sm/md` 变量
- ✨ `a.primary` 和 `a.btn-primary` 加入按钮选择器（修复「开始做题」白色按钮）
- ✨ `problems.html` 新增顶部 Hero 引导区
- ✨ 导航链接对比度从 `--muted` 提升到 `--body-c`
- ✨ `editor.html` 提交按钮加 `class="primary"`
- ✨ `result.html` 按钮优先级重排：「再做一次」primary，「查看过程」secondary

**动画复刻**：
- 🎬 `visualize.html` 从 Canvas 渲染完全重写为 DOM bar + CSS 过渡动画
- 🎬 新增 6 种算法 JavaScript Generator（bubble/select/insert/quick/merge/heap）
- 🎬 双模式驱动：回放模式（后端 API 数据）+ 演示模式（JS generator 实时生成）
- 🎬 伪代码面板：根据算法类型动态切换，操作时高亮对应行
- 🎬 步骤时间线：横向滚动，点击跳转到任意步骤
- 🎬 统计面板：实时显示比较/交换/赋值/总步数
- 🎬 完整交互控件：播放/暂停/单步/重置/速度滑块/音效开关/自定义输入/随机数据

### 2026-06-23 (v1.1 修复与文档)

**Bug 修复**：
- 🐛 `feedback.py` 正则预扫描修复：剥离行内注释 `_strip_inline_comment()` 后再匹配，消除 `if x>0:  # 注释` 等行末带注释语句的"缺少冒号"误报；修正 `(?<!:)$` 替代无效的 `$(?!.*:)` 负向先行断言
- 🐛 `editor.html` 动画区域始终可见：`loadInlineViz` 不再遇空步骤静默退出，改为显示 `📭 暂无排序过程数据` 空状态提示；`.catch()` 分支同样显示错误状态
- 🐛 **`submit.py` 第59行损坏修复**：多行代码被合并成一行（字面 `\n` 替代换行），导致 `marker_result` 永远未定义，步骤采集全量失败（NameError）。拆分恢复为正确的 11 行代码，步骤采集恢复正常
- 🐛 `visualize.html` 代码高亮修复：`userCodeLines` 改用 `submission.code.split('\n')` 完整原始代码（替代裁剪后的函数片段），消除绝对行号与渲染行号的偏移；Demo 模式 `highlight_line` 改为 1-based 统一

**功能优化**：
- ✨ `editor.html` 评分明细展开/折叠：四个维度（正确性/算法匹配/代码质量/效率）均可点击展开，显示详细评分说明 + 专属数据（测试通过数/检测算法/问题清单/复杂度）。问题清单按 severity 着色（红/橙/蓝），附行号
- ✨ `style.css` 新增 `.grade-detail-expand` 等 16 条展开面板样式规则（折叠旋转动画 + 问题列表着色）

**文档与架构**：
- 📊 输出架构图到 `../图/`：`ER图.svg`（7 表 + 关系/级联标注）、`核心引擎类图.svg`（16 模块 4 层 + 依赖箭头）、`路由蓝图架构.svg`（4 蓝图 18 路由）、`架构文档.md`（完整技术文档）
- 📝 核心引擎清单扩至 **16 模块**（补 `algo_simulators` / `code_marker` / `algo_semantic_check` / `tracked_list` / `similarity`）

### 2026-06-17 (初始版本)
- 核心引擎 16 模块完成
- 7 张数据表 + SQLite WAL
- 10 道题目（含 4 道整活题）
- 学生端 7 用例 + 教师端 3 用例
- ~75 测试用例覆盖

---

## 📂 文档

| 文件 | 内容 |
|------|------|
| `docs/UML.md` | 7 张 PlantUML 图（用例/类/ER/顺序/活动/组件/部署） |
| `docs/用例图.svg` | SVG 格式系统用例图 |
| `docs/ER图.svg` | SVG 格式数据库 ER 图 |
| `docs/项目全面审查报告.md` | 13 章全面审查（架构/需求/引擎/测试） |
| `图/架构文档.md` | 🆕 最新架构文档（ER 图 + 类图 + 路由表 + 评测流水线） |
| `图/ER图.svg` | 🆕 数据库 ER 图（7 表 + 关系/级联标注） |
| `图/核心引擎类图.svg` | 🆕 核心引擎类图（16 模块 4 层 + 依赖箭头） |
| `图/路由蓝图架构.svg` | 🆕 路由蓝图架构（4 蓝图 18 路由） |

---

## 📦 依赖

```
Flask >= 3.0
Flask-SQLAlchemy >= 3.1
Werkzeug >= 3.0
pytest >= 8.0
```

---

## ⚠️ 注意事项

- 当前使用 Flask 内置 Werkzeug 开发服务器，仅适合单机演示
- 生产环境建议：Gunicorn + Nginx + PostgreSQL
- 沙箱使用 subprocess 隔离，非 Docker 级别安全隔离