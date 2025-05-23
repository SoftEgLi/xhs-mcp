import json
import httpx
import logging
import asyncio
import time
import random
import os
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='E:/Code/funny/my_rednote_mcp/xhs/image_server.log',
    filemode='a',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

async def image_generation(image_prompt: str):
    """
    生成图片
    :param image_prompt: 图片描述，需要是英文
    :return: 图片保存到的本地路径
    """
    # 检查并创建临时图片存储目录
    if not os.path.exists('./tmp'):
        os.makedirs('./tmp')
    if not os.path.exists('./tmp/images'):
        os.makedirs('./tmp/images')

    async with httpx.AsyncClient() as client:
        data = {'data': [image_prompt, 0, True, 512, 512, 3]}

        # 创建生成图片任务
        response1 = await client.post(
            'https://black-forest-labs-flux-1-schnell.hf.space/call/infer',
            json=data,
            headers={"Content-Type": "application/json"}
        )

        # 解析响应获取事件 ID
        response_data = response1.json()
        event_id = response_data.get('event_id')

        if not event_id:
            return '无法获取事件 ID'

        # 通过流式的方式拿到返回数据
        url = f'https://black-forest-labs-flux-1-schnell.hf.space/call/infer/{event_id}'
        full_response = ''
        async with client.stream('GET', url) as response2:
            async for chunk in response2.aiter_text():
                full_response += chunk
        logger.info(f"full_response:{full_response}")
        image_remote_url = json.loads(full_response.split('data: ')[-1])[0]['url']
        # 下载图片
        image_urls = [image_remote_url]
        local_image_urls = await download_and_save_images(image_urls)
        return local_image_urls

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
    
