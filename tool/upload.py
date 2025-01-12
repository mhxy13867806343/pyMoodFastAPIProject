import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from fastapi import UploadFile
from config.upload_config import UPLOAD_DIR, UPLOAD_TYPES

class FileUploader:
    def __init__(self, upload_type: str, user_id: int):
        self.config = UPLOAD_TYPES.get(upload_type)
        if not self.config:
            raise ValueError(f"不支持的上传类型: {upload_type}")
        self.user_id = user_id
        self.upload_type = upload_type

    def get_file_md5(self, file_content: bytes) -> str:
        """计算文件内容的MD5值"""
        return hashlib.md5(file_content).hexdigest()

    def is_valid_file(self, filename: str, filesize: int) -> Tuple[bool, str]:
        """
        检查文件是否有效
        :return: (是否有效, 错误信息)
        """
        # 检查文件大小
        if filesize > self.config["max_size"]:
            max_size_mb = self.config["max_size"] / (1024 * 1024)
            return False, f"文件大小不能超过{max_size_mb}MB"
        
        # 检查文件扩展名
        ext = Path(filename).suffix.lower()
        if ext not in self.config["allowed_extensions"]:
            return False, f"只支持以下格式: {', '.join(self.config['allowed_extensions'])}"
        
        return True, ""

    def ensure_upload_dir(self) -> Path:
        """
        确保上传目录存在
        :return: 上传目录路径
        """
        # 创建日期目录
        today = datetime.now().strftime("%Y-%m-%d")
        upload_dir = UPLOAD_DIR / today / f"{self.upload_type}-{self.user_id}"
        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir

    async def save_file(self, file_data: bytes, original_filename: str) -> Tuple[bool, str, Optional[str]]:
        """
        保存单个文件
        :return: (是否成功, 消息, 相对路径)
        """
        try:
            # 验证文件
            is_valid, error_msg = self.is_valid_file(original_filename, len(file_data))
            if not is_valid:
                return False, error_msg, None

            # 获取文件MD5和扩展名
            file_md5 = self.get_file_md5(file_data)
            ext = Path(original_filename).suffix.lower()
            
            # 确保上传目录存在
            upload_dir = self.ensure_upload_dir()
            
            # 构建新文件名和路径
            new_filename = f"{file_md5}{ext}"
            file_path = upload_dir / new_filename
            
            # 写入文件
            with open(file_path, "wb") as f:
                f.write(file_data)
            
            # 返回相对路径
            relative_path = f"static/upload/{upload_dir.relative_to(UPLOAD_DIR)}/{new_filename}"
            return True, "上传成功", relative_path
            
        except Exception as e:
            return False, f"文件保存失败: {str(e)}", None

    async def process_files(self, files: List[UploadFile]) -> Dict[str, List]:
        """
        处理多个文件上传
        :return: 处理结果
        """
        if len(files) > self.config["max_files"]:
            return {
                "success": [],
                "failed": [{"name": f.filename, "error": f"超出最大上传数量限制({self.config['max_files']}个文件)"} 
                          for f in files]
            }

        results = {
            "success": [],
            "failed": []
        }

        for file in files:
            try:
                file_content = await file.read()
                success, message, path = await self.save_file(file_content, file.filename)
                
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
                    "error": str(e)
                })

        return results
