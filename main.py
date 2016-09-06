import spider_zhihu
from writers.mysql_writer import GetConnect
from multiprocessing.pool import ThreadPool
import re
def start_crawl(ques_id):
    db = GetConnect()
    p = spider_zhihu.Zhihu_spider()
    coms = p.start_crwal_debug(ques_id)
    for each in coms:
        s = (ques_id, each['title'], each['answer_id'], each['pubtime'], each['agree'], each['content'])
        db.insertInto_discribe_zhihu(s)

if __name__ == '__main__':
    pool=ThreadPool(5)
    lst=[]
    with open('temp','r') as f:
        for lines in f.readlines():
            lst.append(re.sub('\s+','',lines))

    pool.map(start_crawl,lst)
