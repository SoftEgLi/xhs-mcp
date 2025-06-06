# xhs-mcp
一个小红书的MCP服务器，支持通过对话的方式进行账号登陆、文案生成、以及自动发布。相比于已有的实现，优势在于登陆账号以及文案发布全部可以在对话过程中自动实现，并能支持多个账号批量发布文案。此外，在调用发表文章的接口时，该工具还支持自动根据文案内容生成小红书配图。
## 原理
使用浏览器模拟的方式，通过驱动启动谷歌浏览器，来自动进行账号登录（会发送验证码到手机上），以及发布文案。登录后，会将Cookie保存下来，之后发布文章就不再需要重新登录了。
## 示例
<img src="https://github.com/user-attachments/assets/6df5e84e-449a-42a6-ad87-23ed2eb67124" alt="Snipaste_2025-06-04_17-40-50" width="50%">

## 环境配置
1. 查找你的 Chrome 浏览器版本，例如 "136.0.7103.93"然后到https://googlechromelabs.github.io/chrome-for-testing/ 上下载对应版本的chromedriver，解压后将chromedriver.exe所在的文件夹添加到环境变量的Path中。
2. 安装uv
```
pip install uv
```
## 启动服务器
在生成小红书文案的配图时，用到了DeepSeek的chat模型，所以需要配置DEEPSEEK_API_KEY。
### 方式1：直接运行命令
```
env DEEPSEEK_API_KEY=xxxx uvx --from lcl_xhs_mcp==0.3.25 xhs-server
```
### 方式2: 配置文件运行
在配置文件中添加
```
{
  "mcpServers": {
    "xhs": {
      "command": "env",
      "args": [
        "DEEPSEEK_API_KEY=xxxx",
        "uvx",
        "--from",
        "lcl_xhs_mcp==0.3.25",
        "xhs-server"
      ]
    }
  }
}
```
## 注意事项
Cookie的有效期是一个月，如果你自己在网页上登录了小红书，那么之前的Cookie会失效。
## 开源协议
使用MIT协议。

