import fin_Info
import json
import sqlite3
import requests
import requests.auth
import time
import os
import datetime
import matplotlib

day_of_the_week={
    0:'Mon 12am - 6am',
    0.25:'Mon 6am - 12pm',
    0.5:'Mon 12pm - 6pm',
    0.75:'Mon 6pm - 12am',
    1: 'Tue 12am - 6am',
    1.25: 'Tue 6am - 12pm',
    1.5: 'Tue 12pm - 6pm',
    1.75: 'Tue 6pm - 12am',
    2: 'Wed 12am - 6am',
    2.25: 'Wed 6am - 12pm',
    2.5: 'Wed 12pm - 6pm',
    2.75: 'Wed 6pm - 12am',
    3: 'Thu 12am - 6am',
    3.25: 'Thu 6am - 12pm',
    3.5: 'Thu 12pm - 6pm',
    3.75: 'Thu 6pm - 12am',
    4: 'Fri 12am - 6am',
    4.25: 'Fri 6am - 12pm',
    4.5: 'Fri 12pm - 6pm',
    4.75: 'Fri 6pm - 12am',
    5: 'Sat 12am - 6am',
    5.25: 'Sat 6am - 12pm',
    5.5: 'Sat 12pm - 6pm',
    5.75: 'Sat 6pm - 12am',
    6: 'Sun 12am - 6am',
    6.25: 'Sun 6am - 12pm',
    6.5: 'Sun 12pm - 6pm',
    6.75: 'Sun 6pm - 12am',
}

