from pyvirtualdisplay import Display
from selenium import webdriver


class LoginSpider:
    def __init__(self):
        self.url = 'https://courses.edx.org/login'
        self.driver = webdriver.Chrome()
        # driver.set_window_size(1120, 550)

    def sign_in(self):
        """
        Authorization
        """
        username = 'mohmmadhd@gmail.com'
        password = 'tempupwork'

        email = self.driver.find_element_by_id('login-email')
        email.send_keys(username)
        pwd = self.driver.find_element_by_id('login-password')
        pwd.send_keys(password)
        self.driver.find_element_by_class_name('login-button').click()

    def get_body(self):
        return self.driver.page_source

    def __del__(self):
        pass
        self.driver.delete_all_cookies()
        self.driver.close()
