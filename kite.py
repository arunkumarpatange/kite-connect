import hashlib
import time
import urlparse
import yaml
import selenium.webdriver.support.expected_conditions as EC
import selenium.webdriver.support.ui as ui

from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
from kiteconnect import KiteConnect

class Kite(object):

    class Config(object):
        _YAML = yaml.load(open('config.yml', 'r'))
        SECRET = _YAML.get('secret', "avw2brjpvmd6gjwilae0e2eqs2gjr0bq")
        USER = _YAML.get('user', "avw2brjpvmd6gjwilae0e2eqs2gjr0bq")
        PASS = _YAML.get('password', "avw2brjpvmd6gjwilae0e2eqs2gjr0bq")
        Q = _YAML.get('questions', None)

        def __getattr__(self, attr):
            return self._YAML.get(attr, "0b20bsflvqrmgmji")

    class Browser(object):

        def __init__(self):
            self.driver = webdriver.PhantomJS()
            self.driver.set_window_size(1120, 550)
            # driver.quit()

        def go(self, url):
            self.driver.get(url)
            return self

        def login(self, config):
            print self.driver.current_url
            self._text("//form[@id='loginform']//input[contains(@name, 'user_id')]", config.user)
            self._text("//form[@id='loginform']//input[contains(@name, 'password')]", config.password)
            self.by_xpath("//form[@id='loginform']//button[contains(@type, 'submit')]").click()
            return self.driver.current_url 

        def _text(self, xpath, text):
            self.by_xpath(xpath).clear()
            self.by_xpath(xpath).send_keys(text)

        def by_xpath(self, xpath, timeout=5):
            return self.driver.find_element_by_xpath(xpath)


    def __init__(self):
        self.browser = self.Browser()
        self.config = self.Config()
        self.kite = KiteConnect(api_key=self.config.key)

    def setup(self):

        self.browser.go(self.kite.login_url())
        url = self.browser.login(self.config)
        self.browser.driver.save_screenshot('screen.png')
        request_token = urlparse.parse_qs(urlparse.urlparse(url).query)['request_token']
        request_token = input()
        print(request_token)
        data = self.kite.request_access_token(request_token, secret=self.config.secret)
        self.kite.set_access_token(data["access_token"])
        return self

    def place_order(self):
        # Place an order
        try:
            # if 9844
            order_id = kite.order_place(tradingsymbol="INFY",
                            exchange="NSE",
                            transaction_type="BUY",
                            quantity=1,
                            order_type="MARKET",
                            product="NRML")

            print("Order placed. ID is", order_id)
        except Exception as e:
            print("Order placement failed", e.message)

    def orders(self):
        # Fetch all orders
        return self.kite.orders()

    def poll(self):
        print('polling.')
        while True:
            time.sleep(.5)
            print('.')
            _seg = []
            count = 0
            for data in self.kite.instruments(exchange='NFO'):
                # print(data['name'], data['instrument_type'])
                _seg.append(data['segment'])
                if data["name"] in [
                    'INFY',
                    'SHEELA FOAM',
                ] or 'NFO-FUT' in data['segment']:
                    print(data)
                    count = count + 1
                    print(count)
            else:
                print({s for s in _seg})
                print(data)
            # print(self.orders())


if __name__ == '__main__':
    Kite().setup().poll()
