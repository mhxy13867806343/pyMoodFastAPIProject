import os
from pathlib import Path

# 获取项目根目录
ROOT_DIR = Path(__file__).parent.parent

# 基础配置
UPLOAD_DIR = ROOT_DIR / "static" / "upload"
# 确保上传目录存在
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 图片配置
IMAGE_CONFIG = {
    "max_size": 10 * 1024 * 1024,  # 10MB
    "allowed_extensions": {'.png', '.jpg', '.jpeg', '.webp'},
    "max_files": 9,  # 最大上传数量
}

# 视频配置
VIDEO_CONFIG = {
    "max_size": 100 * 1024 * 1024,  # 100MB
    "allowed_extensions": {'.mp4', '.mov', '.avi'},
    "max_files": 1,  # 最大上传数量
}

# 上传类型
UPLOAD_TYPES = {
    "image": IMAGE_CONFIG,
    "video": VIDEO_CONFIG,
}
