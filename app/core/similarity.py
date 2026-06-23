"""代码查重引擎：AST 标准化 + 余弦相似度。

抗变量重命名：将 AST 节点类型名称作为 token，而非源代码文本。
两份仅改名/改格式的代码会产生高度相似的 AST token 序列。
"""
import ast
import math
from collections import Counter


def _tokenize(code: str) -> list[str]:
    """将 Python 代码转为 AST 节点类型序列（抗重命名）。

    Args:
        code: Python 源代码。

    Returns:
        list[str]: AST 节点类型名列表，如 ['FunctionDef','For','For','If','Assign',...]。
    """
    try:
        tree = ast.parse(code)
        return [type(n).__name__ for n in ast.walk(tree)]
    except SyntaxError:
        # 语法错误的代码退化为词法 token
        import re
        return re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', code)


def similarity(a: str, b: str) -> float:
    """计算两份代码的 AST 余弦相似度。

    Args:
        a, b: 两份 Python 源代码。

    Returns:
        float: 相似度 [0, 1]，1 表示 AST 结构完全相同。
    """
    ca = Counter(_tokenize(a))
    cb = Counter(_tokenize(b))

    dot = sum(ca[t] * cb[t] for t in ca.keys() & cb.keys())
    na = math.sqrt(sum(v * v for v in ca.values()))
    nb = math.sqrt(sum(v * v for v in cb.values()))

    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def detect(submissions: list, threshold: float = 0.85) -> list[dict]:
    """在一组提交中检测相似对。

    Args:
        submissions: Submission 模型列表（需含 .user.username 和 .code）。
        threshold: 相似度阈值，默认 0.85。

    Returns:
        list[dict]: 相似对列表，每项 {user_a, user_b, sim, sub_a_id, sub_b_id}。
    """
    pairs = []
    n = len(submissions)
    for i in range(n):
        for j in range(i + 1, n):
            s = similarity(submissions[i].code, submissions[j].code)
            if s >= threshold:
                pairs.append({
                    "sub_a": submissions[i],      # ORM 对象，模板用 .user.username .id
                    "sub_b": submissions[j],      # ORM 对象
                    "similarity": round(s, 3),    # 模板引用 r.similarity
                })
    # 按相似度降序
    pairs.sort(key=lambda x: x["similarity"], reverse=True)
    return pairs