def check_time_point(unix_stamp):
    adjusted_time_stamp=int(unix_stamp)-24*3600*4#The UNIX epoch time is on Jan 1 1970, which is a Thursday, minus 4 days worth of seconds to reset the origin back to Monday 12am
    #print(datetime.datetime.utcfromtimestamp(unix_stamp).strftime('%Y-%m-%dT%H:%M:%SZ'))
    #print(unix_stamp)
    #print((day_of_the_week[(((adjusted_time_stamp/(24*3600*7)-adjusted_time_stamp//(24*3600*7))*7)//0.25)*0.25]))
    return (day_of_the_week[(((adjusted_time_stamp/(24*3600*7)-adjusted_time_stamp//(24*3600*7))*7)//0.25)*0.25])
    #print(datetime.datetime.utcfromtimestamp(unix_stamp).strftime('%Y-%m-%dT%H:%M:%SZ'))

#takes in json string, return json dictionary after caching into a file, named after the supplied file name
def cache_to_file(json_str,cache_file_name,apiname):
    if not os.path.exists('{}'.format(apiname)):os.makedirs('{}'.format(apiname))
    open('{}'.format(apiname+'\\'+cache_file_name), 'w',encoding='utf-8').write(json_str)#create/ over write the cache file with json string

#try to load the cache into python object, if failed, it will return the error message
def load_cache(cache_file_name):
    try:
        cache_file = open(cache_file_name, 'r')  # open cache file
        cache_contents = cache_file.read()  # read lines of the file
        cache_file.close()  # close the file
        return (json.loads(cache_contents))  # load the lines to python object
    except Exception as ex:
        print(ex)
        return ('Error in loading cache {}'.format(cache_file_name))#print the name of the cache file if didn't load anything (becaue cache file does not exist)

def write_to_db(db_name,api_source_name,list_of_tup_to_write):
    conn=sqlite3.connect(db_name)
    cur=conn.cursor()
    cmd_create_table="CREATE TABLE `{}` (`Log_UID`	INTEGER NOT NULL,`Day`	TEXT NOT NULL,`Unix_UTC_Time`	INTEGER NOT NULL,`Text_Note`	TEXT NOT NULL,`Activity_Measure`	INTEGER NOT NULL);".format(api_source_name)
    try:
        cur.execute(cmd_create_table)
        conn.commit()
        print('Created table for {}'.format(api_source_name))
    except:
        print('Table for {} already exists'.format(api_source_name))
    cmd_insert_value="INSERT INTO {} VALUES (?,?,?,?,?)".format(api_source_name)
    for tup in list_of_tup_to_write:
        cur.execute(cmd_insert_value,tup)
        conn.commit()
    cur.close()
    conn.close()

def load_db_to_list(db_name,api_source_name):
    conn=sqlite3.connect(db_name)
    cur=conn.cursor()
    cmd_load="SELECT * FROM {} ORDER BY Unix_UTC_Time ASC".format(api_source_name)
    quoted_tuple=cur.execute(cmd_load)
    cur.close()
    conn.close()
    return quoted_tuple

def reddit_access(load_turns,wait_interval,cache_toggle):
    posts=[]

    def get_access_token():
        client_auth = requests.auth.HTTPBasicAuth('{}'.format(fin_Info.reddit_app_key), '{}'.format(fin_Info.reddit_api_secret))
        post_data = {"grant_type": "password", "username": "{}".format(fin_Info.reddit_user_name), "password": "{}".format(fin_Info.reddit_password)}
        headers = {"User-Agent": "Ahhhhhhh/0.1 by John Woody"}
        requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data,headers=headers)
        return headers

    if cache_toggle==False:
        initial_req_new_posts=r'https://www.reddit.com/r/uofm/hot.json?&limit=1000'
        first_page_str=requests.get(initial_req_new_posts,headers=get_access_token()).text
        first_page=json.loads(first_page_str)
        time.sleep(wait_interval)
        next_page_id =first_page['data']['after']
        cache_to_file(first_page_str, 'reddit_first_page', 'reddit')
        for i in first_page['data']['children']:
            try:
                posts.append((i['data']['url'], check_time_point(i['data']['created_utc']), i['data']['created_utc'],
                              i['data']['author'],
                              i['data']['num_comments']))
            except:
                pass

        for i in range(load_turns):
            new_req_new_posts = initial_req_new_posts + 'after=' + next_page_id
            next_page_str = requests.get(new_req_new_posts, headers=get_access_token()).text
            next_page = json.loads(next_page_str)
            time.sleep(wait_interval)
            next_page_id = next_page['data']['after']
            cache_to_file(next_page_str, 'reddit_next_page_' + next_page_id, 'reddit')
            for i in next_page['data']['children']:
                try:
                    posts.append((i['data']['url'], check_time_point(i['data']['created_utc']), i['data']['created_utc'],
                                  i['data']['author'],
                                  i['data']['num_comments']))
                except:
                    pass

    else:
        for i in [i for i in os.walk([os.getcwd()][0] + '\\' + 'reddit')][0][2]:
            page=load_cache('reddit'+'\\'+i)
            for i in page['data']['children']:
                try:
                    posts.append((i['data']['url'], check_time_point(i['data']['created_utc']), i['data']['created_utc'], i['data']['author'],
                           i['data']['num_comments']))
                except:
                    pass

    print(len(sorted(set(posts),key=lambda x:x[2])))
    return sorted(set(posts), key=lambda x: x[2])

def APIXU_access(load_turns,wait_interval,cache_toggle):
    posts=[]
    if cache_toggle==False:
        dates=[]
        for i in range(0,load_turns+1):
            dates.append((datetime.datetime.today()-datetime.timedelta(days=i)).strftime('%Y-%m-%d'))
        for i in dates:
            req_new_posts=r'http://api.apixu.com/v1/history.json?key={}&q=48104&dt={}'.format(fin_Info.APIXU_secret,i)
            first_page_str = requests.get(req_new_posts).text
            first_page = json.loads(first_page_str)
            time.sleep(wait_interval)
            cache_to_file(first_page_str, 'APIXU_Day_{}'.format(i), 'APIXU')
            for hour in first_page['forecast']['forecastday'][0]['hour']:
                try:
                    posts.append((hour['time'],check_time_point(hour['time_epoch']),hour['time_epoch'],hour['condition']['text'],hour['temp_f']))
                except:
                    pass
    else:
        for i in [i for i in os.walk([os.getcwd()][0] + '\\' + 'APIXU')][0][2]:
            page=load_cache('APIXU'+'\\'+i)
            for hour in page['forecast']['forecastday'][0]['hour']:
                try:
                    posts.append((hour['time'],check_time_point(hour['time_epoch']),hour['time_epoch'],hour['condition']['text'],hour['temp_f']))
                except:
                    pass

    print(len(sorted(set(posts), key=lambda x: x[2])))
    return sorted(set(posts), key=lambda x: x[2])

def facebook_access(load_turns,wait_interval,cache_toggle):
    posts=[]

    if cache_toggle==False:
        initial_req_new_posts=r'https://graph.facebook.com/v2.11/me/feed?access_token={}'.format(fin_Info.facebook_token)
        first_page_str=requests.get(initial_req_new_posts).text
        first_page=json.loads(first_page_str)
        time.sleep(wait_interval)
        cache_to_file(first_page_str, 'facebook_feed', 'facebook')
        for i in first_page['data']:
            try:
                posts.append((i['id'], check_time_point(datetime.datetime.strptime(i['created_time'],"%Y-%m-%dT%H:%M:%S%z").timestamp()), datetime.datetime.strptime(i['created_time'],"%Y-%m-%dT%H:%M:%S%z").timestamp(),
                              i['story'],
                              0))
            except:
                posts.append((i['id'], check_time_point(datetime.datetime.strptime(i['created_time'],"%Y-%m-%dT%H:%M:%S%z").timestamp()), datetime.datetime.strptime(i['created_time'],"%Y-%m-%dT%H:%M:%S%z").timestamp(),
                              '',
                              0))

        second_req_new_posts=r'https://graph.facebook.com/v2.11/me/likes?access_token={}'.format(fin_Info.facebook_token)
        second_page_str=requests.get(second_req_new_posts).text
        second_page=json.loads(second_page_str)
        time.sleep(wait_interval)
        cache_to_file(second_page_str, 'facebook_likes', 'facebook')
        try:
            next_page=second_page['paging']['next']
            still_page_left=True
        except:
            still_page_left=False
        for i in second_page['data']:
            try:
                posts.append((i['id'], check_time_point(datetime.datetime.strptime(i['created_time'],"%Y-%m-%dT%H:%M:%S%z").timestamp()), datetime.datetime.strptime(i['created_time'],"%Y-%m-%dT%H:%M:%S%z").timestamp(),
                              i['name'],
                              0))
            except:
                posts.append((i['id'], check_time_point(datetime.datetime.strptime(i['created_time'],"%Y-%m-%dT%H:%M:%S%z").timestamp()), datetime.datetime.strptime(i['created_time'],"%Y-%m-%dT%H:%M:%S%z").timestamp(),
                              '',
                              0))
        k = 2
        while still_page_left==True:
            try:
                second_req_new_posts = next_page
                second_page_str = requests.get(second_req_new_posts).text
                second_page = json.loads(second_page_str)
                time.sleep(wait_interval)
                cache_to_file(second_page_str, 'facebook_likes_page_{}'.format(k), 'facebook')
                k+=1
                next_page = second_page['paging']['next']
                for i in second_page['data']:
                    try:
                        posts.append((i['id'], check_time_point(
                            datetime.datetime.strptime(i['created_time'], "%Y-%m-%dT%H:%M:%S%z").timestamp()),
                                      datetime.datetime.strptime(i['created_time'], "%Y-%m-%dT%H:%M:%S%z").timestamp(),
                                      i['name'],
                                      0))
                    except:
                        posts.append((i['id'], check_time_point(
                            datetime.datetime.strptime(i['created_time'], "%Y-%m-%dT%H:%M:%S%z").timestamp()),
                                      datetime.datetime.strptime(i['created_time'], "%Y-%m-%dT%H:%M:%S%z").timestamp(),
                                      '',
                                      0))
            except Exception as ex:
                still_page_left=False

        third_req_new_posts=r'https://graph.facebook.com/v2.11/me/events?access_token={}'.format(fin_Info.facebook_token)
        third_page_str=requests.get(third_req_new_posts).text
        third_page=json.loads(third_page_str)
        time.sleep(wait_interval)
        cache_to_file(third_page_str, 'facebook_events', 'facebook')
        for i in third_page['data']:
            try:
                posts.append((i['id'], check_time_point(datetime.datetime.strptime(i['start_time'],"%Y-%m-%dT%H:%M:%S%z").timestamp()), datetime.datetime.strptime(i['start_time'],"%Y-%m-%dT%H:%M:%S%z").timestamp(),
                              i['name'],
                              0))
            except:
                posts.append((i['id'], check_time_point(datetime.datetime.strptime(i['start_time'],"%Y-%m-%dT%H:%M:%S%z").timestamp()), datetime.datetime.strptime(i['start_time'],"%Y-%m-%dT%H:%M:%S%z").timestamp(),
                              '',
                              0))

    else:
        for i in [i for i in os.walk([os.getcwd()][0] + '\\' + 'facebook')][0][2]:
            if 'likes' in i:
                page=load_cache('facebook'+'\\'+i)
                for i in page['data']:
                    try:
                        posts.append((i['id'], check_time_point(
                            datetime.datetime.strptime(i['created_time'], "%Y-%m-%dT%H:%M:%S%z").timestamp()),
                                      datetime.datetime.strptime(i['created_time'], "%Y-%m-%dT%H:%M:%S%z").timestamp(),
                                      i['name'],
                                      0))
                    except:
                        posts.append((i['id'], check_time_point(
                            datetime.datetime.strptime(i['created_time'], "%Y-%m-%dT%H:%M:%S%z").timestamp()),
                                      datetime.datetime.strptime(i['created_time'], "%Y-%m-%dT%H:%M:%S%z").timestamp(),
                                      '',
                                      0))
            if 'feed' in i:
                page = load_cache('facebook' + '\\' + i)
                for i in page['data']:
                    try:
                        posts.append((i['id'], check_time_point(
                            datetime.datetime.strptime(i['created_time'], "%Y-%m-%dT%H:%M:%S%z").timestamp()),
                                      datetime.datetime.strptime(i['created_time'], "%Y-%m-%dT%H:%M:%S%z").timestamp(),
                                      i['story'],
                                      0))
                    except:
                        posts.append((i['id'], check_time_point(
                            datetime.datetime.strptime(i['created_time'], "%Y-%m-%dT%H:%M:%S%z").timestamp()),
                                      datetime.datetime.strptime(i['created_time'], "%Y-%m-%dT%H:%M:%S%z").timestamp(),
                                      '',
                                      0))
            if 'events' in i:
                page = load_cache('facebook' + '\\' + i)
                for i in page['data']:
                    try:
                        posts.append((i['id'], check_time_point(
                            datetime.datetime.strptime(i['start_time'], "%Y-%m-%dT%H:%M:%S%z").timestamp()),
                                      datetime.datetime.strptime(i['start_time'], "%Y-%m-%dT%H:%M:%S%z").timestamp(),
                                      i['name'],
                                      0))
                    except:
                        posts.append((i['id'], check_time_point(
                            datetime.datetime.strptime(i['start_time'], "%Y-%m-%dT%H:%M:%S%z").timestamp()),
                                      datetime.datetime.strptime(i['start_time'], "%Y-%m-%dT%H:%M:%S%z").timestamp(),
                                      '',
                                      0))

    print(len(sorted(set(posts),key=lambda x:x[2])))
    return sorted(set(posts), key=lambda x: x[2])

def pinterest_access(load_turns,wait_interval,cache_toggle):
    posts=[]
    if cache_toggle == False:
        initial_req_new_posts='https://api.pinterest.com/v1/me/pins/?access_token={}&fields=id%2Cnote%2Ccreated_at'.format(fin_Info.pinterest_token)
        first_page_str=requests.get(initial_req_new_posts).text
        first_page=json.loads(first_page_str)
        time.sleep(wait_interval)
        cache_to_file(first_page_str, 'pinterest_pins', 'pinterest')
        next_page=first_page['page']['next']
        for i in first_page['data']:
            try:
                posts.append((i['id'],check_time_point(
                                datetime.datetime.strptime(i['created_at'], "%Y-%m-%dT%H:%M:%S").timestamp()),
                                          datetime.datetime.strptime(i['created_at'], "%Y-%m-%dT%H:%M:%S").timestamp(),
                                          i['note'],
                                          0))
            except:
                pass
        k=2
        while next_page!=None:
            initial_req_new_posts = next_page
            first_page_str = requests.get(initial_req_new_posts).text
            first_page = json.loads(first_page_str)
            time.sleep(wait_interval)
            cache_to_file(first_page_str, 'pinterest_pins_page_'.format(k), 'pinterest')
            k+=1
            for i in first_page['data']:
                try:
                    posts.append((i['id'], check_time_point(
                        datetime.datetime.strptime(i['created_at'], "%Y-%m-%dT%H:%M:%S").timestamp()),
                                  datetime.datetime.strptime(i['created_at'], "%Y-%m-%dT%H:%M:%S").timestamp(),
                                  i['note'],
                                  0))
                except:
                    pass
            next_page = first_page['page']['next']
    else:
        for i in [i for i in os.walk([os.getcwd()][0] + '\\' + 'pinterest')][0][2]:
            page = load_cache('pinterest' + '\\' + i)
            for i in page['data']:
                try:
                    posts.append((i['id'], check_time_point(
                        datetime.datetime.strptime(i['created_at'], "%Y-%m-%dT%H:%M:%S").timestamp()),
                                  datetime.datetime.strptime(i['created_at'], "%Y-%m-%dT%H:%M:%S").timestamp(),
                                  i['note'],
                                  0))
                except:
                    pass

    print(len(sorted(set(posts), key=lambda x: x[2])))
    return sorted(set(posts), key=lambda x: x[2])

def github_access(load_turns,wait_interval,cache_toggle):
    posts=[]
    if cache_toggle==False:
        initial_req_new_posts='https://api.github.com/search/repositories?q=umich&sort=stars&order=desc&per_page=100'
        first_page_str=requests.get(initial_req_new_posts).text
        first_page=json.loads(first_page_str)
        time.sleep(wait_interval)
        cache_to_file(first_page_str, 'github_repos', 'github')
        for i in first_page['items']:
            try:
                posts.append((i['id'], check_time_point(
                        datetime.datetime.strptime(i['pushed_at'], "%Y-%m-%dT%H:%M:%SZ").timestamp()),
                                  datetime.datetime.strptime(i['pushed_at'], "%Y-%m-%dT%H:%M:%SZ").timestamp(),
                                  i['owner']['login'],
                                  i['score']))
            except Exception as ex:
                print(ex)
    else:
        for i in [i for i in os.walk([os.getcwd()][0] + '\\' + 'github')][0][2]:
            page=load_cache('github'+'\\'+i)
            for i in page['items']:
                try:
                    posts.append((i['id'], check_time_point(
                        datetime.datetime.strptime(i['pushed_at'], "%Y-%m-%dT%H:%M:%SZ").timestamp()),
                                  datetime.datetime.strptime(i['pushed_at'], "%Y-%m-%dT%H:%M:%SZ").timestamp(),
                                  i['owner']['login'],
                                  i['score']))
                except Exception as ex:
                    print(ex)
    print(len(sorted(set(posts), key=lambda x: x[2])))
    return sorted(set(posts), key=lambda x: x[2])

try:reddit_list=reddit_access(4,1,True)
except:reddit_list=reddit_access(4,1,False)
try:weather_list=APIXU_access(17,1,True)
except:weather_list=APIXU_access(17,1,False)
try:fb_list=facebook_access(4,1,True)
except:fb_list=facebook_access(4,1,False)
try:pt_list=pinterest_access(4,1,True)
except:pt_list=pinterest_access(4,1,False)
try:gt_list=github_access(4,1,True)
except:gt_list=github_access(4,1,False)

write_to_db('proj4.db','reddit',reddit_list)
write_to_db('proj4.db','weather',weather_list)
write_to_db('proj4.db','facebook',fb_list)
write_to_db('proj4.db','pinterest',pt_list)
write_to_db('proj4.db','github',gt_list)

