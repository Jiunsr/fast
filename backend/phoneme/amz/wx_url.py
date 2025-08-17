from seleniumwire import webdriver  # 注意是 seleniumwire
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--remote-debugging-port=9222")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.40"
)
chrome_options.add_experimental_option("prefs", {
    "profile.managed_default_content_settings.images": 2,
    "profile.managed_default_content_settings.stylesheets": 2,
    "profile.managed_default_content_settings.fonts": 2
})

service = Service("/usr/local/bin/chromedriver")
global_driver = webdriver.Chrome(service=service, options=chrome_options)


class WeixinLinkFetcher:
    # def __init__(self, chromedriver_path="/usr/local/bin/chromedriver"):
        # service = Service(chromedriver_path)
        # 提前启动浏览器，提升后续调用性能
        # global_driver = webdriver.Chrome(service=service, options=chrome_options)

    def get_weixin_link(self, url, timeout=10):
        """传入公众号 H5 页面链接，返回跳转到微信的真实链接"""
        print('当前页面数量:', len(global_driver.window_handles))

        if len(global_driver.window_handles) > 1:
            # 假设第一个 window 是主窗口
            global_driver.switch_to.window(global_driver.window_handles[1])
            global_driver.close()
            # 切回主窗口
            global_driver.switch_to.window(global_driver.window_handles[0])

        global_driver.execute_script("window.open('');")
        global_driver.switch_to.window(global_driver.window_handles[-1])
        global_driver.get(url)

        try:
            # 等待第一个按钮出现
            button = WebDriverWait(global_driver, 5).until(
                EC.element_to_be_clickable((By.ID, "profileBt"))
            )
            button.click()

            # 等待“前往”按钮出现并点击
            go_button = WebDriverWait(global_driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Proceed')]"))
            )
            go_button.click()

            request = global_driver.wait_for_request("jumptoweixin", timeout=timeout)
            if request.response:
                body = request.response.body.decode('utf-8')
                data = json.loads(body)
                return data.get("url")

        except Exception as e:
            print("操作失败:", e)

        return None

    def quit(self):
        """关闭浏览器"""
        global_driver.quit()

    def close(self):
        """关闭标签页"""
        global_driver.close()


# ===== 使用示例 =====
if __name__ == "__main__":
    fetcher = WeixinLinkFetcher()
    link = fetcher.get_weixin_link("https://mp.weixin.qq.com/s/xXf3zL5FI3s5LOT2Fk7Uqw")
    if link:
        print("获取到的链接：", link)
    else:
        print("未捕获到链接")
    fetcher.quit()
