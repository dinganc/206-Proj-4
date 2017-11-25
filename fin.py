import fin_Info
import json
import sqlite3
import matplotlib

fb_api=fin_Info.fb_api_secret

#takes in json string, return json dictionary
def cache_to_file(json_str,cache_file_name):
    open('{}'.format(cache_file_name), 'w').write(json.dumps(json.loads(json_str)))
    return (json.loads(json_str))

def load_cache(cache_file_name):
    try:
        cache_file = open(cache_file_name, 'r')
        cache_contents = cache_file.read()
        cache_file.close()
        return (json.loads(cache_contents))
    except:
        return ('Error in loading cache {}'.format(cache_file_name))

def write_to_db(db_name,api_source_name,list_of_tup_to_write):
    conn=sqlite3.connect(db_name)
    cur=conn.cursor()
    cmd_create_table="CREATE TABLE `{}` (`Log_UID`	INTEGER NOT NULL,`Time`	DATETIME NOT NULL,`Unix_UTC_Time`	INTEGER NOT NULL,`User`	TEXT NOT NULL,`Activity_Measure`	INTEGER NOT NULL);".format(api_source_name)
    try:
        cur.execute(cmd_create_table)
        conn.commit()
        print('Created table for {}'.format(api_source_name))
    except:
        print('Table for {} already exists'.format(api_source_name))
    cmd_insert_value="INSERT INTO {} VALUES ?".format(api_source_name)
    for tup in list_of_tup_to_write:
        cur.execute(cmd_insert_value,tup)
        conn.commit()
    cur.close()
    conn.close()

def load_db_to_list(db_name,api_source_name):
    conn=sqlite3.connect(db_name)
    cur=conn.cursor()
    cmd_load="SELECT * FROM {} ORDER BY Unix_UTC_Time ASC"
    quoted_tuple=cur.execute(cmd_load)
    cur.close()
    conn.close()

