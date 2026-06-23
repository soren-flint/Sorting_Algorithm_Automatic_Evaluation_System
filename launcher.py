"""排序算法学习系统 — 一键启动器。

自动检测 Python 环境 → 安装依赖 → 初始化数据库 → 启动 Flask → 打开浏览器。

用法：
    python launcher.py          # 默认端口 5000
    python launcher.py 8080     # 指定端口
"""
import os
import subprocess
import sys
import time
import webbrowser


def check_python() -> bool:
    """检查 Python 版本 >= 3.10。"""
    major, minor = sys.version_info[:2]
    if (major, minor) < (3, 10):
        print(f"[!] 当前 Python {major}.{minor}，需要 3.10+，请升级。")
        return False
    print(f"[✓] Python {major}.{minor}.{sys.version_info.micro}")
    return True


def install_deps() -> bool:
    """安装 requirements.txt 中的依赖。"""
    req_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if not os.path.exists(req_file):
        print("[!] 未找到 requirements.txt，跳过依赖安装。")
        return True
    print("[…] 正在安装依赖…")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", req_file, "-q"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("[✓] 依赖安装完成")
        return True
    except subprocess.CalledProcessError:
        print("[!] 依赖安装失败，尝试继续启动…")
        return False  # 通知调用方，但 main() 不阻断


def seed_db() -> bool:
    """初始化种子数据（幂等）。"""
    seed_path = os.path.join(os.path.dirname(__file__), "seed.py")
    if not os.path.exists(seed_path):
        print("[!] 未找到 seed.py，跳过数据初始化。")
        return True
    print("[…] 正在初始化数据库…")
    try:
        subprocess.check_call(
            [sys.executable, seed_path],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        print("[✓] 数据库初始化完成")
        return True
    except subprocess.CalledProcessError:
        print("[!] 数据库初始化失败")
        return False


def start_flask(port: int = 5000):
    """启动 Flask 开发服务器并打开浏览器。"""
    run_path = os.path.join(os.path.dirname(__file__), "run.py")
    url = f"http://127.0.0.1:{port}"

    print(f"\n{'='*50}")
    print(f"  排序算法学习系统")
    print(f"  地址: {url}")
    print(f"  按 Ctrl+C 停止服务器")
    print(f"{'='*50}\n")

    # 延迟打开浏览器，等 Flask 就绪
    def _open_browser():
        time.sleep(1.5)
        webbrowser.open(url)

    import threading
    threading.Thread(target=_open_browser, daemon=True).start()

    # 启动 Flask
    env = os.environ.copy()
    env["FLASK_DEBUG"] = "1"
    subprocess.run(
        [sys.executable, run_path],
        env=env,
    )


def main():
    print("\n" + "=" * 50)
    print("  排序算法学习系统 — 一键启动器")
    print("=" * 50 + "\n")

    if not check_python():
        input("\n按回车键退出…")
        sys.exit(1)

    install_deps()  # 失败不阻断启动（函数内部已处理）

    if not seed_db():
        input("\n按回车键退出…")
        sys.exit(1)

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    try:
        start_flask(port)
    except KeyboardInterrupt:
        print("\n服务器已停止。")


if __name__ == "__main__":
    main()