import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from twocaptcha import TwoCaptcha
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from tempfile import TemporaryDirectory

PROXY = "proxy url"
options = Options()
webdriver.DesiredCapabilities.CHROME["proxy"] = {
    "httpProxy": PROXY,
    "httpsProxy": PROXY,
    "proxyType": "MANUAL",
}
# options.add_argument("start-maximized")
# options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--kiosk-printing")
options.add_argument("--disable-notifications")
options.add_argument("--disable-popup-blocking")
options.add_argument("--no-sandbox")
options.add_argument("--disable-extensions")
options.add_argument("disable-infobars")
options.add_experimental_option("excludeSwitches", ["enable-logging"])

driver = webdriver.Chrome(r"chromedriver\chromedriver.exe", options=options)

"""-----------recaptcha test URL's-------------
recaptcha v2 - https://recaptcha-demo.appspot.com/recaptcha-v2-checkbox.php
image captcha(normal) - https://captcha.com/demos/features/captcha-demo.aspx 
hCaptcha - https://accounts.hcaptcha.com/demo
hcaptcha - https://democaptcha.com/demo-form-eng/hcaptcha.html
turnstile - https://2captcha.com/demo/cloudflare-turnstile

"""
url = "https://captcha.com/demos/features/captcha-demo.aspx"
driver.get(url)

step = {
    # recaptcha v2
    "key_xpath": "/html/body/main/form/fieldset/div[@class='g-recaptcha form-field']",
    "checkbox_xpath": "/html/body/main/form/fieldset/div[@class='g-recaptcha form-field']/div/div/iframe",
    "submit_xpath": "/html/body/main/form/fieldset/button",
    # normal captcha
    "image_xpath": "/html/body/div[1]/div[1]/div[1]/form/fieldset[1]/div[1]/div/div[1]/img",
    "validate_xpath": "/html/body/div[1]/div[1]/div[1]/form/fieldset[1]/div[2]/input[2]",
    "text_xpath": "/html/body/div[1]/div[1]/div[1]/form/fieldset[1]/div[2]/input[1]",
    # hCaptcha
    "sitekey_xpath": "/html/body/main/article/div/form/div",
    "iframe_xpath": "/html/body/main/article/div/form/div/iframe",
    # //*[@id="hcaptcha-demo"]/iframe
    "hcheckbox_xpath": "/html/body/div/div[1]/div[1]/div/div/div[1]",
    "hsubmit_xpath": "/html/body/main/article/div/form/input[2]",
    # cloudflare-turnstile
    "CFT_sitekey_xpath": "/html/body/div[1]/div/main/div/section/form/div/div",
    "CFT_checkbox_xpath": "/html/body/table/tbody/tr/td/div/div[1]/table/tbody/tr/td[1]/div[6]/label/input",
    "CFT_submit_xpath": "/html/body/div[1]/div/main/div/section/form/button[1]",
}

""" -------------type inputted from UI------------------
# Check the class of the captcha element to determine the type of captcha
captcha_element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div[class*='captcha']")))
captcha_class = captcha_element.get_attribute("class")
if "g-recaptcha" in captcha_class:
    type = "reCaptcha"
elif "h-captcha" in captcha_class:
    type = "hCaptcha"
elif "turnstile" in captcha_class:
    type = "turnstile"
else:
    type = "normal"
    """

type = "normal"

API_KEY = ""  # personal test account api key

solver = TwoCaptcha(API_KEY)


def solve_captcha(driver, type, step):
    # proxy setup for 2captcha API
    proxy = {
        "type": "HTTPS",
        "uri": "proxy url",
    }
    if type == "normal":
        # saving the captcha image
        with TemporaryDirectory() as tempdir:
            with open(f"{tempdir}\captcha.png", "wb") as file:
                img = driver.find_element(By.XPATH, step["image_xpath"])
                file.write(img.screenshot_as_png)
            print("Solving captcha...")
            result = solver.normal(f"{tempdir}\captcha.png", proxy=proxy)

            driver.find_element(By.XPATH, step["text_xpath"]).send_keys(result["text"])
            # Click Submit
            validate_button = driver.find_element(By.XPATH, step["validate_xpath"])
            validate_button.click()

    elif type == "reCaptcha":
        # acquire sitekey from webpage
        element = driver.find_element(By.XPATH, step["key_xpath"])
        sitekey = element.get_attribute("data-sitekey")
        result = solver.recaptcha(
            sitekey=sitekey, url=driver.current_url
        )  # , proxy=proxy)

        # Click on Check button
        check_button = driver.find_element(By.XPATH, step["checkbox_xpath"])
        check_button.click()

        # replace value text with solution in webpage
        driver.execute_script(
            "document.getElementById('g-recaptcha-response').value='%s'"
            % result["text"]
        )

        # Click Submit
        submit_button = driver.find_element(By.XPATH, step["submit_xpath"])
        submit_button.click()

    elif type == "hCaptcha":
        element = driver.find_element(By.XPATH, step["sitekey_xpath"])
        sitekey = element.get_attribute("data-sitekey")
        result = solver.hcaptcha(sitekey=sitekey, url=driver.current_url)

        try:
            element = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, step["iframe_xpath"]))
            )
            driver.execute_script(
                "document.querySelector('iframe').setAttribute('data-hcaptcha-response', '%s');"
                % result["text"]
            )
        except:
            print("iframe not found")

        # Click Submit
        submit_button = driver.find_element(By.XPATH, step["hsubmit_xpath"])
        submit_button.click()

    elif type == "turnstile":
        # acquire sitekey from webpage
        element = driver.find_element(By.XPATH, step["CFT_sitekey_xpath"])
        sitekey = element.get_attribute("data-sitekey")
        result = solver.turnstile(
            sitekey=sitekey, url=driver.current_url
        )  # , proxy=proxy)
        # Click on Check button
        check_button = driver.find_element(By.XPATH, step["CFT_checkbox_xpath"])
        check_button.click()

        # replace value text with solution in webpage
        driver.execute_script(
            "document.getElementById('cf-turnstile-response').value='%s'"
            % result["text"]
        )

        # Click Submit
        submit_button = driver.find_element(By.XPATH, step["CFT_submit_xpath"])
        submit_button.click()


solve_captcha(driver, type, step)
