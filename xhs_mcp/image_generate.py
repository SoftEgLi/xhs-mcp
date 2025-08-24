import json
import httpx
import logging
import asyncio
import time
import random
import os
from openai import OpenAI
from html2image import Html2Image

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='./app.log',
    filemode='a',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)
api_key = os.getenv("DEEPSEEK_API_KEY")
base_url = "https://api.deepseek.com"

client = OpenAI(api_key=api_key, base_url=base_url)
# Please install OpenAI SDK first: `pip3 install openai`
html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>None</title>
    <style>
        /* 重置默认边距，让内容居中更方便 */
        body {{
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: flex-start;
            /* 让 body 内元素垂直方向先整体居中，再调整单个元素 */
            align-items: center; 
            height: 100vh;
            background-color: #fff;
            font-family: sans-serif;
        }}
        .container {{
            /* 移除text-align: center以允许文本左对齐 */
            /* 让 container 也成为 Flex 容器，方便内部元素垂直调整 */
            display: flex;
            flex-direction: column; 
            align-items: flex-start;
            margin-top: 20vh;
            padding-left: 20vw; /* 减小左边距，让文字更靠左 */
            padding-right: 20px; /* 添加右边距 */
            width: calc(90vw - 20px); /* 设置容器宽度，考虑左右padding */
        }}
        .title {{
            font-size: 48px; /* 控制文字大小，可按需调整 */
            font-weight: bold;
            margin-bottom: 20px;
            width: 100%; /* 让标题占满容器宽度 */
            word-wrap: break-word; /* 允许在任意字符间换行 */
            word-break: break-all; /* 允许在任意字符间换行 */
        }}
        /* 给需要调整位置的标题单独加类名，或者直接用 .title:first-child 选择 */
        .title-top {{
            /* 让这个元素在父容器（.container）的垂直方向上，比居中位置往上移 20px */
            align-self: flex-start;
            margin-bottom: calc(10vh);
            /* 解释：50vh 是页面垂直方向一半高度，减去 20px 后，元素底部到页面中间线是 20px，整体就偏上了 */
        }}
        .highlight {{
            background-color: #73f377; /* 绿色背景，模拟突出效果 */
            padding: 5px 10px;
            border-radius: 5px;
            display: inline-block; /* 让highlight也能换行 */
            max-width: 100%; /* 确保不会超出容器宽度 */
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 给要调整位置的标题加自定义类名 -->
        <div class="title title-top">{title_normal_part}</div> 
        <div class="title">
            <span class="highlight">{title_highlight_part}</span>
        </div>
    </div>
</body>
</html>
    """
# Helper for running sync file I/O in thread
async def read_system_prompt_async():
    try:
        with open('system_prompt.txt', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error("system_prompt.txt文件不存在")
        raise
    except Exception as e:
        logger.error(f"读取system_prompt.txt文件失败: {str(e)}")
        raise

async def ai_chat_text_async(user_prompt: str, system_prompt: str = None):
    # 从文件中异步读取system prompt
    # system_prompt = await read_system_prompt_async()
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})
    response = await asyncio.to_thread(
        client.chat.completions.create,
        model="deepseek-chat",
        messages=messages,
        stream=False
    )
    
    text = response.choices[0].message.content
    return text

def ai_chat_text(prompt: str):
    # 从文件中读取system prompt
    try:
        with open('system_prompt.txt', 'r', encoding='utf-8') as f:
            system_prompt = f.read()
    except FileNotFoundError:
        logger.error("system_prompt.txt文件不存在")
        raise FileNotFoundError("system_prompt.txt文件不存在")
    except Exception as e:
        logger.error(f"读取system_prompt.txt文件失败: {str(e)}")
        raise Exception(f"读取system_prompt.txt文件失败: {str(e)}")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        stream=False
    )
    
    html_code = response.choices[0].message.content
    return html_code

# Keep the original sync version if it's used elsewhere, or remove if ai_chat_text_async replaces all uses.
# For now, let's assume new async logic will use ai_chat_text_async.

def extract_html_code(html_code):
    # 查找第一个<div>标签
    start_index = html_code.find('```html')
    if start_index == -1:
        return html_code
    start_index += len('```html')

    # 查找最后一个```标签
    end_index = html_code.rfind('```')
    if end_index == -1:
        return html_code[start_index:]

    # 提取HTML代码
    html_code = html_code[start_index:end_index].strip()
    return html_code

async def image_generation_deepseek(image_prompt: str):
    """
    异步生成图片
    :param image_prompt: 图片描述,目前是文案内容
    :return: 图片保存到的本地路径
    """
    # 检查并创建临时图片存储目录 (os.makedirs is blocking but usually fast)
    # For strict non-blocking, these could also be wrapped, but often acceptable.
    if not os.path.exists('./tmp'):
        await asyncio.to_thread(os.makedirs, './tmp')
    if not os.path.exists('./tmp/images'):
        await asyncio.to_thread(os.makedirs, './tmp/images')
    
    image_urls = []
    summary_system_prompt = '''对内容进行提炼,拆分成title_normal_part和title_highlight_part两部分，前者是普通的话，后面是要加粗的部分。
    两个部分都要尽量简短，它们将作为小红书配图的文字，起到吸引人的作用。
    按如下格式输出，直接输出纯文本即可:
    {
    "title_normal_part": "小白必看",
    "title_highlight_part": "跨境电商"
    }
    '''
    summary_user_prompt = image_prompt
    summary_text = await ai_chat_text_async(user_prompt=summary_user_prompt, system_prompt=summary_system_prompt)
    logger.info(f'summary_text: {summary_text}')
    def extract_data(data, start_str, end_str):
        start_index = data.find(start_str)
        if start_index == -1:
            return data
        end_index = data.find(end_str)
        if end_index == -1:
            return data
        start_index = start_index + len(start_str)
        return data[start_index:end_index]

    data = extract_data(summary_text, "{", "}")
    data = json.loads(summary_text, strict=False)
    html_code = html_template.format(**data)
    logger.info(f'html_code for image: {html_code}') # Log snippet

    timestamp = int(time.time() * 1000)
    random_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
    image_path = f'deepseek_image_{timestamp}_{random_suffix}.png'
    
    def ImportImageFromExecl(html_code, outputPNGImage):
        if not os.path.exists('./tmp/images'):
            os.makedirs('./tmp/images')
        hti = Html2Image(custom_flags=['--no-sandbox'], size=(512, 500), output_path="./tmp/images")
        hti.screenshot(
            html_str=html_code,  # 直接传入 HTML 代码字符串
            save_as=outputPNGImage
    )
    # imgkit.from_string is a blocking I/O operation

    ImportImageFromExecl(html_code, image_path)
    image_path = f'./tmp/images/{image_path}'
    image_path = os.path.abspath(image_path) # 转换为绝对路径

    image_urls.append(image_path)

    logger.info(f'图片保存到的本地路径: {image_path}')
    return image_urls

async def download_and_save_images(image_urls):
    """
    下载图片
    :param image_urls: 图片的url列表
    :return: 图片保存到的本地路径
    """
    async with httpx.AsyncClient() as client:
        tasks = []
        for image_url in image_urls:
            tasks.append(client.get(image_url))

        responses = await asyncio.gather(*tasks)

        # 保存图片
        image_paths = []
        for response in responses:
            # 为每个图片生成独立的时间戳和随机数作为文件名
            timestamp = int(time.time() * 1000) 
            random_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
            image_path = f'./tmp/image_{timestamp}_{random_suffix}.png'
            with open(image_path, 'wb') as f:
                f.write(response.content)

            image_path = os.path.abspath(image_path) # 转换为绝对路径
            image_paths.append(image_path)
            
            # 确保下一张图片有不同的时间戳
            time.sleep(0.001)

        return image_paths
    

if __name__ == '__main__':
    # 创建事件循环
    loop = asyncio.get_event_loop()
    # 运行异步函数
    result = loop.run_until_complete(
        image_generation_deepseek('标题:上海游记\n内容:上海是一座充满魅力的城市，拥有丰富的历史和现代文化。从外滩的万国建筑群到陆家嘴的摩天大楼，上海展现了传统与现代的完美融合。漫步在南京路步行街，感受繁华的都市气息；或是探访田子坊，体验独特的艺术氛围。无论是美食、购物还是文化体验，上海都能满足你的需求。')
    )
    # 关闭事件循环
    loop.close()
