"""应用入口：启动 Flask 开发服务器。

用法：
    python run.py              # 默认 debug 模式
    FLASK_DEBUG=0 python run.py # 关闭 debug
"""
import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(debug=debug, host="127.0.0.1", port=5000)
