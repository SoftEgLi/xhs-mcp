# This program will automate Xiaohongshu login and save/load cookies.
# It will require manual intervention for the verification code step.
import os
import sys
# Get the current script's directory
current_dir = os.path.dirname(os.path.abspath(__file__))
# Add the parent directory to sys.path
sys.path.append(os.path.dirname(current_dir))
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

import pyperclip
import platform

from xhs_mcp.image_generate import image_generation_deepseek, download_and_save_images
import asyncio # 确保导入 asyncio

import time
import json
import os
import logging
import asyncio



# Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     filename='./app.log',
#     filemode='a',
#     encoding='utf-8'
# )
logger = logging.getLogger(__name__)


class AuthManager:
    def __init__(self, phone_number):
        self.phone_number = phone_number
        if not os.path.exists('./cookies'):
            os.makedirs('./cookies')
        self.COOKIE_FILE = f'./cookies/{phone_number}.json'
        # 使用webdriver-manager自动管理Chrome驱动程序
        chrome_service = ChromeService(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=chrome_service)
        # self.driver.maximize_window()

        self.has_cookie = self.load_cookies()
        logger.info(f"cookie文件路径: {os.path.abspath(self.COOKIE_FILE)}")
        self.driver.get("https://creator.xiaohongshu.com")
        # time.sleep(5)
        time.sleep(1)

    def __del__(self):
        # 在这里执行清理操作
        if self.driver:
            self.driver.quit()
            print("浏览器已关闭")


    def save_cookies(self):
        """Saves cookies to a file."""
        cookies = self.driver.get_cookies()
        # 如果文件存在则先清空文件内容
        if os.path.exists(self.COOKIE_FILE):
            open(self.COOKIE_FILE, 'w').close()
        # 重新写入cookies数据
        with open(self.COOKIE_FILE, 'w') as f:
            json.dump(cookies, f)
        logger.info(f"Cookies saved to {self.COOKIE_FILE}")
    
    def load_cookies(self):
        """Loads cookies from a file and adds them to the browser."""
        if not os.path.exists(self.COOKIE_FILE):
            logger.info('Cookie文件不存在，返回False')
            return False
        
        try:
            logger.info(f'从{self.COOKIE_FILE}加载cookies')
            with open(self.COOKIE_FILE, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            if not cookies or len(cookies) == 0:
                logger.info('cookies为空或不存在，返回False')
                return False
            self.driver.get("https://creator.xiaohongshu.com")
            for cookie in cookies:
                # Selenium requires domain to be set for adding cookies
                # Need to handle potential domain issues depending on the site
                # For simplicity, we'll add them after navigating to the site
                self.driver.add_cookie(cookie)
                
            logger.info(f'成功加载 {len(cookies)} 个cookies')
            self.driver.get("https://creator.xiaohongshu.com")
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            return True
            
        except Exception as e:
            logger.error(f'加载cookies出错: {str(e)}')
            return False
        
    def send_keys_with_emoji(self, element, text):
        try:
            pyperclip.copy(text)  # 向剪贴板写入文本
        except Exception as e:
            print(repr(e))

        # 判断操作系统
        current_os = platform.system()

        if current_os == "Darwin":  # macOS
            element.send_keys(Keys.COMMAND, 'v')  # 使用 Command + V 粘贴
        elif current_os in ["Windows", "Linux"]:
            element.send_keys(Keys.CONTROL, 'v')  # 使用 Ctrl + V 粘贴
        else:
            logger.error(f"不支持的操作系统: {current_os}")
            raise Exception("不支持的操作系统")

        element.send_keys(Keys.ENTER)  # 回车确认

    async def create_note(self, title, content, image_urls):
        # return f"创建笔记失败: {str(e)}"
        # 会在成功登录的情况调用该函数。
        """创建小红书笔记并上传图片."""
        # 启动图片生成任务
        image_generation_task = None
        if len(image_urls) == 0:
            logger.info("未提供图片URL，开始异步生成图片")
            # 注意：image_generation_deepseek 现在是异步的
            image_generation_task = asyncio.create_task(image_generation_deepseek(title))
        else:
            # 如果提供了URL，则异步下载它们
            image_generation_task = asyncio.create_task(download_and_save_images(image_urls))
        
        try:
            # 导航到发布笔记的页面
            self.driver.get("https://creator.xiaohongshu.com/publish/publish?from=menu")
            try:
                WebDriverWait(self.driver, 30).until(
                    lambda driver: driver.current_url != "https://creator.xiaohongshu.com/login"
                )
            except Exception as e:
                logger.error(f"等待页面跳转超时: {str(e)}")
                return "登录失败"
            
            if self.driver.current_url != "https://creator.xiaohongshu.com/publish/publish?from=menu":
                return "登录失败"

            # 关闭遮挡层
            try:
                tooltip_close_btn = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "body > div.d-popover.d-popover-default > div.short-note-tooltip > button > div > span"))
                )
                # 点击关闭遮挡层
                tooltip_close_btn.click()
                time.sleep(0.3)  # 关闭后稍等，确保弹窗消失
            except Exception as e:
                logger.error(f"关闭遮挡层出错: {str(e)}")

            # 切换到上传图文按钮对应的栏目
            upload_text_elem = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#web .header .header-tabs > div:nth-child(3) > span"))
            )
            upload_text_elem.click()
            # 点击上传图文按钮
            # tabs = WebDriverWait(self.driver, 20).until(
            #     EC.presence_of_element_located((By.CSS_SELECTOR, "#web > div > div > div > div.upload-content > div.upload-wrapper > div > div > div > button:nth-child(1)"))
            # )
            # tabs.click()
            # time.sleep(1)
            # logger.info("点击了上传图文按钮")
        except Exception as e:
            logger.error(f"点击上传图文按钮出错: {str(e)}")
            return f"创建笔记失败: {str(e)}"

        
        # 在等待图片生成/下载的同时，可以执行一些不依赖图片的浏览器操作
        # 例如，导航到页面，点击按钮等，如果这些操作可以在图片准备好之前完成
        # image_urls = ["E:\\Code\\funny\\my_rednote_mcp\\xhs\\src\\tmp\\images\\deepseek_image_1749181891241_4ng5zf.png"]
        # 等待图片生成/下载任务完成
        if image_generation_task:
            image_urls = await image_generation_task
            logger.info(f"图片处理完成，本地路径为: {image_urls}")
        
        if not image_urls:
            logger.error("图片生成或下载失败，无法继续发布笔记")
            return "创建笔记失败: 图片处理失败"
        msg = None
        try:
            file_input_selector = '.upload-input'
            file_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, file_input_selector))
            )
            logger.info("找到文件上传输入框")

            # 将图片文件路径发送给输入框
            # Selenium会自动处理多个文件路径，用换行符分隔
            image_paths_string = "\n".join(image_urls) # image_urls 应该是本地文件路径列表

            # 调试：检查每个图片路径是否存在
            for img_path in image_urls:
                if not os.path.exists(img_path):
                    logger.error(f"图片文件不存在: {img_path}")
                    # 可以选择在这里抛出异常或返回错误信息
                    return f"创建笔记失败: 图片文件不存在: {img_path}"
                else:
                    logger.info(f"图片文件存在: {img_path}")

            logger.info(f"准备发送给Selenium的文件路径字符串:\n{image_paths_string}")

            file_input.send_keys(image_paths_string)
            logger.info(f"已发送 {len(image_urls)} 个图片文件路径")

            # 填写标题和内容，并点击发布按钮
            # 标题HTML代码:<div class="d-input --color-text-title --color-bg-fill"><!----><input class="d-text" type="text" placeholder="填写标题会有更多赞哦～" value=""><!----><!----><!----></div>
            # 使用XPath定位标题输入框
            title_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".d-text"))
            )
            if len(title) > 20:
                title = title[:20]
            self.send_keys_with_emoji(title_input, title)
            # title_input.send_keys(title)
            logger.info(f"已输入标题: {title}")
            time.sleep(1)
            # 内容HTML代码:<div contenteditable="true" role="textbox" translate="no" class="tiptap ProseMirror" tabindex="0"><p data-placeholder="输入正文描述，真诚有价值的分享予人温暖" class="is-empty is-editor-empty"><br class="ProseMirror-trailingBreak"></p></div>
            content_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".tiptap.ProseMirror"))
            )
            self.send_keys_with_emoji(content_input, content)

            # content_input.send_keys(content)
            logger.info(f"已输入内容: {content}")
            # 发布按钮HTML代码:<span class="d-text --color-static --color-current --size-text-paragraph d-text-nowrap d-text-ellipsis d-text-nowrap" style="text-underline-offset: auto;"><!---->发布<!----><!----><!----></span>
            # 发布button HTML代码：<button data-v-34b0c0bc="" data-v-30daec93="" data-v-0624972c-s="" type="button" class="d-button d-button-large --size-icon-large --size-text-h6 d-button-with-content --color-static bold --color-bg-fill --color-text-paragraph custom-button red publishBtn" data-impression="{&quot;noteTarget&quot;:{&quot;type&quot;:&quot;NoteTarget&quot;,&quot;value&quot;:{&quot;noteEditSource&quot;:1,&quot;noteType&quot;:1}},&quot;event&quot;:{&quot;type&quot;:&quot;Event&quot;,&quot;value&quot;:{&quot;targetType&quot;:{&quot;type&quot;:&quot;RichTargetType&quot;,&quot;value&quot;:&quot;note_compose_target&quot;},&quot;action&quot;:{&quot;type&quot;:&quot;NormalizedAction&quot;,&quot;value&quot;:&quot;impression&quot;},&quot;pointId&quot;:50979}},&quot;page&quot;:{&quot;type&quot;:&quot;Page&quot;,&quot;value&quot;:{&quot;pageInstance&quot;:{&quot;type&quot;:&quot;PageInstance&quot;,&quot;value&quot;:&quot;creator_service_platform&quot;}}}}"><div class="d-button-content"><!----><span class="d-text --color-static --color-current --size-text-paragraph d-text-nowrap d-text-ellipsis d-text-nowrap" style="text-underline-offset: auto;"><!---->发布<!----><!----><!----></span><!----></div></button>
            publish_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".publishBtn"))
            )
            # 等待图片上传完毕
            time.sleep(3)
            publish_button.click()
            time.sleep(2)
            logger.info("点击了发布按钮")

            logger.info("笔记创建流程已执行图片上传步骤")
            msg = "成功发布到小红书上" # 或者根据实际情况返回发布结果

        except Exception as e:
            logger.error(f"创建笔记出错: {str(e)}")
            msg = f"发送小红书失败: {str(e)}"

        finally:
            # 删除本地图片
            for image_path in image_urls:
                if os.path.exists(image_path):
                    os.remove(image_path)
                    logger.info(f"已删除本地图片: {image_path}")
                else:
                    logger.warning(f"本地图片不存在: {image_path}")
            return msg

        

    def login_with_verification_code(self, verification_code):
        """Automates the login process."""
        # 尝试加载Cookie来快速登录，如果不成功，重新进行手机验证码登录流程
        if self.has_cookie:
            logger.info("Attempted login with saved cookies.")
            if self.driver.current_url != "https://creator.xiaohongshu.com/login":
                print("使用cookies登录成功")
                return "登录成功"
            else:
                # Continue with manual login steps if cookie login fails
                self.driver.delete_all_cookies()
                logger.info("Saved cookies did not result in login. Proceeding with manual login.")
                # return None
        else:
            logger.info("No saved cookies found. Proceeding with manual login.")

        try:
            phone_input = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='手机号']")))
            phone_input.clear()
            phone_input.send_keys(self.phone_number)
        except:
            logger.info("Phone number input not found.")
            return "登录失败，网页可能发生变动，请联系维护人员"

        code_input = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='验证码']")))
        code_input.clear()
        code_input.send_keys(verification_code)

        # 点击登录按钮
        login_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".beer-login-btn")))
        login_button.click()

        # 等待登录成功,获取token
        try:
            WebDriverWait(self.driver, 3).until(
                lambda driver: driver.current_url != "https://creator.xiaohongshu.com/login"
            )
        except Exception as e:
            logger.error(f"等待页面跳转超时: {str(e)}")
            return "登录失败"
        # 保存cookies
        self.save_cookies()
        return "登录成功"
    

    def login_without_verification_code(self):
        """Automates the login process."""
        # 尝试加载Cookie来快速登录，如果不成功，重新进行手机验证码登录流程
        if self.has_cookie:
            logger.info("Attempted login with saved cookies.")
            if self.driver.current_url != "https://creator.xiaohongshu.com/login":
                print("使用cookies登录成功")
                return "登录成功"
            else:
                # Continue with manual login steps if cookie login fails
                self.driver.delete_all_cookies()
                logger.info("Saved cookies did not result in login. Proceeding with manual login.")
                # return None
        else:
            logger.info("No saved cookies found. Proceeding with manual login.")

        try:
            phone_input = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='手机号']")))
            phone_input.clear()
            phone_input.send_keys(self.phone_number)
        except:
            logger.info("Phone number input not found.")
            return "登录失败，网页可能发生变动，请联系维护人员"
        # <span class="login-btn" data-v-a93a7d02="">登录</span>
        try:
            send_code_btn = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".css-uyobdj")))
            send_code_btn.click()
            time.sleep(3)
        except:
            # 尝试其他可能的选择器
            try:
                send_code_btn = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".css-1vfl29")))
                send_code_btn.click()
            except:
                try:
                    send_code_btn = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'发送验证码')]")))
                    send_code_btn.click()
                except:
                    return "无法找到发送验证码按钮"

        return "发送验证码成功,请提醒用户输入验证码"
        


if __name__ == "__main__":
    # Replace with the phone number you want to use
    your_phone_number = "xxxx"
    
    # IMPORTANT: You will need to manually enter the verification code in the browser window that opens.
    auth = AuthManager(your_phone_number)
    msg = auth.login_without_verification_code()
    # msg = auth.login_with_verification_code("367699")

    
    async def main():
        # msg = await auth.create_note('🔥3年亚马逊老司机吐血整理！', '🔥3年亚马逊老司机吐血整理！', [])
        msg = await auth.create_note('🔥3年亚马逊老司机吐血整理！', '🔥', [])
    

    asyncio.run(main())
    while(True):
        pass