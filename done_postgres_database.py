import psycopg2
from psycopg2.extensions import AsIs
def create_conn():

    conn = psycopg2.connect(database = 'xiuchebot',
                    user = 'xiuchebot_user',
                    password = '46FRMRJb74h1Zdu1G4BVxs785Bb2JzG2',
                    host = 'dpg-cjg1v841ja0c73f7epqg-a.ohio-postgres.render.com',
                    port = '5432')

    return conn

def get_trade_list_from_sqlite(user_id,status):
    try:
        conn = create_conn()
        c = conn.cursor()
        c.execute("SELECT * from trade WHERE USER_ID = %s AND STATUS = '%s'"%(user_id,status))
        cursor = c.fetchall()
        res = cursor
        #res = (cursor[0][0])
        conn.close()
        return res
    except Exception as e:
        print(e)
        return '0'

def insert_trade_in_sqlite(t_id,g_id,g_name,u_id,u_name,c_time,st):
    try:
        conn = create_conn()
        c = conn.cursor()
        c.execute("INSERT INTO trade (trade_id,goods_id,goods_name,user_id,user_name,create_time,status) VALUES (%s,%s,'%s',%s,'%s',%s,'%s')"%(t_id,g_id,g_name,u_id,u_name,c_time,st))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(e)
        return False

def get_unpaid_list_from_sqlite():
    try:
        conn = create_conn()
        c = conn.cursor()
        c.execute("SELECT * from trade WHERE STATUS = 'unpaid'")
        cursor = c.fetchall()
        res = cursor
        #res = (cursor[0][0])
        conn.close()
        return res
    except Exception as e:
        print(e)
        return '0'

def update_lock_status_to_sqlite(trade_id):
    try:
        conn = create_conn()
        c = conn.cursor()
        c.execute("UPDATE trade set STATUS = 'lock' WHERE ID = %s"%(id,))
        conn.commit()
        conn.close()
        return True
    except:
        return False

#print(get_trade_list_from_sqlite(121,"unpaid"))
d = "qwqweq"
#print(insert_trade_in_sqlite(1223,222,d,123,'wew',1,'2222'))