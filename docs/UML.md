# SortJudge — 系统 UML 建模

> 排序算法学习与评测系统  |  2026-06-16  |  实践周题目二
>
> 所有图提供 PlantUML 源码，可在 [PlantUML Online](https://www.plantuml.com/plantuml/)、VS Code + PlantUML 插件、或 StarUML 中渲染。

---

## 图表索引

| # | 图名 | 类型 | 对应报告章节 |
|---|------|------|------------|
| 1 | 系统用例图 | Use Case | §2 需求分析 |
| 2 | 核心类图 | Class | §3.2 概要设计 |
| 3 | 数据库 ER 图 | Entity-Relationship | §3.3 数据库设计 |
| 4 | 评测顺序图 | Sequence | §4.1 详细设计 |
| 5 | 评测活动图 | Activity | §4.2 详细设计 |
| 6 | 组件架构图 | Component | §3.1 体系结构 |
| 7 | 部署图 | Deployment | §3.1 体系结构 |

---

## 图 1: 系统用例图

```plantuml
@startuml
left to right direction
skinparam packageStyle rectangle

actor "学生" as Student
actor "教师" as Teacher

rectangle "SortJudge 排序评测系统" {
  usecase (UC1 注册/登录) as UC1
  usecase (UC2 浏览题目列表) as UC2
  usecase (UC3 内置IDE编写代码) as UC3
  usecase (UC4 提交评测\n(沙箱执行+算法识别\n+正确性判定)) as UC4
  usecase (UC5 查看评测结果\n与智能反馈) as UC5
  usecase (UC6 观看排序过程\n可视化回放) as UC6
  usecase (UC7 查看提交历史) as UC7
  usecase (UC8 教师建题\n(算法/规则/用例)) as UC8
  usecase (UC9 代码查重) as UC9
  usecase (UC10 复杂度分析) as UC10
}

Student --> UC1
Student --> UC2
Student --> UC3
Student --> UC4
Student --> UC5
Student --> UC6
Student --> UC7

UC3 ..> UC4 : <<include>>
UC4 ..> UC5 : <<include>>
UC4 ..> UC6 : <<extend>>
UC4 ..> UC10 : <<extend>>

Teacher --> UC1
Teacher --> UC8
Teacher --> UC9
Teacher --> UC2

@enduml
```

**说明**：
- `<<include>>`：UC3(编码) 必然触发 UC4(评测)；UC4(评测) 必然产生 UC5(结果)
- `<<extend>>`：UC4(评测) 可选触发 UC6(可视化) 和 UC10(复杂度分析)
- 教师可建题(UC8)、查重(UC9)，也可浏览题目(UC2)

---

## 图 2: 核心类图

```plantuml
@startuml
skinparam classAttributeIconSize 0

' === 数据模型层 ===
class User {
  + id : int {PK}
  + username : str {unique}
  + password_hash : str
  + role : str {"student"|"teacher"}
  --
  + set_password(pwd)
  + check_password(pwd) : bool
}

class Problem {
  + id : int {PK}
  + title : str
  + description : str
  + difficulty : str {"easy"|"medium"|"hard"}
  + algo_type : str
  + sort_rule : str {"strict"|"stalin"|"stable"|"topk"}
  + complexity_ceiling : str {nullable}
  + created_by : int {FK}
}

class TestCase {
  + id : int {PK}
  + problem_id : int {FK}
  + input_data : str {JSON}
  + expected_output : str {JSON, nullable}
  + is_public : bool
}

class Submission {
  + id : int {PK}
  + user_id : int {FK}
  + problem_id : int {FK}
  + code : str
  + status : str
  + score : int
  + recognized_algo : str {nullable}
  + submitted_at : datetime
}

class SubmissionDetail {
  + id : int {PK}
  + submission_id : int {FK}
  + test_case_id : int {FK}
  + input_arr : str {JSON}
  + actual_output : str {nullable}
  + passed : bool
  + feedback : str {nullable}
}

class SortStep {
  + id : int {PK}
  + detail_id : int {FK}
  + seq : int
  + array_state : str {JSON}
  + op : str {"compare"|"swap"|"set"|"delete"|"done"|"error"}
  + i : int {nullable}
  + j : int {nullable}
  + note : str {nullable}
}

class ComplexityAnalysis {
  + id : int {PK}
  + submission_id : int {FK, unique}
  + estimated : str
  + theoretical : str {nullable}
  + timings : str {JSON}
  + ratio : float {nullable}
  + meets_ceiling : bool {nullable}
  + analyzed_at : datetime
}

' === 核心引擎层（纯函数，与 Flask 解耦）===
class SandboxRunner <<engine>> {
  + run(code, stdin, timeout) : RunResult
  + run_with_collect(code, input_arr) : (RunResult, steps)
}

class AlgoRecognizer <<engine>> {
  + recognize(code) : str
  - _has_nested_loop(tree) : bool
  - _has_adjacent_swap(tree) : bool
  - _has_recursion(tree) : bool
  - _has_merge(tree) : bool
  - _has_heap(tree) : bool
  - _has_min_find(tree) : bool
  - _has_while_inner(tree) : bool
}

class SortValidator <<engine>> {
  + is_monotonic(arr) : bool
  + is_permutation(a, b) : bool
  + is_subsequence(short, long) : bool
  + validate(output, input, rule, k) : Result
  + check_off_by_one(output, expected) : str?
}

class StepCollector <<engine>> {
  + collect(code, input_arr, max_steps, strategy) : list[Step]
  - _collect_tracked() : list[Step]
  - _collect_ast_instrument() : list[Step]
  - _collect_replay() : list[Step]
}

class FeedbackEngine <<engine>> {
  + diagnose(code, run_result, algo) : dict?
  + static_check_sort(code) : list[Issue]
  - SORT_TRACEBACK_PATTERNS : list
}

class OutputComparator <<engine>> {
  + compare_outputs(actual, expected, input, rule) : Result
  - _describe_diff(actual, expected) : str
}

class ComplexityEstimator <<engine>> {
  + estimate(user_code, sizes, timeout) : Report
}

class SimilarityDetector <<engine>> {
  + similarity(a, b) : float
  + detect(submissions, threshold) : list[Pair]
  - _tokenize(code) : list[str]
}

class AlgoProfiles <<engine>> {
  + ALGO_PROFILES : dict
  + get_profile(algo_type) : dict?
  + check_ceiling(estimated, ceiling) : Result
}

' === 关系 ===
User "1" -- "0..*" Submission : submits
Problem "1" -- "0..*" TestCase : has
Problem "1" -- "0..*" Submission : evaluated
Submission "1" -- "0..*" SubmissionDetail : details
SubmissionDetail "1" -- "0..*" SortStep : steps
Submission "1" -- "0..1" ComplexityAnalysis : analyzed
TestCase "1" -- "0..*" SubmissionDetail : verified

Submission ..> AlgoRecognizer : <<use>>
Submission ..> SandboxRunner : <<use>>
SubmissionDetail ..> SortValidator : <<use>>
SubmissionDetail ..> StepCollector : <<use>>
SubmissionDetail ..> FeedbackEngine : <<use>>
Submission ..> ComplexityEstimator : <<use, 按需>>
Submission ..> SimilarityDetector : <<use, 教师>>

@enduml
```

**说明**：
- 上半部分：7 张数据表，模型层
- 下半部分：8 个核心引擎，全部纯函数，与 Flask Web 层物理解耦
- SubmissionDetail 关联 SortValidator / StepCollector / FeedbackEngine
- ComplexityEstimator 和 SimilarityDetector 按需触发，不在常规评测链路

---

## 图 3: 数据库 ER 图

```plantuml
@startuml
entity "user" as user {
  * id : INTEGER <<PK>>
  --
  username : TEXT <<unique>>
  password_hash : TEXT
  role : TEXT
}

entity "problem" as problem {
  * id : INTEGER <<PK>>
  --
  title : TEXT
  description : TEXT
  difficulty : TEXT
  algo_type : TEXT
  sort_rule : TEXT
  complexity_ceiling : TEXT <<nullable>>
  created_by : INTEGER <<FK>>
}

entity "test_case" as test_case {
  * id : INTEGER <<PK>>
  --
  problem_id : INTEGER <<FK>>
  input_data : TEXT {JSON}
  expected_output : TEXT <<nullable>>
  is_public : INTEGER
}

entity "submission" as submission {
  * id : INTEGER <<PK>>
  --
  user_id : INTEGER <<FK>>
  problem_id : INTEGER <<FK>>
  code : TEXT
  status : TEXT
  score : INTEGER
  recognized_algo : TEXT <<nullable>>
  submitted_at : TEXT
}

entity "submission_detail" as detail {
  * id : INTEGER <<PK>>
  --
  submission_id : INTEGER <<FK>>
  test_case_id : INTEGER <<FK>>
  input_arr : TEXT
  actual_output : TEXT <<nullable>>
  passed : INTEGER
  feedback : TEXT <<nullable>>
}

entity "sort_step" as step {
  * id : INTEGER <<PK>>
  --
  detail_id : INTEGER <<FK>>
  seq : INTEGER
  array_state : TEXT {JSON}
  op : TEXT
  i : INTEGER <<nullable>>
  j : INTEGER <<nullable>>
  note : TEXT <<nullable>>
}

entity "complexity_analysis" as cx {
  * id : INTEGER <<PK>>
  --
  submission_id : INTEGER <<FK, unique>>
  estimated : TEXT
  theoretical : TEXT <<nullable>>
  timings : TEXT {JSON}
  ratio : REAL <<nullable>>
  meets_ceiling : INTEGER <<nullable>>
  analyzed_at : TEXT
}

user ||--o{ submission
problem ||--o{ test_case
problem ||--o{ submission
submission ||--o{ detail
detail ||--o{ step
submission ||--o| cx
problem ||--o{ detail

@enduml
```

**说明**：
- `user` 与 `submission` 一对多：一个学生可多次提交
- `problem` 与 `test_case` 一对多：一道题有多个测试用例
- `submission` 与 `submission_detail` 一对多：一次提交评测多组用例
- `submission_detail` 与 `sort_step` 一对多：一组用例有多步排序快照
- `submission` 与 `complexity_analysis` 一对一（按需触发，0 或 1 条）

---

## 图 4: 评测流程顺序图

```plantuml
@startuml
actor 学生 as S
participant "前端 IDE\n(editor.html)" as UI
participant "提交 API\n(submit.py)" as API
participant "算法识别\n(recognizer)" as AR
participant "沙箱\n(sandbox)" as Box
participant "判定器\n(validator)" as Val
participant "步骤采集\n(step_collector)" as SC
participant "反馈引擎\n(feedback)" as FB
database "SQLite" as DB

S -> UI : 编写排序代码
S -> UI : 点击「提交评测」
UI -> API : POST /submit/{pid}\n{code, csrf_token}

API -> AR : recognize(code)
AR --> API : algo = "bubble"

API -> DB : 创建 submission(status=pending)

loop 每个测试用例
  API -> Box : run(code, input_arr)
  Box -> Box : subprocess(降权, timeout=5s)

  alt 超时
    Box --> API : {timed_out: true}
    API -> DB : detail(反馈=超时提示)

  else 运行错误
    Box --> API : {returncode != 0, stderr}
    API -> FB : diagnose(code, result, algo)
    FB --> API : {type, hint}
    API -> DB : detail(feedback=教学反馈)

  else 正常运行
    Box --> API : {stdout}
    API -> Val : validate(output, input, sort_rule)

    alt 通过
      Val --> API : {passed: true}
    else 不通过
      Val --> API : {passed: false, reason}
    end

    API -> SC : collect(code, input_arr)
    SC --> API : steps[]

    API -> DB : detail + sort_steps
  end
end

API -> DB : 汇总 status/score/algo → commit
API --> UI : JSON {submission_id, status, score,\n          recognized_algo, detail_ids, feedback}

UI -> S : inline 展示结果
@enduml
```

**说明**：
- 8 个参与者的完整交互
- 三条分支：超时 / 运行错误 / 正常运行
- 步骤采集始终执行（可视化冗余设计）
- 异常时整体事务回滚（Phase 6 新增）

---

## 图 5: 评测 + 可视化活动图

```plantuml
@startuml
start

:接收学生代码;

:AST 算法识别;

if (语法错误?) then (是)
  :status = error;
  :反馈: 语法错误;
else (否)

  :创建 submission(status=pending);

  repeat
    :解析输入数组;
    :沙箱执行\n(subprocess, timeout=5s);

    if (超时?) then (是)
      :status = timeout;
      :反馈: 超时提示;
      break

    elseif (运行时错误?) then (是)
      :反馈引擎诊断;
      :记录 detail(带反馈);

    else (正常)
      :按 sort_rule 判定;

      if (通过?) then (是)
        :记录 detail(passed=true);
      else (否)
        :记录 detail(feedback=原因);
      endif

      :步骤采集\n(TrackedList 拦截);
      :写入 sort_step 表;
    endif

  repeat while (还有未测用例?)

  :汇总 status/score;

endif

:提交事务 commit;
:返回 JSON 结果给前端;

fork
  :学生查看 inline 结果;
fork again
  :学生点击「查看过程」;
  :GET /api/steps → Canvas 动画回放;
end fork

:学生点击「分析复杂度」;
:多规模实测 → 写入 complexity_analysis;

stop
@enduml
```

**说明**：
- 主泳道：评测流程（同步）
- fork：可视化 + 复杂度分析（异步按需）
- break：超时直接终止该提交

---

## 图 6: 组件架构图

```plantuml
@startuml
skinparam componentStyle rectangle

package "表现层 (Web UI)" {
  [Jinja2 模板] as Templates
  [CodeMirror IDE] as CM
  [Canvas 可视化] as Canvas
  [Bootstrap 5] as BS
}

package "业务层 (Routes)" {
  [auth.py\n登录/注册] as AuthRoute
  [problem.py\n题目浏览] as ProbRoute
  [submit.py\n提交评测] as SubRoute
  [teacher.py\n教师管理] as TeachRoute
}

package "核心引擎层 (Core)" {
  [sandbox.py\n沙箱执行] as Sandbox
  [validator.py\n排序判定] as Validator
  [recognizer.py\n算法识别] as Recognizer
  [step_collector.py\n步骤采集] as StepCol
  [feedback.py\n智能反馈] as Feedback
  [comparator.py\n输出比对] as Comparator
  [complexity.py\n复杂度估算] as Complexity
  [similarity.py\n代码查重] as Similarity
  [algo_profiles.py\n算法档案] as Profiles
}

package "数据层" {
  [SQLAlchemy ORM] as ORM
  database "SQLite\n(judge.db)" as DB
}

Templates --> AuthRoute
Templates --> ProbRoute
Templates --> SubRoute
Templates --> TeachRoute

SubRoute --> Sandbox
SubRoute --> Validator
SubRoute --> Recognizer
SubRoute --> StepCol
SubRoute --> Feedback
SubRoute --> Comparator
SubRoute --> Complexity
TeachRoute --> Similarity

AuthRoute --> ORM
ProbRoute --> ORM
SubRoute --> ORM
TeachRoute --> ORM

ORM --> DB

@enduml
```

**说明**：
- 三层架构：表现层 → 业务层 → 核心引擎层 → 数据层
- 核心引擎层与 Flask 物理解耦（纯 Python 函数，可独立测试）
- 数据层通过 SQLAlchemy ORM 统一访问 SQLite

---

## 图 7: 部署图

```plantuml
@startuml
node "学生/教师 浏览器" as Browser {
  artifact "HTML5 + CSS3\n+ JavaScript\n+ CodeMirror" as FE
}

node "服务器 (单机)" as Server {
  node "Flask 3.x\n(Werkzeug 开发服务器)" as Flask {
    artifact "app/ (Python)" as App
    artifact "core/ (引擎)" as Core
  }
  database "SQLite\n(instance/judge.db)" as SQLite
}

Browser --> Server : HTTP (localhost:5000)
Flask --> SQLite : SQLAlchemy

note right of Server
  单机演示部署
  Python 3.12+
  pip install -r requirements.txt
  python seed.py && python run.py
end note

@enduml
```

**说明**：
- 浏览器端：Bootstrap + CodeMirror + Canvas 动画，无需构建工具
- 服务器：Flask 内置开发服务器（实践周演示），单机部署
- 数据库：SQLite 单文件，零配置
- 部署命令：`pip install -r requirements.txt && python seed.py && python run.py`

---

## 附录：UML 图渲染说明

所有 PlantUML 源码可直接在以下工具中渲染：

| 工具 | 方式 |
|------|------|
| [PlantUML Online](https://www.plantuml.com/plantuml/) | 粘贴源码在线渲染 |
| VS Code + PlantUML 插件 | `Alt+D` 预览 |
| StarUML | 不支持 PlantUML；需手动重建或导出 PNG 贴入 |
| IntelliJ + PlantUML 插件 | 原生支持 |

**使用 PlantUML Online 批量渲染**：
1. 打开 https://www.plantuml.com/plantuml/
2. 将每个 `@startuml ... @enduml` 块分别粘贴
3. 下载 PNG/SVG 插入实验报告
