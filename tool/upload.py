import hashlib
from pathlib import Path
from datetime import datetime
from typing import Tuple, List, Dict
from fastapi import UploadFile
from config.upload_config import UPLOAD_TYPES, UPLOAD_DIR
from config.error_messages import USER_ERROR

class FileUploader:
    def __init__(self, user_id: int):
        """
        初始化文件上传器
        :param user_id: 用户ID
        """
        self.user_id = user_id

    def _get_upload_type(self, filename: str) -> str:
        """
        根据文件扩展名判断上传类型
        :return: 'image' 或 'video'
        """
        ext = Path(filename).suffix.lower()
        for upload_type, config in UPLOAD_TYPES.items():
            if ext in config["allowed_extensions"]:
                return upload_type
        return ""

    def _is_valid_file(self, filename: str, filesize: int, upload_type: str) -> Tuple[bool, str]:
        """
        检查文件是否有效
        :return: (是否有效, 错误信息)
        """
        config = UPLOAD_TYPES.get(upload_type)
        if not config:
            return False, USER_ERROR["FILE_TYPE_ERROR"]

        # 检查文件大小
        if filesize > config["max_size"]:
            max_size_mb = config["max_size"] / (1024 * 1024)
            if upload_type == "video":
                return False, USER_ERROR["VIDEO_TOO_LARGE"]
            else:
                return False, USER_ERROR["IMAGE_TOO_LARGE"]
        
        # 检查文件扩展名
        ext = Path(filename).suffix.lower()
        if ext not in config["allowed_extensions"]:
            return False, USER_ERROR["FILE_TYPE_ERROR"]
        
        return True, ""

    def _get_file_md5(self, file_content: bytes) -> str:
        """计算文件内容的MD5值"""
        return hashlib.md5(file_content).hexdigest()

    def _ensure_upload_dir(self, upload_type: str) -> Path:
        """
        确保上传目录存在
        :return: 上传目录路径
        """
        today = datetime.now().strftime("%Y-%m-%d")
        upload_dir = UPLOAD_DIR / today / f"{upload_type}-{self.user_id}"
        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir

    async def save_file(self, file_content: bytes, filename: str) -> Tuple[bool, str, str]:
        """
        保存文件
        :param file_content: 文件内容
        :param filename: 原始文件名
        :return: (是否成功, 消息, 文件路径)
        """
        # 自动识别上传类型
        upload_type = self._get_upload_type(filename)
        if not upload_type:
            return False, "不支持的文件类型", ""

        # 验证文件
        is_valid, error_msg = self._is_valid_file(filename, len(file_content), upload_type)
        if not is_valid:
            return False, error_msg, ""

        # 获取文件MD5和扩展名
        file_md5 = self._get_file_md5(file_content)
        ext = Path(filename).suffix.lower()
        
        # 确保上传目录存在
        upload_dir = self._ensure_upload_dir(upload_type)
        
        # 构建新文件名和路径
        new_filename = f"{file_md5}{ext}"
        file_path = upload_dir / new_filename
        
        # 写入文件
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # 返回相对路径
        relative_path = f"static/upload/{upload_dir.relative_to(UPLOAD_DIR)}/{new_filename}"
        return True, "上传成功", relative_path

    async def process_files(self, files: List[UploadFile]) -> Dict[str, List]:
        """
        批量处理文件
        :param files: 文件列表
        :return: 处理结果，包含成功和失败的文件信息
        """
        results = {
            "success": [],
            "failed": []
        }

        # 按类型分组文件
        image_files = []
        video_files = []

        for file in files:
            upload_type = self._get_upload_type(file.filename)
            if upload_type == "image":
                image_files.append(file)
            elif upload_type == "video":
                video_files.append(file)
            else:
                results["failed"].append({
                    "name": file.filename,
                    "error": "不支持的文件类型"
                })

        # 检查文件数量限制
        image_config = UPLOAD_TYPES["image"]
        video_config = UPLOAD_TYPES["video"]

        if len(image_files) > image_config["max_files"]:
            results["failed"].extend([
                {"name": f.filename, "error": f"图片数量超出限制（最多{image_config['max_files']}个）"}
                for f in image_files[image_config["max_files"]:]
            ])
            image_files = image_files[:image_config["max_files"]]

        if len(video_files) > video_config["max_files"]:
            results["failed"].extend([
                {"name": f.filename, "error": f"视频数量超出限制（最多{video_config['max_files']}个）"}
                for f in video_files[video_config["max_files"]:]
            ])
            video_files = video_files[:video_config["max_files"]]

        # 处理所有有效文件
        for file in image_files + video_files:
            try:
                content = await file.read()
                success, message, path = await self.save_file(content, file.filename)
                
                if success:
                    results["success"].append({
                        "name": file.filename,
                        "url": path
                    })
                else:
                    results["failed"].append({
                        "name": file.filename,
                        "error": message
                    })
                    
            except Exception as e:
                results["failed"].append({
                    "name": file.filename,
                    "error": f"处理文件失败: {str(e)}"
                })
            finally:
                # 确保文件指针回到开始位置，以便后续可能的读取
                await file.seek(0)

        return results
