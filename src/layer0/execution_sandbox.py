"""
代码执行沙箱 - Layer 0: 基础设施层

基于 Docker 容器提供安全的代码执行环境（纯工具封装，无智能能力）
"""

import docker
import tempfile
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class ExecutionEnvironment(Enum):
    """支持的执行环境"""
    PYTHON = "python"
    GO = "go"
    SWIFT = "swift"
    NODE = "node"


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    output: str
    error: Optional[str]
    exit_code: int
    execution_time: float  # 秒


class ExecutionSandbox:
    """
    代码执行沙箱

    功能:
    - Docker 容器隔离执行
    - 支持多语言 (Python/Go/Swift/Node)
    - 资源限制 (CPU/内存/超时)
    - 安全性保障 (网络隔离/文件系统隔离)
    """

    def __init__(
        self,
        memory_limit: str = "512m",
        cpu_limit: float = 1.0,
        timeout: int = 30,
    ):
        """
        初始化沙箱

        Args:
            memory_limit: 内存限制 (如 "512m", "1g")
            cpu_limit: CPU 限制 (如 1.0 = 1核)
            timeout: 超时时间（秒）
        """
        self.client = docker.from_env()
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self.timeout = timeout

    def execute(
        self,
        code: str,
        environment: ExecutionEnvironment,
        files: Optional[Dict[str, str]] = None,
    ) -> ExecutionResult:
        """
        在沙箱中执行代码

        Args:
            code: 要执行的代码
            environment: 执行环境
            files: 额外文件 {"path": "content"}

        Returns:
            ExecutionResult: 执行结果
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # 准备代码文件
            code_file = self._prepare_code_file(temp_dir, code, environment)
            if files:
                self._prepare_additional_files(temp_dir, files)

            # 选择镜像和命令
            image, command = self._get_environment_config(environment, code_file.name)

            try:
                # 运行容器
                container = self.client.containers.run(
                    image=image,
                    command=command,
                    volumes={temp_dir: {"bind": "/workspace", "mode": "rw"}},
                    working_dir="/workspace",
                    mem_limit=self.memory_limit,
                    cpu_period=100000,
                    cpu_quota=int(100000 * self.cpu_limit),
                    network_disabled=True,  # 网络隔离
                    remove=False,
                    detach=True,
                )

                # 等待执行完成
                result = container.wait(timeout=self.timeout)

                # 读取输出
                logs = container.logs().decode("utf-8")
                container.remove()

                return ExecutionResult(
                    success=result["StatusCode"] == 0,
                    output=logs,
                    error=None if result["StatusCode"] == 0 else logs,
                    exit_code=result["StatusCode"],
                    execution_time=0.0,  # TODO: 实现精确计时
                )

            except Exception as e:
                return ExecutionResult(
                    success=False,
                    output="",
                    error=str(e),
                    exit_code=-1,
                    execution_time=0.0,
                )

    def _prepare_code_file(
        self,
        temp_dir: str,
        code: str,
        environment: ExecutionEnvironment,
    ) -> Path:
        """准备代码文件"""
        extensions = {
            ExecutionEnvironment.PYTHON: ".py",
            ExecutionEnvironment.GO: ".go",
            ExecutionEnvironment.SWIFT: ".swift",
            ExecutionEnvironment.NODE: ".js",
        }

        ext = extensions[environment]
        filename = f"main{ext}"
        filepath = Path(temp_dir) / filename

        with open(filepath, "w") as f:
            f.write(code)

        return filepath

    def _prepare_additional_files(self, temp_dir: str, files: Dict[str, str]):
        """准备额外文件"""
        for path, content in files.items():
            filepath = Path(temp_dir) / path
            filepath.parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, "w") as f:
                f.write(content)

    def _get_environment_config(
        self,
        environment: ExecutionEnvironment,
        filename: str,
    ) -> tuple[str, list[str]]:
        """
        获取环境的镜像和命令

        Returns:
            (镜像名, 命令列表)
        """
        configs = {
            ExecutionEnvironment.PYTHON: (
                "python:3.11-slim",
                ["python", f"/workspace/{filename}"],
            ),
            ExecutionEnvironment.GO: (
                "golang:1.24",
                ["go", "run", f"/workspace/{filename}"],
            ),
            ExecutionEnvironment.SWIFT: (
                "swift:5.9",
                ["swift", f"/workspace/{filename}"],
            ),
            ExecutionEnvironment.NODE: (
                "node:20",
                ["node", f"/workspace/{filename}"],
            ),
        }

        return configs[environment]

    def cleanup(self):
        """清理资源"""
        # 停止所有运行中的容器
        for container in self.client.containers.list(all=True):
            if "sandbox" in container.name:
                container.remove(force=True)
