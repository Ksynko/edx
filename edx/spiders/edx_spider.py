# -*- coding: utf-8 -*-
import os

import scrapy
from scrapy import FormRequest, Request
import selenium.webdriver.support.expected_conditions as EC
from selenium import webdriver

from edx.items import EdxItem
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
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
        self.start_urls = [self.login_url]
        if not os.path.exists(self.BASE_DIR):
            os.makedirs(self.BASE_DIR)
        super(EdxSpider, self).__init__(*args, **kwargs)

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
        self.driver.close()

        return cookies

    def is_visible(self, driver, locator, timeout=2):
        try:
            ui.WebDriverWait(driver, timeout).until(EC.visibility_of_any_elements_located((By.XPATH, locator)))
            return True
        except TimeoutException:
            return False

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
                callback=self.parse_course)
        else:
            print("Please input course url in parameters")

    def parse_course(self, response):
        lessons_path = response.xpath('//ol/li/ol/li/a')[0]
        lections_url = lessons_path.xpath('./@href').extract()[0]
        yield Request(url=lections_url, callback=self.parse_lesson)

    def parse_lesson(self, response):
        folder = response.xpath('//span[@class="nav-item nav-item-section"]/a/text()').extract()[0]

        driver = webdriver.PhantomJS()
        url = 'https://courses.edx.org/login'
        driver.get(url)
        wait = ui.WebDriverWait(driver, 60)

        email = driver.find_element_by_id('login-email')
        email.send_keys(self.username)
        pwd = driver.find_element_by_id('login-password')
        pwd.send_keys(self.password)
        driver.find_element_by_class_name('login-button').click()
        wait.until(lambda driver: driver.title.lower().startswith('dashboard'))
        driver.get(response.url)

        problem_tabs = driver.find_elements_by_xpath('//button[contains(@class, "seq_problem")]')
        for tab in problem_tabs:
            item = EdxItem()
            tab.click()

            block_ids = []
            show_answer_buttons = driver.find_elements_by_xpath('//div[@id="seq_content"]//button[contains(@class, "show problem-action-btn")]')

            for button in show_answer_buttons:
                block_ids.append(button.get_attribute("aria-describedby").split('-')[0])
                button.click()

            is_all_visible = True
            for block_id in block_ids:
                xpath_correct_status = '//div[@id="seq_content"]//div[contains(@id, "{0}")]//' \
                                       '*[contains(@class, "correct") ' \
                                       'or (contains(@id, "answer_{0}") ' \
                                       'and string-length(text()) > 0)]'.format(block_id)

                if not self.is_visible(driver, xpath_correct_status, 60):
                    is_all_visible = False

            if is_all_visible:
                item['title'] = driver.find_element_by_xpath('//div[@id="seq_content"]//'
                                                             'h2[contains(@class, "unit-title")]').text
                item['url'] = response.url
                item['folder'] = folder

                page_source = driver.page_source
                excluded_script = 'lms-modules'
                item['html'] = page_source.encode('utf-8').replace(excluded_script, '')

            else:
                print("NOT ALL ANSWERS HERE!")

            yield item
        driver.close()

        next_url = response.xpath('//div[@data-next-url]/@data-next-url').extract()[0]
        yield Request(url=self.BASE_URL + next_url, callback=self.parse_lesson)
