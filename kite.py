import sys
import os
import hashlib
import time
import urlparse
import yaml
import csv
import selenium.webdriver.support.expected_conditions as EC
import selenium.webdriver.support.ui as ui

from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
from kiteconnect import KiteConnect
from kiteconnect.exceptions import DataException, NetworkException

# TODO:
# ADD logger
# Handle exceptions graciously
# call instrument list once a day
# go dormaant after placing order

print_ = lambda d, cr='\n': sys.stdout.write("{}{}".format(d, cr or ''))

class QObject(object):
    '''
        Quick Object Dict
    '''

    def __init__(self, data):
        self.data = data

    def __getattr__(self, attr):
        return self.data.get(attr, None)

class Kite(object):

    class Config(QObject):

        def __init__(self):
            super(self.__class__, self).__init__(self._yaml())

        def _yaml(self):
            with open('config.yml', 'r') as config:
                return yaml.load(config)

        def has_changed(self):
            for k, v in self._yaml().iteritems():
                if getattr(self, k) != v:
                    return True
            return False


    class Browser(object):

        xpath_user = "//form[@id='loginform']//input[contains(@name, 'user_id')]"
        xpath_password = "//form[@id='loginform']//input[contains(@name, 'password')]"
        xpath_question1 = '//form[@id="twofaform"]//span[contains(@class, "first")][contains(text(), "{}")]'
        xpath_question2 = '//form[@id="twofaform"]//span[contains(@class, "second")][contains(text(), "{}")]'
        xpath_answer1 = "//form[@id='twofaform']//input[contains(@name, 'answer1')]"
        xpath_answer2 = "//form[@id='twofaform']//input[contains(@name, 'answer2')]"
        xpath_qa_ok = "//form[@id='twofaform']//button[contains(@type, 'submit')]"
        xpath_submit = "//form[@id='loginform']//button[contains(@type, 'submit')]"



        def __init__(self):
            self.driver = webdriver.PhantomJS()
            self.driver.set_window_size(1120, 550)

        def go(self, url):
            print_(url)
            self.driver.get(url)
            return self

        def login(self, config):
            self._text(self.xpath_user, config.user)
            self._text(self.xpath_password, config.password)
            self.by_xpath(self.xpath_submit).click()
            self.set_answers(config)
            return self.driver.current_url

        def set_answers(self, config):
            for _xpath, _xpath_answer in ((self.xpath_question1, self.xpath_answer1), (self.xpath_question2, self.xpath_answer2)):
                for qa in config.questions:
                    for q, answer in qa.iteritems():
                        try:
                            self.by_xpath(_xpath.format(q))
                            self._text(_xpath_answer, answer)
                        except Exception as e:
                            continue
            self.by_xpath(self.xpath_qa_ok).click()

        def _text(self, xpath, text):
            self.by_xpath(xpath).clear()
            self.by_xpath(xpath).send_keys(text)

        def by_xpath(self, xpath, timeout=5):
            return self.driver.find_element_by_xpath(xpath)

        def exit(self):
            self.driver.quit();
            return self

    STATE = [
        0, # order place
        1, # delay network gateway down
        2, # something else
    ]

    def __init__(self):
        self.browser_config()
        self.kite = KiteConnect(api_key=self.config.key)
        self.orders_placed = {}

    def browser_config(self):
        self.browser = self.Browser()
        self.config = self.Config()
        return self

    def setup(self):
        self.browser.go(self.kite.login_url())
        url = self.browser.login(self.config)
        self.browser.driver.save_screenshot('screen.png')
        request_token = urlparse.parse_qs(urlparse.urlparse(url).query)['request_token'][0]

        data = self.kite.request_access_token(request_token, secret=self.config.secret)
        self.kite.set_access_token(data["access_token"])
        return self

    def place_order(self, row, data):
        if (
            (float(data.last_price) >= float(row.price) and row.transaction_type == 'BUY') or
            float(data.last_price) <= float(row.price) and row.transaction_type == 'SELL'
        ):
            try:
                order_id = self.kite.order_place(tradingsymbol=row.trading_symbol,
                                exchange=self.config.exchange,
                                transaction_type=row.transaction_type,
                                quantity=int(row.quantity),
                                order_type="LIMIT",
                                product="BO",
                                price=float(row.price),
                                squareoff_value=float(row.squareoff_value),
                                stoploss_value=float(row.stoploss_value),
                                trailing_stoploss=int(row.trailing_stoploss),
                                tag='AUTO')
                print_("Order placed. ID is", order_id)
                return self.STATE[0]
            except NetworkException as ne:
                print_("Gateway exception: ", ne.message)
                return self.STATE[1]
            except Exception as e:
                print_(e)
                print_(data.data)
                print_("Order failed", e.message)
        return self.STATE[2]

    def orders(self):
        # Fetch all orders
        return self.kite.orders()

    def poll(self):
        print_('polling... ')
        while True:
            time.sleep(.5)
            if self.config.has_changed():
                print_('re-config session')
                self.browser.exit()
                self.browser_config().setup()
            else:
                print_('.', cr=None)
                print
                with open('trade.csv') as symbols:
                    for row in (QObject(row) for row in csv.DictReader(symbols)):
                        try:
                            if not self.orders_placed.get(row.trading_symbol, False):
                                data = self.kite.quote(exchange=self.config.exchange, tradingsymbol=row.trading_symbol)
                                self.orders_placed[row.trading_symbol] = self.place_order(row, QObject(data)) == self.STATE[0]
                        except DataException as de:
                            print_(de)



if __name__ == '__main__':
    Kite().setup().poll()
