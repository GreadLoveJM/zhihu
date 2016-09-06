# coding=utf-8
import requests
import ConfigParser
import scrapy
import re
import datetime
import logging
from retrying import retry
from multiprocessing.pool import ThreadPool
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

def remove_space(s):
    spa = re.compile('\s+')
    con = re.sub(spa, "", s)
    return con

def read_config():
    conf = ConfigParser.ConfigParser()
    conf.read('zhihu_config.ini')
    cookie = conf.get('webconf', 'Cookie')
    cook = {'Cookie': cookie}
    agent = conf.get('webconf', 'User-Agent')
    headers = {'User-Agent': agent}
    return {'cookie': cook, 'headers': headers}

def request_session(url):
    webconf = read_config()
    html = requests.get(url, timeout=10, cookies=webconf['cookie'], headers=webconf['headers']).text
    return html

def normolize_time(pre_time):

    '''this function is used to normolize time and return'''

    def match_partten(raw,parttenlst):
        for partten,convert in parttenlst:
            match_obj=re.match(partten,raw)
            if match_obj:
                return convert(match_obj)
        raise myexception('can\'t normolize time')
    partten_convert_pairs=[
        (u'昨天',
            lambda m:datetime.date.today()-datetime.timedelta(days=1)),
        (u'(\d+)-(\d+)-(\d+)',
            lambda  m:datetime.date(int(m.group(1)),int(m.group(2)),int(m.group(3))))
    ]
    return match_partten(pre_time,partten_convert_pairs)

class myexception(Exception):
    def __init__(self, info):
        logging.warning(info)

class Zhihu_spider(object):
    def __init__(self):
        self.pool = ThreadPool(20)
    def _get_ques_name(self,ques_id):
        url = "http://www.zhihu.com/question/{}?sort=created".format(ques_id)
        html = request_session(url)
        title=scrapy.Selector(text=html).xpath('.//span[@class="zm-editable-content"]/text()').extract_first()
        self.title= title

    def _get_max_page(self, ques_id):

        ''' this method is used to get answers count of self.answers
        and return max pages '''

        url = "http://www.zhihu.com/question/{}?sort=created".format(ques_id)
        html = request_session(url)

        _sele = scrapy.Selector(text=html)
        answers_count = _sele.xpath('.//*[@id="zh-question-answer-num"]/@data-num').extract_first()
        self.answers_count = answers_count
        logging.warning('the number of all the answers is {} of {}'.format(answers_count,ques_id))

        _page_lst = _sele.xpath('.//div[@class="zm-invite-pager"]/span')
        if _page_lst:
            page = 0
            for each in _page_lst:
                item = each.xpath('string(.)').extract_first()
                try:
                    if int(page) < int(item):
                        page = item
                except:
                    pass
        else:
            page = 1

        return page

    def _extract_comment_item(self, selector):

        '''this func is used to extract infomation of each answer and return'''

        answer_id = selector.xpath('./@data-aid').extract_first()
        _votebar = selector.xpath('.//*[@class="zm-votebar"]')
        if _votebar:
            agree = _votebar.xpath('.//button[@class="up "]/span[@class="count"]/text()').extract_first()
        else:
            agree = 0

        _con = selector.xpath('.//div[@class="zm-editable-content clearfix"]')
        if _con:
            content = _con[0].xpath('string(.)').extract_first()
        else:
            content = ""

        _date=selector.xpath('.//a[@class="answer-date-link meta-item"]/text()').extract_first()
        pre_time=_date.split(" ")[1]
        pubtime=normolize_time(pre_time)
        return {'title':self.title,'answer_id': answer_id, 'agree': agree, 'content': remove_space(content),'pubtime':pubtime}

    @retry(stop_max_attempt_number=3)
    def _extract_one_page(self, page, chick=True, chick_num=None):

        url = "http://www.zhihu.com/question/{}?sort=created&page={}".format(self.ques_id, page)
        html = request_session(url)
        answer_wrap = scrapy.Selector(text=html).xpath('.//div[@id="zh-question-answer-wrap"]/div[@tabindex="-1"]')
        comments=self.pool.map(self._extract_comment_item,answer_wrap)
        if chick == True:
            if len(comments) == 20:
                return comments
            else:
                raise myexception('page {} has not reach 20 | retrying...')
        else:
            if len(comments) >= chick_num:
                return comments
            else:
                raise myexception('the last page has not reach experience | retrying...')

    # @retry(stop_max_attempt_number=3)
    # def start_crwal(self, ques_id):
    #     self.ques_id = ques_id
    #     max_page = self._get_max_page(self.ques_id)
    #     comments = self.pool.map(self._extract_one_page, range(1, int(max_page) + 1))
    #     truth_count = 0
    #     for comment in comments:
    #         truth_count += len(comment['comments'])
    #     logging.warning('the truth comments is {} and the exesprice is {}'.format(truth_count, self.answers_count))
    #     if truth_count == int(self.answers_count):
    #         return comments
    #     else:
    #         logging.warning('the truth comments is {} and the exesprice is {} | retry........'.format(truth_count,
    #                                                                                                   self.answers_count))
    #         raise myexception

    def start_crwal_debug(self, ques_id):
        self.ques_id = ques_id
        self._get_ques_name(ques_id)
        max_page = self._get_max_page(self.ques_id)
        for each in range(1, int(max_page) + 1):
            if each == int(max_page):
                comments = self._extract_one_page(each, chick=False,
                                                  chick_num=int(self.answers_count) - 20 * (int(max_page) - 1))
            else:
                comments = self._extract_one_page(each)
            for comment in comments:
                yield comment
        logging.warning('all is done')

if __name__ == '__main__':
    pass

