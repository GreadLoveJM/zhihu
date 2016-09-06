# -*- coding:utf-8 -*-
import sys
import MySQLdb
import ConfigParser
import logging
reload(sys)
sys.setdefaultencoding('utf-8')

class GetConnect(object):
    def __init__(self):
        conf = ConfigParser.ConfigParser()
        conf.read('zhihu_config.ini')
        self.host = conf.get('dbconf','host')
        self.user = conf.get('dbconf','user')
        self.passwd = conf.get('dbconf','password')
        self.port = int(conf.get('dbconf','port'))
        self.db =conf.get('dbconf','db')
        self.charset = conf.get('dbconf','charset')
        self.use_unicode = True
        self.conn = None
        self.cur = None
        self.initDb()

    def initDb(self):
        try:
            self.conn = MySQLdb.connect(host=self.host, port=self.port, user=self.user,
                                        passwd=self.passwd, db=self.db, charset=self.charset, use_unicode=self.use_unicode)
            self.cursor = self.conn.cursor()
        except MySQLdb.Error, e:
            logging.warning( 'Mysql Error %d: %s' % (e.args[0], e.args[1]))
            sys.exit(-1)


    def getCount(self, sql):
        count = self.cursor.execute(sql)
        return count

    def getData(self, sql):
        count = self.cursor.execute(sql)
        print 'There has %d rows record' % count
        if count != 0:
            results = self.cursor.fetchall()
            return results
        else:
            return None

    def insertInto_discribe_zhihu(self,obj):

		self.cursor.execute('replace  into discribe_zhihu VALUES (%s,%s,%s,%s,%s,%s)',obj)
		self.conn.commit()

    def executeDB(self, sql):
        self.cursor.execute(sql)
        self.conn.commit()
        print 'Success execute sql'

    def closeResource(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

def main():
    pass
if __name__ == '__main__':
    main()
