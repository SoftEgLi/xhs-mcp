"""XHS MCP - A Model Context Protocol server for Xiaohongshu automation."""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .mcp_server import main
from .mcp_util import AuthManager
from .image_generate import image_generation_deepseek, download_and_save_images

__all__ = [
    "main",
    "AuthManager", 
    "image_generation_deepseek",
    "download_and_save_images"
]