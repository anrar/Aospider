import pymysql.cursors

class Mysql:
    def __init__(self, host='localhost', port=3306, user='root', password = 'password'   \
        ,db = 'db', charset = 'utf8mb4', cursorclass=pymysql.cursors.DictCursor):
        """
        Mysql Helper
        """
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._db = db
        self._charset = charset
        self._cursorclass = cursorclass
        self.connection = pymysql.connect(host=self._host, port=self._port, user=self._user, password=self._password\
            ,db=self._db, charset=self._charset,  cursorclass=self._cursorclass)
        return

    def fetchall(self, sql, args):
        result = None
        try:
            if not self.connection.open:
                self.connection = pymysql.connect(host=self._host, port=self._port, user=self._user, password=self._password\
            ,db=self._db, charset=self._charset,  cursorclass=self._cursorclass)
            with self.connection.cursor() as cursor:
                # Read a single record
                cursor.execute(sql, args)
                result = cursor.fetchall()
        #except Exception as excep:
        #    result = None
        #    logging.debug("%s repeat: %s, keys=%s, repeat=%s, url=%s", self.__class__.__name__, excep, keys, repeat, url)
        finally:
            self.connection.close()
        return result

    def excute(self,sql,args):
        result = None
        try:
            if not self.connection.open:
                self.connection = pymysql.connect(host=self._host, port=self._port, user=self._user, password=self._password\
            ,db=self._db, charset=self._charset,  cursorclass=self._cursorclass)
            with self.connection.cursor() as cursor:
                result = cursor.execute(sql, args)
            self.connection.commit()
        except:
            self.connection.rollback()
        finally:
            self.connection.close()
        return result
