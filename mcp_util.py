# This program will automate Xiaohongshu login and save/load cookies.
# It will require manual intervention for the verification code step.

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from image_generate import image_generation, download_and_save_images

import time
import json
import os
import logging



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='./app.log',
    filemode='a',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)
class AuthManager:
    def __init__(self, phone_number):
        self.phone_number = phone_number
        if not os.path.exists('./cookies'):
            os.makedirs('./cookies')
        self.COOKIE_FILE = f'./cookies/{phone_number}.json'
        self.driver=None

    def __del__(self):
        # 在这里执行清理操作
        if self.driver:
            self.driver.quit()
            print("浏览器已关闭")


    def save_cookies(self):
        """Saves cookies to a file."""
        cookies = self.driver.get_cookies()
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

            for cookie in cookies:
                # Selenium requires domain to be set for adding cookies
                # Need to handle potential domain issues depending on the site
                # For simplicity, we'll add them after navigating to the site
                self.driver.add_cookie(cookie)
                
            logger.info(f'成功加载 {len(cookies)} 个cookies')
            return True
            
        except Exception as e:
            logger.error(f'加载cookies出错: {str(e)}')
            return False

    async def create_note(self, title, content, image_urls):
        """创建小红书笔记并上传图片."""
        if len(image_urls) == 0:
            image_urls = await image_generation(title)
        else:
            image_urls = await download_and_save_images(image_urls)

        try:
            # 导航到发布笔记的页面
            self.driver.get("https://creator.xiaohongshu.com/publish/publish?source=official&from=menu")
            # time.sleep(5)
            # HTML:<span data-v-16fdb080="" class="title">上传图文</span>
            # HTML:<div data-v-16fdb080="" data-v-a964f0b4="" class="creator-tab"><span data-v-16fdb080="" class="title">上传图文</span><div data-v-16fdb080="" class="underline"></div></div>
            
            column_button_selector = "//span[@class='title'][1]"
            column_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, column_button_selector))
            )
            # 鼠标向右移动80像素，然后点击
            actions = ActionChains(self.driver)
            actions.move_to_element(column_button).perform()
            actions.move_by_offset(80, 0).click().perform()
            # print(f"找到按钮，文字内容为: {column_button.text}")
            # column_button.click()
            logger.info("点击了上传图文按钮")
        except Exception as e:
            logger.error(f"点击上传图文按钮出错: {str(e)}")
            return f"创建笔记失败: {str(e)}"
            # 等待页面加载完成，找到文件上传输入框
            # 使用提供的HTML代码中的class和type属性作为选择器
        try:
            file_input_selector = 'input[type="file"].upload-input'
            file_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, file_input_selector))
            )
            logger.info("找到文件上传输入框")

            # 将图片文件路径发送给输入框
            # Selenium会自动处理多个文件路径，用换行符分隔
            image_paths_string = "\n".join(image_urls) # image_urls 应该是本地文件路径列表
            # # TODO:For test
            # image_paths_string = "C:/Users/1c1/Desktop/公众号推文/创建公众号文章预览图.png"
            file_input.send_keys(image_paths_string)
            logger.info(f"已发送 {len(image_urls)} 个图片文件路径")

            # 填写标题和内容，并点击发布按钮
            # 标题HTML代码:<div class="d-input --color-text-title --color-bg-fill"><!----><input class="d-text" type="text" placeholder="填写标题会有更多赞哦～" value=""><!----><!----><!----></div>
            # 使用XPath定位标题输入框
            title_input_selector = "//input[@class='d-text' and @placeholder='填写标题会有更多赞哦～']"
            title_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, title_input_selector))
            )
            title_input.send_keys(title)
            logger.info(f"已输入标题: {title}")
            # 内容HTML代码:<div class="ql-editor ql-blank" contenteditable="true" aria-owns="quill-mention-list" data-placeholder="输入正文描述，真诚有价值的分享予人温暖"><p><br></p></div>
            content_input_selector = "div[contenteditable='true']"
            content_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, content_input_selector))
            )
            content_input.send_keys(content)
            logger.info(f"已输入内容: {content}")
            # 发布按钮HTML代码:<span class="d-text --color-static --color-current --size-text-paragraph d-text-nowrap d-text-ellipsis d-text-nowrap" style="text-underline-offset: auto;"><!---->发布<!----><!----><!----></span>
            # 发布button HTML代码：<button data-v-34b0c0bc="" data-v-30daec93="" data-v-0624972c-s="" type="button" class="d-button d-button-large --size-icon-large --size-text-h6 d-button-with-content --color-static bold --color-bg-fill --color-text-paragraph custom-button red publishBtn" data-impression="{&quot;noteTarget&quot;:{&quot;type&quot;:&quot;NoteTarget&quot;,&quot;value&quot;:{&quot;noteEditSource&quot;:1,&quot;noteType&quot;:1}},&quot;event&quot;:{&quot;type&quot;:&quot;Event&quot;,&quot;value&quot;:{&quot;targetType&quot;:{&quot;type&quot;:&quot;RichTargetType&quot;,&quot;value&quot;:&quot;note_compose_target&quot;},&quot;action&quot;:{&quot;type&quot;:&quot;NormalizedAction&quot;,&quot;value&quot;:&quot;impression&quot;},&quot;pointId&quot;:50979}},&quot;page&quot;:{&quot;type&quot;:&quot;Page&quot;,&quot;value&quot;:{&quot;pageInstance&quot;:{&quot;type&quot;:&quot;PageInstance&quot;,&quot;value&quot;:&quot;creator_service_platform&quot;}}}}"><div class="d-button-content"><!----><span class="d-text --color-static --color-current --size-text-paragraph d-text-nowrap d-text-ellipsis d-text-nowrap" style="text-underline-offset: auto;"><!---->发布<!----><!----><!----></span><!----></div></button>
            publish_button_selector = "// button[@data-v-34b0c0bc and @data-v-30daec93]"
            publish_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, publish_button_selector))
            )
            # 等待图片上传完毕
            time.sleep(3)
            publish_button.click()
            logger.info("点击了发布按钮")

            logger.info("笔记创建流程已执行图片上传步骤")
            return "成功发布到小红书上" # 或者根据实际情况返回发布结果

        except Exception as e:
            logger.error(f"创建笔记出错: {str(e)}")
            return f"发送小红书失败: {str(e)}"


    def login_with_verification_code(self, verification_code):
        """Automates the login process."""
        # Use a headless browser if you don't need to see the browser window
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')
        # options.add_argument("--disable-gpu")

        # options.add_argument('--no-sandbox')
        # options.add_argument('--disable-dev-shm-usage')
        
        self.driver = webdriver.Chrome(options=options) # Or use Firefox, Edge, etc.
        self.driver.maximize_window()
        self.driver.get("https://www.xiaohongshu.com/explore")

        # 尝试加载Cookie来快速登录，如果不成功，重新进行手机验证码登录流程
        if self.load_cookies():
            time.sleep(0.5)
            self.driver.get("https://www.xiaohongshu.com/explore")
            print("Attempted login with saved cookies.")
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "span[data-v-a93a7d02].channel"))
                )
                print("Successfully logged in with saved cookies.")
                # time.sleep(10)
                return "登录成功"
            except:
                # Continue with manual login steps if cookie login fails
                logger.info("Saved cookies did not result in login. Proceeding with manual login.")
                # return None
        else:
            logger.info(f"No saved cookies for {self.phone_number} found. Proceeding with manual login.")

        # 等待登录容器出现
        try:
            login_container_selector = ".login-container" # Updated selector based on provided HTML
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, login_container_selector))
            )
            logger.info("Login container found.")
        except:
            logger.info("Login container not found.")
            return "登录失败，小红书网页格式可能发生变化，需要重新实现工具，请联系维护人员"

        # 填入手机号
        try:
            # Wait for the phone number input field
            # Replace with the actual selector for the phone number input
            phone_input_selector = "input[placeholder='输入手机号']"
            phone_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, phone_input_selector))
            )
            phone_input.send_keys(self.phone_number)
            logger.info("Phone number input found.")
        except:
            logger.info("Phone number input not found.")
            return "登录失败，请检查手机号是否正确。如果手机号正确，请联系工具维护人员"

        # 点击同意协议
        icon_selector = "div[data-v-bd53e6d2].icon-wrapper"
        try:
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, icon_selector))
            ).click()
            logger.info("Icon element clicked.")
        except Exception as e:
            logger.info(f"Error clicking icon element: {e}")
            return "登录失败，小红书网页格式可能发生变化，需要重新实现工具，请联系维护人员"
        # 填入验证码
        try:
            code_input_selector = "input[placeholder='输入验证码']" # Example selector, might need adjustment
            code_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, code_input_selector))
            )
            code_input.send_keys(verification_code)
            logger.info("Verification code entered.")
        except:
            logger.info("Verification code input not found.")
            return "登录失败，请检查验证码是否正确"

        # 点击登录按钮
        try:
            login_button_selector = "button[data-v-53838a75].submit" # 根据实际HTML元素更新的选择器
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, login_button_selector))
            ).click()
            logger.info("Login button clicked.")
            # time.sleep(10)
        except:
            logger.info("Login button not found.")
            return "登录失败，小红书网页格式可能发生变化，需要重新实现工具，请联系维护人员"
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span[data-v-a93a7d02].channel"))
            )
            logger.info("Successfully logged in")
            logger.info('登录成功，保存cookies')
            # Save cookies after successful login
            self.save_cookies()
            #     time.sleep(10)
            return "登录成功" # Return driver if successful
        except Exception as e:
            print("Login failed")
            print(e.message)
            return "登录失败，请重新发送验证码"
    

    def login_without_verification_code(self):
        """Automates the login process."""
        # Use a headless browser if you don't need to see the browser window
        options = webdriver.ChromeOptions()
        
        # options.add_argument('--headless')
        # options.add_argument('--no-sandbox')
        # options.add_argument('--disable-dev-shm-usage')
        
        self.driver = webdriver.Chrome(options=options) # Or use Firefox, Edge, etc.
        self.driver.maximize_window()
        self.driver.get("https://www.xiaohongshu.com/explore")

        # 尝试加载Cookie来快速登录，如果不成功，重新进行手机验证码登录流程
        if self.load_cookies():
            # time.sleep(1)
            self.driver.get("https://www.xiaohongshu.com/explore")
            # You might need to check if login was successful based on page content
            # For now, assume if cookies loaded, it might be logged in
            logger.info("Attempted login with saved cookies.")
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "span[data-v-a93a7d02].channel"))
                )
                logger.info("Successfully logged in with saved cookies.")
                # time.sleep(10)
                return "登录成功"
            except:
                # Continue with manual login steps if cookie login fails
                logger.info("Saved cookies did not result in login. Proceeding with manual login.")
                # return None
        else:
            logger.info("No saved cookies found. Proceeding with manual login.")

        try:
            login_container_selector = ".login-container" # Updated selector based on provided HTML
            # 等待登录容器出现
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, login_container_selector))
            )
            print("Login container found.")
        except:
            logger.info("Login container not found.")
            self.driver.quit()
            return None
        try:
            # Wait for the phone number input field
            # Replace with the actual selector for the phone number input
            phone_input_selector = "input[placeholder='输入手机号']" # Example selector, might need adjustment
            phone_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, phone_input_selector))
            )
            phone_input.send_keys(self.phone_number)
            logger.info("Phone number input found.")
        except:
            logger.info("Phone number input not found.")
            self.driver.quit()
            return None

        try:
            # 点击发送验证码按钮
            send_code_button_selector = "span[data-v-53838a75].code-button" # 根据实际HTML元素更新的选择器
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, send_code_button_selector))
            ).click()

            logger.info(f"已成功向手机号{self.phone_number}发送验证码")
            return "验证码已发送到手机，请提醒用户输入验证码，验证码格式为6位数字"
        except Exception as e:
            logger.info(f"Error during verification code entry or login click: {e}")
            return None


if __name__ == "__main__":
    # Replace with the phone number you want to use
    your_phone_number = "19921987257"
    
    # IMPORTANT: You will need to manually enter the verification code in the browser window that opens.
    auth = AuthManager(your_phone_number)
    msg = auth.login_without_verification_code()
    
    msg = auth.create_note('测试标题', '测试内容', ['https://cbu01.alicdn.com/img/ibank/O1CN01QCQ07K1VMFqRtG66L_!!2210409292638-0-cib.jpg'])
    time.sleep(10)