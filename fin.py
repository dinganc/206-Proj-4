import fin_Info#import the python file that contains all the log in credential for the APIs
import json
import sqlite3
import requests
import requests.auth
import time
import os
import datetime
import pandas
import matplotlib.pyplot as plt#I used matplot for visualization because plotly does not support world cloud
import numpy as np
#import plotly.plotly as py
#import plotly.tools as tls
from wordcloud import WordCloud

day_of_the_week={#I divide a week into an interval from 0 to 7, and each 6 hour period is 0.25 a part from the other, the below function explains how I convert a time stamp into something like "Mon 12am-6am"
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
    #takes in a unix time stamp and convert it back to literal representation of the time.
    #conversion is based on the mechanics that we only need to know the remainder of time stamp/total number of seconds in a week to know which time point it is in the last week
    #then user floor divide and multiplication to convert the remainder to a number that is divisible by 0.25, which will be the keys in the dictionary
    adjusted_time_stamp=int(unix_stamp)-24*3600*4#The UNIX epoch time is on Jan 1 1970, which is a Thursday, minus 4 days worth of seconds to reset the origin back to Monday 12am
    #print(datetime.datetime.utcfromtimestamp(unix_stamp).strftime('%Y-%m-%dT%H:%M:%SZ'))
    #print(unix_stamp)
    #print((day_of_the_week[(((adjusted_time_stamp/(24*3600*7)-adjusted_time_stamp//(24*3600*7))*7)//0.25)*0.25]))
    return (day_of_the_week[(((adjusted_time_stamp/(24*3600*7)-adjusted_time_stamp//(24*3600*7))*7)//0.25)*0.25])
    #adjuested time stamp/(hours in a day*number of seconds in an hour*number of days in a week)=how many weeks are here from the last Monday of December 1969, the decimal part is very important as demonstrated below
    #adjuested time stamp//(hours in a day*number of seconds in an hour*number of days in a week), the floor divide will give us the interger part of the above calculation
    #the difference between the two above is the decimal number of "excessive" weeks becuase the reamining days cannot be fully divided by seven, for example if 4 days is left, the remainder will be 0.5714
    #times 7 to get it to the number of days that is excessive
    #In the above dictionary, a day is divided into 4 time periods, set apart by 0.25. Therefore, we use the floor divide by 0.25 since we won't care about the excessive number of days
    #times the result by 0.25, we will get the number that exactly matches the key in the dictionary
    #then return the determined literal for the time of the day
    #print(datetime.datetime.utcfromtimestamp(unix_stamp).strftime('%Y-%m-%dT%H:%M:%SZ'))

#takes in json string, return json dictionary after caching into a file, named after the supplied file name
def cache_to_file(json_str,cache_file_name,apiname):
    if not os.path.exists('{}'.format(apiname)):os.makedirs('{}'.format(apiname))#save the cache to the folder named after the api, thus have to first check if the folder exists
    open('{}'.format(apiname+'//'+cache_file_name), 'w',encoding='utf-8').write(json_str)#create/ over write the cache file with json string

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

def write_to_db(db_name,api_source_name,list_of_tup_to_write):#conviniently takes in a list of entry that needs to write and write it to the table named after the api
    conn=sqlite3.connect(db_name)#connects to the database
    cur=conn.cursor()
    cmd_create_table="CREATE TABLE `{}` (`Log_UID`	TEXT NOT NULL UNIQUE,`Day`	TEXT NOT NULL,`Unix_UTC_Time`	INTEGER NOT NULL,`Text_Note`	TEXT NOT NULL,`Activity_Measure`	INTEGER NOT NULL,PRIMARY KEY(`Log_UID`));".format(api_source_name)
    #Log UID is an unique identifier for each entry, for example, each facebook post has an unique number that refers to it
    #day is the time of the day that is determined by the above check_time_point function
    #unix utc time is the time stamp of the post
    #text note is any text that I want to save to the post, for example, user name or comments
    #activity measure is an interger that measures some kind of activity level, for example, how many people commented
    #the code can create the table if does not exist
    try:#try because the table might already exist if the user did not delete the database
        cur.execute(cmd_create_table)
        conn.commit()#saves the database
        print('Created table for {}'.format(api_source_name))
    except:
        print('Table for {} already exists'.format(api_source_name))
    cmd_insert_value="INSERT INTO {} VALUES (?,?,?,?,?)".format(api_source_name)#each api gets its own table
    for tup in list_of_tup_to_write:#tup is the tuple that contains one entry we want to write to the database, Log UID, time of the day, timestamp, text message, activity measure
        try:#list of tup is a list of such tuple that needs to write
            cur.execute(cmd_insert_value,tup)
            conn.commit()
        except:
            pass
    cur.close()
    conn.close()

def load_db_to_list(db_name,api_source_name,param_name):# used later in the visualization process to pull data from the database
    conn=sqlite3.connect(db_name)
    cur=conn.cursor()
    cmd_load="SELECT {} FROM {} ORDER BY Unix_UTC_Time ASC".format(param_name,api_source_name)#select by order to ensure the chronicallogical order
    quoted_tuple=cur.execute(cmd_load).fetchall()#fetch all
    cur.close()
    conn.close()
    return quoted_tuple#return the tuple

def reddit_access(load_turns,wait_interval,cache_toggle):
    posts=[]# this is the list of tuple that will be passed into the write to database function

    def get_access_token():
        client_auth = requests.auth.HTTPBasicAuth('{}'.format(fin_Info.reddit_app_key), '{}'.format(fin_Info.reddit_api_secret))#Oauth through requests module
        post_data = {"grant_type": "password", "username": "{}".format(fin_Info.reddit_user_name), "password": "{}".format(fin_Info.reddit_password)}
        headers = {"User-Agent": "Ahhhhhhh/0.1 by John Woody"}
        requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data,headers=headers)#request the token from reddit
        return headers
#if cache toggle is off, then the program will try to do api call and refresh cache
    if cache_toggle==False:
        initial_req_new_posts=r'https://www.reddit.com/r/uofm/hot.json?&limit=1000'
        first_page_str=requests.get(initial_req_new_posts,headers=get_access_token()).text#get the json string
        first_page=json.loads(first_page_str)#load string into dictionary
        time.sleep(wait_interval)# wait a second so i'm not spamming reddit's server
        next_page_id =first_page['data']['after']#reddit uses an id to navigate between pages of search result
        cache_to_file(first_page_str, 'reddit_first_page', 'reddit')#store the raw json string to cahce file named reddit first page under the folder reddit
        for i in first_page['data']['children']:#accessing each post
            try:
                posts.append((i['data']['url'], check_time_point(i['data']['created_utc']), i['data']['created_utc'],
                              i['data']['title'],
                              i['data']['num_comments']))#append to the list of tuple waiting to be submitted to database
            except:
                pass

        for i in range(load_turns):#flipping pages
            new_req_new_posts = initial_req_new_posts + 'after=' + next_page_id#reddit uses after param in the api request to access the next page
            next_page_str = requests.get(new_req_new_posts, headers=get_access_token()).text#get json string
            next_page = json.loads(next_page_str)
            time.sleep(wait_interval)
            next_page_id = next_page['data']['after']#below is simialr to the above process of extracting info each each post, this line refreshes the after id
            cache_to_file(next_page_str, 'reddit_next_page_' + next_page_id, 'reddit')
            for i in next_page['data']['children']:
                try:
                    posts.append((i['data']['url'], check_time_point(i['data']['created_utc']), i['data']['created_utc'],
                                  i['data']['title'],
                                  i['data']['num_comments']))
                except:
                    pass

    else:# else is for when cache toggle is switched on, so the program will load json string from cache instead of pulling fresh json by api call
        for i in [i for i in os.walk([os.getcwd()][0] + '//' + 'reddit')][0][2]:#get all the file names under the reddit folder
            page=load_cache('reddit'+'//'+i)#calling the load cache funtion to load the json string to a dictionary, dictionary will be empty if no cache is there
            for i in page['data']['children']:
                try:
                    posts.append((i['data']['url'], check_time_point(i['data']['created_utc']), i['data']['created_utc'], i['data']['title'],
                           i['data']['num_comments']))
                except:#if no cache already exist, then the program will fail for exception
                    pass

    print(len(sorted(set(posts),key=lambda x:x[2])))#checking if get 100 entries
    return sorted(set(posts), key=lambda x: x[2])[:100]#cut for exact 100 entries

def APIXU_access(load_turns,wait_interval,cache_toggle):
    posts=[]
    counter = 0
    if cache_toggle==False:#similar to above cache toggle structure
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
                if counter%3==0:
                    try:
                        posts.append((hour['time'],check_time_point(hour['time_epoch']),hour['time_epoch'],hour['condition']['text'],hour['temp_f']))
                        counter+=1
                    except:
                        counter += 1
                else:
                    counter += 1
    else:
        for i in [i for i in os.walk([os.getcwd()][0] + '//' + 'APIXU')][0][2]:
            page=load_cache('APIXU'+'//'+i)
            for hour in page['forecast']['forecastday'][0]['hour']:
                if counter%3==0:
                    try:
                        posts.append((hour['time'],check_time_point(hour['time_epoch']),hour['time_epoch'],hour['condition']['text'],hour['temp_f']))
                        counter+=1
                    except:
                        counter += 1
                else:
                    counter += 1
    print(len(sorted(set(posts), key=lambda x: x[2])))
    return sorted(set(posts), key=lambda x: x[2])[-100:]

def facebook_access(load_turns,wait_interval,cache_toggle):
    posts=[]
    # for facebook, I can only access my own data, so I pulled my data from multiple sources such as posts, events, and stuff I liked
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
    #this is loading the cache files
    else:
        for i in [i for i in os.walk([os.getcwd()][0] + '//' + 'facebook')][0][2]:
            if 'likes' in i:#if likes is in the file name, then it is a cache file for the like call, I have to do this because the stucture and keys are different between these objects
                page=load_cache('facebook'+'//'+i)
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
            if 'feed' in i:#if feed is in the file name, then it is a cache file for the feed call
                page = load_cache('facebook' + '//' + i)
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
                page = load_cache('facebook' + '//' + i)
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
    return sorted(set(posts), key=lambda x: x[2])[:100]

def pinterest_access(load_turns,wait_interval,cache_toggle):
    posts=[]
    #pinterest is similar to facebook as I can only access my own data
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
            cache_to_file(first_page_str, 'pinterest_pins_page_{}'.format(k), 'pinterest')
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
            next_page = first_page['page']['next']#similar flip page mechanism as reddit
    else:
        for i in [i for i in os.walk([os.getcwd()][0] + '//' + 'pinterest')][0][2]:
            page = load_cache('pinterest' + '//' + i)
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
    return sorted(set(posts), key=lambda x: x[2])[:100]

def github_access(load_turns,wait_interval,cache_toggle):
    posts=[]
    if cache_toggle==False:#similar caching mechanism like above
        initial_req_new_posts='https://api.github.com/search/repositories?q=umich&sort=stars&order=desc&per_page=100'#seach for repos that contains "umich"
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
        for i in [i for i in os.walk([os.getcwd()][0] + '//' + 'github')][0][2]:
            page=load_cache('github'+'//'+i)
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
    return sorted(set(posts), key=lambda x: x[2])[:100]

try:reddit_list=reddit_access(4,1,True)#first try to run the access by loading the cache file, if it is the first time and the cache does not exist, the exception will trigger because the dictionary will be empty, and my program is looking for a key that does not exist
except:reddit_list=reddit_access(4,1,False)#after the first fail, then run the access and tell the program to call api and pull fresh cache data
try:weather_list=APIXU_access(20,1,True)#if the cache already exist and loads successfully, then the no cache code won'r run because it is after the except statement
except:weather_list=APIXU_access(20,1,False)
try:fb_list=facebook_access(4,1,True)
except:fb_list=facebook_access(4,1,False)
try:pt_list=pinterest_access(4,1,True)
except:pt_list=pinterest_access(4,1,False)
try:gt_list=github_access(4,1,True)
except:gt_list=github_access(4,1,False)

write_to_db('proj4.db','reddit',reddit_list)#write the tupple to the database, save to the table named after the api
write_to_db('proj4.db','weather',weather_list)
write_to_db('proj4.db','facebook',fb_list)
write_to_db('proj4.db','pinterest',pt_list)
write_to_db('proj4.db','github',gt_list)

table_list=['reddit','facebook','pinterest','github','weather']#
time_point_list=[i[1] for i in sorted(day_of_the_week.items(),key=lambda x:x[0])]
api_activity_timepoints={}
for j in table_list:
    if j != 'weather':
        count_activity={}
        for m in time_point_list:
            count_activity[m]=0
        for k in load_db_to_list('proj4.db',j,'Day'):
            count_activity[k[0]]+=1
        api_activity_timepoints[j]=[count_activity[i] for i in time_point_list]
    if j =='weather':
        count_activity={}
        for m in time_point_list:
            count_activity[m]=[]
        for k in load_db_to_list('proj4.db',j,'Day,Activity_Measure'):
            count_activity[k[0]].append(k[1])
        api_activity_timepoints[j]=[sum(count_activity[i])/(len(count_activity[i])) for i in time_point_list]

api_data=pandas.DataFrame([api_activity_timepoints[i] for i in table_list],index=table_list,columns=time_point_list)
print(api_data)

axes_fig1 = []
fig1 = plt.figure(figsize=(12, 12))
axes_fig1.append(plt.subplot2grid(shape=(2, 1), loc=(0, 0), rowspan=(1), colspan=(1)))
axes_fig1.append(plt.subplot2grid(shape=(2, 1), loc=(1, 0), rowspan=(1), colspan=(1)))

axes_fig1[1].pcolor(api_data.loc[api_data.index.isin(['reddit','github'])], cmap=plt.cm.Blues)
axes_fig1[1].set_yticklabels(['reddit','github'], minor=False)
axes_fig1[1].set_xticklabels(time_point_list, minor=False,rotation = 90)
axes_fig1[1].set_yticks(np.arange(api_data.loc[api_data.index.isin(['reddit','github'])].shape[0])+0.5, minor=False)
axes_fig1[1].set_xticks(np.arange(api_data.loc[api_data.index.isin(['reddit','github'])].shape[1])+0.5, minor=False)

axes_fig1[0].pcolor(api_data.loc[api_data.index.isin(['facebook','pinterest'])], cmap=plt.cm.Blues)
axes_fig1[0].set_yticklabels(['facebook','pinterest'], minor=False)
axes_fig1[0].set_xticklabels([])
axes_fig1[0].set_yticks(np.arange(api_data.loc[api_data.index.isin(['facebook','pinterest'])].shape[0])+0.5, minor=False)
axes_fig1[0].set_xticks(np.arange(api_data.loc[api_data.index.isin(['facebook','pinterest'])].shape[1])+0.5, minor=False)

axes_fig1[0].set_title('Activity for Myself')
axes_fig1[1].set_title('Activity for All UMich Users')
fig1.suptitle('Activity Heatmap Comparison', fontsize=14, fontweight='bold')
fig1.savefig("Activity Heatmap Comparison")

axes_fig2 = []
fig2 = plt.figure(figsize=(12, 12))
axes_fig2.append(plt.subplot2grid(shape=(2, 1), loc=(0, 0), rowspan=(1), colspan=(1)))
axes_fig2.append(plt.subplot2grid(shape=(2, 1), loc=(1, 0), rowspan=(1), colspan=(1)))
axes_fig2.append(axes_fig2[0].twinx())
axes_fig2.append(axes_fig2[1].twinx())
api_data.loc[api_data.index.isin(['weather'])].transpose().plot(ax=axes_fig2[2],color='#2B9D36')
api_data.loc[api_data.index.isin(['weather'])].transpose().plot(ax=axes_fig2[3],color='#2B9D36')

axes_fig2[2].set_xticklabels([])
vals = axes_fig2[2].get_yticks()
axes_fig2[2].set_yticklabels(['{} °F'.format(x) for x in vals])
axes_fig2[2].set_xticks([])
axes_fig2[2].legend(loc='center left', bbox_to_anchor=(1, 0.5))

axes_fig2[3].set_xticklabels([])
vals = axes_fig2[3].get_yticks()
axes_fig2[3].set_yticklabels(['{} °F'.format(x) for x in vals])
axes_fig2[3].set_xticks([])
axes_fig2[3].legend(loc='center left', bbox_to_anchor=(1, 0.5))

api_data.loc[api_data.index.isin(['facebook','pinterest'])].transpose().plot(ax=axes_fig2[0],kind='bar')
api_data.loc[api_data.index.isin(['reddit','github'])].transpose().plot(ax=axes_fig2[1],kind='bar')

axes_fig2[1].set_xticklabels(time_point_list, minor=False,rotation = 90)
vals = axes_fig2[1].get_yticks()
axes_fig2[1].set_yticklabels(['{} Interaction(s)'.format(int(x)) for x in vals])

axes_fig2[0].set_xticklabels([])
vals = axes_fig2[0].get_yticks()
axes_fig2[0].set_yticklabels(['{} Interaction(s)'.format(int(x)) for x in vals])
axes_fig2[0].set_xticks([])

axes_fig2[0].set_title('Activity for Myself')
axes_fig2[1].set_title('Activity for All UMich Users')
fig2.suptitle('Temperature Impact on Activity Level', fontsize=14, fontweight='bold')

fig2.savefig('Temperature Impact on Activity Level')

reddit_word_list=[]
for k in load_db_to_list('proj4.db','reddit','Text_Note'):
    for j in k[0].split():reddit_word_list.append(''.join(e for e in j if e.isalnum()))

axes_fig3=[]
fig3 = plt.figure(figsize=(12, 12))
axes_fig3.append(plt.subplot2grid(shape=(1, 1), loc=(0, 0), rowspan=(1), colspan=(1)))
wordcloud = WordCloud(width=1200, height=1200).generate(" ".join(reddit_word_list))
axes_fig3[0].imshow(wordcloud)
axes_fig3[0].axis("off")
fig3.suptitle('World Cloud for UM Subreddit', fontsize=14, fontweight='bold')
fig3.savefig('World Cloud for UM Subreddit')

#py.sign_in(fin_Info.plotly_user_name, fin_Info.plotly_API_key)
#unique_url1 = py.plot_mpl(fig3