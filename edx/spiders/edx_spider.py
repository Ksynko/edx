# -*- coding: utf-8 -*-
import os
import scrapy
from scrapy import FormRequest, Request, Selector
from scrapy.utils.response import open_in_browser
from selenium import webdriver

from edx.items import EdxItem
from selenium.webdriver.support import ui


class EdxSpider(scrapy.Spider):
    name = 'edx_spider'
    allowed_domains = ["courses.edx.org", "edx.org"]
    BASE_URL = 'https://courses.edx.org'
    BASE_DIR = "courses"
    login_url = 'https://courses.edx.org/login'
    home_page = "https://courses.edx.org/dashboard"
    username = 'mohmmadhd@gmail.com'
    password = 'tempupwork'

    HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36"
                             " (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
               "X-CSRFToken": '',
               "X-Requested-With": 'XMLHttpRequest'}

    def __init__(self, course_url=None, *args, **kwargs):
        self.course_url = course_url
        # self.start_urls = [course_url]
        self.start_urls = [self.login_url]
        if not os.path.exists(self.BASE_DIR):
            os.makedirs(self.BASE_DIR)
        super(EdxSpider, self).__init__(*args, **kwargs)

    # def save_cookies(self, driver, file_path):
    #     LINE = "document.cookie = '{name}={value}; path={path}; domain={domain}; expires={expires}';\n"
    #     with open(file_path, 'w') as file:
    #         for cookie in driver.get_cookies():
    #             print(cookie)
    #             print(LINE.format(**cookie).encode('utf-8'))
    #             file.write(LINE.format(**cookie).encode('utf-8'))
    #
    # def load_cookies(self, driver, file_path):
    #     with open(file_path, 'r') as file:
    #         driver.execute_script(file.read())

    def get_cookies(self):
        url = 'https://courses.edx.org/login'
        self.driver = webdriver.PhantomJS()
        self.driver.get(url)

        email = self.driver.find_element_by_id('login-email')
        email.send_keys(self.username)
        pwd = self.driver.find_element_by_id('login-password')
        pwd.send_keys(self.password)
        self.driver.find_element_by_class_name('login-button').click()

        cookies = self.driver.get_cookies()
        # self.save_cookies(self.driver, "cookies.js")
        self.driver.close()

        return cookies

    def parse(self, response):
        self.cookies = self.get_cookies()

        for cookie in self.cookies:
            if cookie['name'] == 'csrftoken':
                self.HEADERS['X-CSRFToken'] = cookie['value']

        yield Request(
            url=self.login_url,
            cookies=self.cookies,
            callback=self.login)

    def login(self, response):
        return FormRequest(url="https://courses.edx.org/user_api/v1/account/login_session/",
                           formdata={'email': self.username, 'password': self.password, 'remember': 'true'},
                           callback=self.parse_home_page,
                           headers=self.HEADERS)

    def parse_home_page(self, response):
        if self.course_url:
            yield Request(
                url=self.course_url,
                # cookies=self.cookie,
                callback=self.parse_course)
        else:
            print("Please input course url in parameters")

    def parse_course(self, response):
        lessons_paths = response.xpath('//ol/li/ol/li/a')
        for path in lessons_paths[2:3]:
            lections_url = path.xpath('./@href').extract()[0]
            yield Request(url=lections_url, callback=self.parse_lesson)

    def parse_lesson(self, response):
        item = EdxItem()
        folder = response.xpath('//span[@class="nav-item nav-item-section"]/a/text()').extract()[0]
        item['url'] = response.url
        item['folder'] = folder
        item['title'] = response.xpath('//span[@class="nav-item nav-item-sequence"]/text()').extract()[0]

        if "Show Answer" in response.body:
            driver = webdriver.PhantomJS()
            # url = 'https://courses.edx.org/login'
            # driver.get(url)
            # wait = ui.WebDriverWait(driver, 60)
            #
            # email = driver.find_element_by_id('login-email')
            # email.send_keys(self.username)
            # pwd = driver.find_element_by_id('login-password')
            # pwd.send_keys(self.password)
            # driver.find_element_by_class_name('login-button').click()
            # wait.until(lambda driver: driver.title.lower().startswith('dashboard'))
            # self.load_cookies(driver, "cookies.js")

            driver.get(response.url)
            for cookie in self.cookies:
                driver.add_cookie(cookie)
            driver.get(response.url)
            # wait.until(lambda driver: driver.find_elements_by_xpath('//div[@class="action"]//button/span[text()="Show Answer"]'))

            show_answer_buttons = driver.find_elements_by_xpath('//div[@class="action"]//button/span[text()="Show Answer"]')

            for button in show_answer_buttons:
                button.click()

            # wait.until(
            #         lambda driver: driver.find_elements_by_xpath('//span[@class="status correct"]'))
            page_source = driver.page_source

            excluded_script = '<script type="text/javascript" src="https://prod-edxapp.edx-cdn.org/static/edx.org/js/lms-modules.3d780e23e1a0.js" charset="utf-8"></script>'
            item['html'] = page_source.encode('utf-8').replace(excluded_script, '')

            driver.close()
        else:
            item['html'] = response.body

        yield item

        next_url = response.xpath('//div[@data-next-url]/@data-next-url').extract()[0]
        # yield Request(url=self.BASE_URL + next_url, callback=self.parse_lesson)
