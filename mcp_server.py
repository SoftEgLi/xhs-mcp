from mcp.server.fastmcp import FastMCP
import time
import os
import sys
# Get the current script's directory
current_dir = os.path.dirname(os.path.abspath(__file__))
# Add the parent directory to sys.path
sys.path.append(os.path.dirname(current_dir))
from .mcp_util import AuthManager
import time

# # 初始化 FastMCP 服务器
mcp = FastMCP('xhs')

@mcp.tool()
def login_with_verification_code(phone_number: str, verification_code: str) -> str:
    """
    通过验证码的方式登录小红书账号，当不带验证码的方式登录小红书账号失败时使用
    Args:
        phone_number: 待登录账号的手机号
        verification_code: 验证码
    Returns:
        登录结果
    """
    auth_manager = AuthManager(phone_number)
    result = auth_manager.login_with_verification_code(verification_code)
    return result

@mcp.tool()
def login_without_verification_code(phone_number: str) -> str:
    """
    不带验证码的方式登录小红书账号
    Args:
        phone_number: 待登录账号的手机号
    Returns:
        登录结果
    """
    auth_manager = AuthManager(phone_number)
    msg = auth_manager.login_without_verification_code()
    # time.sleep(5) # Wait for the login process to complete
    if msg:
        return msg
    else:
        return "登录失败，请检查手机号是否正确"

# @mcp.tool()
# def create_note(phone_number: str, title: str, content: str, image_urls: list) -> str:
@mcp.tool()
async def create_note(phone_number: str, title: str, content: str, image_urls: list[str]) -> str:
    """
    将文章发布到某个手机号的小红书上，不需要先登录小红书，可以直接调用该接口。
    Args:
        phone_number: 待登录账号的手机号
        title: 文章标题
        content: 文章内容
        image_urls: 用户上传图片的url列表
    Returns:
        发布结果
    """
    auth_manager = AuthManager(phone_number)
    msg = auth_manager.login_without_verification_code()
    # time.sleep(5) # Wait for the login process to complete
    if msg != "登录成功":
        return "未登录," + msg
    msg = await auth_manager.create_note(title, content, image_urls)
    return msg

def main():
    # 启动 MCP 服务器
    mcp.run(transport='stdio')
    
if __name__ == "__main__":
    # 以标准 I/O 方式运行 MCP 服务器
    main()