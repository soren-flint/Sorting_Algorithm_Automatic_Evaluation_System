"""应用配置——支持环境变量覆盖。"""
import os


def _get_secret_key() -> str:
    """获取 SECRET_KEY：优先环境变量 → 持久化文件 → 随机生成并持久化。

    文件持久化确保开发环境下重启不会导致所有 session 失效。
    """
    env_key = os.environ.get("SECRET_KEY")
    if env_key:
        return env_key

    instance_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "instance"
    )
    key_file = os.path.join(instance_dir, ".secret_key")

    # 尝试读取已持久化的 key
    try:
        with open(key_file, "r") as f:
            saved = f.read().strip()
            if saved:
                return saved
    except FileNotFoundError:
        pass

    # 生成新 key 并写入文件
    import secrets
    new_key = secrets.token_hex(32)
    os.makedirs(os.path.dirname(key_file), exist_ok=True)
    with open(key_file, "w") as f:
        f.write(new_key)
    return new_key


class Config:
    """基础配置。"""
    SECRET_KEY = _get_secret_key()
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance', 'judge.db')}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SANDBOX_TIMEOUT = int(os.environ.get("SANDBOX_TIMEOUT", "5"))
    MAX_STEPS = int(os.environ.get("MAX_STEPS", "500"))
    SIMILARITY_THRESHOLD = float(os.environ.get("SIMILARITY_THRESHOLD", "0.85"))
    OUTPUT_SIZE_LIMIT = int(os.environ.get("OUTPUT_SIZE_LIMIT", "100000"))
