"""种子数据：创建示例用户、题目和测试用例。

用法：
    python seed.py

每次运行会清空旧数据重新插入（幂等）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.core.examples import EXAMPLE_CODE
from app.extensions import db
from app.models import User, Problem, TestCase


def seed():
    """清空并填充种子数据。"""
    app = create_app()

    with app.app_context():
        db.drop_all()
        db.create_all()

        # --- 1. 创建用户 ---
        users = [
            ("student1", "123456", "student"),
            ("student2", "123456", "student"),
            ("student3", "123456", "student"),
            ("teacher1", "123456", "teacher"),
        ]
        for uname, pwd, role in users:
            u = User(username=uname, role=role)
            u.set_password(pwd)
            db.session.add(u)
        db.session.flush()

        teacher = User.query.filter_by(username="teacher1").first()

        # ── 各算法标准示例代码（从共享模块导入）──
        EXAMPLE = EXAMPLE_CODE

        # --- 2. 创建题目 ---
        problems_data = [
            {
                "title": "冒泡排序（Bubble Sort）",
                "description": (
                    "请实现冒泡排序算法。\n\n"
                    "要求：\n"
                    "- 定义函数 sort(arr)，接收一个整数列表，返回升序排序后的列表\n"
                    "- 使用冒泡排序的思想：相邻元素两两比较，大的往后'冒'\n"
                    "- 输入为标准 JSON 数组，输出为标准 JSON 数组\n\n"
                    "示例：\n"
                    "输入：[5,2,8,1,3]\n"
                    "输出：[1,2,3,5,8]"
                ),
                "difficulty": "简单",
                "algo_type": "bubble",
                "sort_rule": "strict",
                "complexity_ceiling": None,
                "example_code": EXAMPLE["bubble"],
                "is_meme": False,
                "test_cases": [
                    ("[5,2,8,1,3]", "[1,2,3,5,8]", True),
                    ("[8,3,5,1,9,2,6,4,7,0]", "[0,1,2,3,4,5,6,7,8,9]", True),
                    ("[1]", "[1]", True),
                    ("[]", "[]", True),
                    ("[1,2,3,4,5]", "[1,2,3,4,5]", False),
                    ("[5,4,3,2,1]", "[1,2,3,4,5]", False),
                    ("[3,1,4,1,5,9,2,6]", "[1,1,2,3,4,5,6,9]", False),
                    ("[15,2,88,34,7,91,0,42,66,13]", "[0,2,7,13,15,34,42,66,88,91]", False),
                ],
            },
            {
                "title": "快速排序（Quick Sort）",
                "description": (
                    "请实现快速排序算法。\n\n"
                    "要求：\n"
                    "- 使用分治策略：选 pivot，分区，递归排序左右子数组\n"
                    "- 可使用递归实现\n\n"
                    "示例：\n"
                    "输入：[5,2,8,1,3]\n"
                    "输出：[1,2,3,5,8]"
                ),
                "difficulty": "中等",
                "algo_type": "quick",
                "sort_rule": "strict",
                "complexity_ceiling": "O(n log n)",
                "example_code": EXAMPLE["quick"],
                "is_meme": False,
                "test_cases": [
                    ("[5,2,8,1,3]", "[1,2,3,5,8]", True),
                    ("[8,3,5,1,9,2,6,4,7,0]", "[0,1,2,3,4,5,6,7,8,9]", True),
                    ("[1]", "[1]", True),
                    ("[5,4,3,2,1]", "[1,2,3,4,5]", False),
                    ("[3,1,4,1,5,9,2,6]", "[1,1,2,3,4,5,6,9]", False),
                    ("[15,2,88,34,7,91,0,42,66,13]", "[0,2,7,13,15,34,42,66,88,91]", False),
                ],
            },
            {
                "title": "归并排序（Merge Sort）",
                "description": (
                    "请实现归并排序算法。\n\n"
                    "要求：\n"
                    "- 使用分治策略：递归分割数组，两路归并有序子数组\n"
                    "- 需使用辅助空间进行合并操作\n\n"
                    "示例：\n"
                    "输入：[5,2,8,1,3]\n"
                    "输出：[1,2,3,5,8]"
                ),
                "difficulty": "中等",
                "algo_type": "merge",
                "sort_rule": "strict",
                "complexity_ceiling": "O(n log n)",
                "example_code": EXAMPLE["merge"],
                "is_meme": False,
                "test_cases": [
                    ("[5,2,8,1,3]", "[1,2,3,5,8]", True),
                    ("[8,3,5,1,9,2,6,4,7,0]", "[0,1,2,3,4,5,6,7,8,9]", True),
                    ("[1]", "[1]", True),
                    ("[5,4,3,2,1]", "[1,2,3,4,5]", False),
                    ("[3,1,4,1,5,9,2,6]", "[1,1,2,3,4,5,6,9]", False),
                    ("[15,2,88,34,7,91,0,42,66,13]", "[0,2,7,13,15,34,42,66,88,91]", False),
                ],
            },
            {
                "title": "选择排序（Selection Sort）",
                "description": (
                    "请实现选择排序算法。\n\n"
                    "要求：\n"
                    "- 每轮从未排序部分找出最小值，放到已排序部分的末尾\n"
                    "- 每轮只做一次交换\n\n"
                    "示例：\n"
                    "输入：[5,2,8,1,3]\n"
                    "输出：[1,2,3,5,8]"
                ),
                "difficulty": "简单",
                "algo_type": "select",
                "sort_rule": "strict",
                "complexity_ceiling": None,
                "example_code": EXAMPLE["select"],
                "is_meme": False,
                "test_cases": [
                    ("[5,2,8,1,3]", "[1,2,3,5,8]", True),
                    ("[8,3,5,1,9,2,6,4,7,0]", "[0,1,2,3,4,5,6,7,8,9]", True),
                    ("[1]", "[1]", True),
                    ("[5,4,3,2,1]", "[1,2,3,4,5]", False),
                    ("[15,2,88,34,7,91,0,42,66,13]", "[0,2,7,13,15,34,42,66,88,91]", False),
                ],
            },
            {
                "title": "插入排序（Insertion Sort）",
                "description": (
                    "请实现插入排序算法。\n\n"
                    "要求：\n"
                    "- 从第二个元素开始，将当前元素插入前面已排序部分的正确位置\n"
                    "- 通过向后移动元素为插入腾出空间\n\n"
                    "示例：\n"
                    "输入：[5,2,8,1,3]\n"
                    "输出：[1,2,3,5,8]"
                ),
                "difficulty": "简单",
                "algo_type": "insert",
                "sort_rule": "strict",
                "complexity_ceiling": None,
                "example_code": EXAMPLE["insert"],
                "is_meme": False,
                "test_cases": [
                    ("[5,2,8,1,3]", "[1,2,3,5,8]", True),
                    ("[8,3,5,1,9,2,6,4,7,0]", "[0,1,2,3,4,5,6,7,8,9]", True),
                    ("[1]", "[1]", True),
                    ("[5,4,3,2,1]", "[1,2,3,4,5]", False),
                    ("[15,2,88,34,7,91,0,42,66,13]", "[0,2,7,13,15,34,42,66,88,91]", False),
                ],
            },
            {
                "title": "不限算法的排序练习",
                "description": (
                    "用你喜欢的任何排序算法完成此题。\n\n"
                    "要求：\n"
                    "- 输出必须有序且是输入的排列（strict 规则）\n"
                    "- 系统会自动识别你使用的算法类型\n\n"
                    "示例：\n"
                    "输入：[5,2,8,1,3]\n"
                    "输出：[1,2,3,5,8]"
                ),
                "difficulty": "中等",
                "algo_type": "any",
                "sort_rule": "strict",
                "complexity_ceiling": None,
                "example_code": EXAMPLE["quick"],  # 默认展示快速排序示例
                "is_meme": False,
                "test_cases": [
                    ("[5,2,8,1,3]", "[1,2,3,5,8]", True),
                    ("[8,3,5,1,9,2,6,4,7,0]", "[0,1,2,3,4,5,6,7,8,9]", True),
                    ("[1]", "[1]", True),
                    ("[5,4,3,2,1]", "[1,2,3,4,5]", False),
                    ("[3,1,4,1,5,9,2,6]", "[1,1,2,3,4,5,6,9]", False),
                    ("[15,2,88,34,7,91,0,42,66,13]", "[0,2,7,13,15,34,42,66,88,91]", False),
                ],
            },
            # ── 整活专区 ──
            {
                "title": "斯大林排序挑战（Stalin Sort）",
                "description": (
                    "这是一道开放性的创意题！\n\n"
                    "斯大林排序（Stalin Sort）的'哲学'：不是排序，而是淘汰——\n"
                    "遍历数组，凡是破坏升序的元素直接删除，留下的就是有序序列。\n\n"
                    "要求：\n"
                    "- 输出必须是输入的一个子序列\n"
                    "- 输出必须有序（升序）\n"
                    "- 你可以用任何策略决定删除哪些元素\n\n"
                    "示例：\n"
                    "输入：[1,3,2,5,4]\n"
                    "输出：[1,3,5]（删除了 2 和 4，因为它们破坏了升序）\n\n"
                    "提示：本题使用 stalin 规则评测——只检查'有序+子序列'，不检查排列。"
                ),
                "difficulty": "整活 🤪",
                "algo_type": "any",
                "sort_rule": "stalin",
                "complexity_ceiling": None,
                "example_code": EXAMPLE["stalin"],
                "is_meme": True,
                "test_cases": [
                    ("[1,3,2,5,4]", None, True),
                    ("[8,3,5,1,9,2,6,4,7,0]", None, True),
                    ("[5,1,3,2,4]", None, True),
                    ("[1,2,3,4,5]", None, False),
                    ("[1]", None, True),
                    ("[15,2,88,34,7,91,0,42,66,13]", None, False),
                ],
            },
            {
                "title": "猴子排序（Bogo Sort）🐒",
                "description": (
                    "🐒 猴子排序：史上最'慢'的排序算法！\n\n"
                    "原理：\n"
                    "- 检查数组是否已有序\n"
                    "- 如果没序？随机打乱，再来一次！\n"
                    "- 重复直到偶然有序（或达到尝试次数上限）\n\n"
                    "要求：\n"
                    "- 实现 is_sorted 检查逻辑\n"
                    "- 设置合理的尝试次数上限（如 500000 次）\n"
                    "- 使用 random.shuffle 进行随机打乱\n\n"
                    "时间复杂度：O((n+1)!) 平均情况\n\n"
                    "⚠️ 注意：本题为娱乐性质，大数组可能永远跑不完！\n"
                    "建议输入长度 ≤ 6。"
                ),
                "difficulty": "整活 🤪",
                "algo_type": "any",
                "sort_rule": "strict",
                "complexity_ceiling": None,
                "example_code": EXAMPLE["bogo"],
                "is_meme": True,
                "test_cases": [
                    ("[3,1,2]", "[1,2,3]", True),
                    ("[1]", "[1]", True),
                    ("[]", "[]", True),
                ],
            },
            {
                "title": "睡眠排序（Sleep Sort）😴",
                "description": (
                    "😴 睡眠排序：让数字自己'睡醒'排队！\n\n"
                    "原理：\n"
                    "- 每个元素启动一个线程\n"
                    "- 线程 sleep 的时间 = 元素的值（可缩小比例加速）\n"
                    "- 睡醒后把值加入结果列表\n"
                    "- 数字小的先醒，自然形成有序序列\n\n"
                    "要求：\n"
                    "- 使用 threading 模块\n"
                    "- 线程安全：使用 Lock 保护共享结果列表\n"
                    "- 处理负数和零：sleep 时间不能为负（取 0）\n"
                    "- 设置 join timeout 防止线程卡死\n\n"
                    "⚠️ 注意：\n"
                    "- 排序耗时取决于最大值，与数组长度无关\n"
                    "- 小值先醒的特性依赖操作系统线程调度，不保证 100% 稳定\n"
                    "- 本题为娱乐性质，大数值会很慢！"
                ),
                "difficulty": "整活 🤪",
                "algo_type": "any",
                "sort_rule": "strict",
                "complexity_ceiling": None,
                "example_code": EXAMPLE["sleep"],
                "is_meme": True,
                "test_cases": [
                    ("[3,1,2]", "[1,2,3]", True),
                    ("[5,2,8]", "[2,5,8]", True),
                    ("[1]", "[1]", True),
                    ("[]", "[]", True),
                ],
            },
            {
                "title": "仁慈的斯大林排序（Merciful Stalin Sort）🙏",
                "description": (
                    "🙏 仁慈版斯大林排序：不枪毙，只'劳改'！\n\n"
                    "原始斯大林排序直接删除'破坏升序'的元素，太残忍了。\n"
                    "仁慈版本：\n"
                    "- 第一遍遍历，保留递增序列，把'不顺从'的元素收集到另一个列表\n"
                    "- 对'不顺从'列表递归执行同样的操作\n"
                    "- 最后将递归结果与保留序列归并（merge）\n\n"
                    "要求：\n"
                    "- 实现递归分解逻辑\n"
                    "- 实现两个有序序列的归并\n"
                    "- 展示递归过程（可在控制台打印）\n\n"
                    "区别：\n"
                    "- 原始斯大林：O(n)，丢失元素\n"
                    "- 仁慈斯大林：最坏 O(n²)，保留全部元素（正确排序）\n\n"
                    "示例：\n"
                    "输入：[3,1,4,2,5]\n"
                    "第一遍：保留 [3,4,5]，淘汰 [1,2]\n"
                    "递归：[1,2] 保留 [1,2]（已有序）\n"
                    "归并：[1,2] + [3,4,5] → [1,2,3,4,5]"
                ),
                "difficulty": "整活 🤪",
                "algo_type": "any",
                "sort_rule": "strict",
                "complexity_ceiling": None,
                "example_code": EXAMPLE["merciful_stalin"],
                "is_meme": True,
                "test_cases": [
                    ("[3,1,4,2,5]", "[1,2,3,4,5]", True),
                    ("[8,3,5,1,9,2,6,4,7,0]", "[0,1,2,3,4,5,6,7,8,9]", True),
                    ("[5,4,3,2,1]", "[1,2,3,4,5]", True),
                    ("[1,2,3,4,5]", "[1,2,3,4,5]", False),
                    ("[1]", "[1]", True),
                    ("[]", "[]", True),
                    ("[15,2,88,34,7,91,0,42,66,13]", "[0,2,7,13,15,34,42,66,88,91]", False),
                ],
            },
        ]

        for pd in problems_data:
            problem = Problem(
                title=pd["title"],
                description=pd["description"],
                difficulty=pd["difficulty"],
                algo_type=pd["algo_type"],
                sort_rule=pd["sort_rule"],
                complexity_ceiling=pd.get("complexity_ceiling"),
                example_code=pd.get("example_code", ""),
                is_meme=pd.get("is_meme", False),
                created_by=teacher.id,
            )
            db.session.add(problem)
            db.session.flush()

            for inp, exp, pub in pd["test_cases"]:
                tc = TestCase(
                    problem_id=problem.id,
                    input_data=inp,
                    expected_output=exp,
                    is_public=pub,
                )
                db.session.add(tc)

        db.session.commit()

        # 统计输出
        user_count = User.query.count()
        problem_count = Problem.query.count()
        tc_count = TestCase.query.count()

        print("=" * 50)
        print("种子数据导入完成！")
        print(f"   用户：{user_count} 人（3 学生 + 1 教师）")
        print(f"   题目：{problem_count} 道（含 4 道整活题）")
        print(f"   测试用例：{tc_count} 个")
        print()
        print("   演示账号：")
        print("     学生：student1 / 123456")
        print("     教师：teacher1 / 123456")
        print("=" * 50)


if __name__ == "__main__":
    seed()