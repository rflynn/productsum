# ex: set ts=4 et:

import psycopg2


dbhost = 'productmap.ccon1imhl6ui.us-east-1.rds.amazonaws.com'
dbname = 'productmap'
dbuser = 'root'
dbpass = 'SyPi6q1gp961'

# PGPASSWORD=SyPi6q1gp961 psql -h productmap.ccon1imhl6ui.us-east-1.rds.amazonaws.com -U root productmap

# ref: http://initd.org/psycopg/docs/usage.html#unicode-handling
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
#psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)


_Conn = None
def get_psql_conn():
    global _Conn
    if not _Conn:
        _Conn = psycopg2.connect("host='%s' user='%s' password='%s' dbname='%s'" % (
            (dbhost, dbuser, dbpass, dbname)))
        _Conn.set_client_encoding('utf8')
        print _Conn
    return _Conn

