import twitter_info # still need this in the same directory, filled out
import tweepy
import json
import sqlite3

consumer_key = twitter_info.consumer_key
consumer_secret = twitter_info.consumer_secret
access_token = twitter_info.access_token
access_token_secret = twitter_info.access_token_secret
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
twitter_api = tweepy.API(auth, parser=tweepy.parsers.JSONParser())

def get_tweets(qury):
    CACHE_FNAME = "twitter_cache.json"
    try:
        cache_file = open(CACHE_FNAME, 'r')
        cache_contents = cache_file.read()
        cache_file.close()
        CACHE_DICTION = json.loads(cache_contents)
    except:
        CACHE_DICTION = {}
    if CACHE_DICTION == {}:
        CACHE_DICTION = twitter_api.search(q=qury)
        open('{}'.format(CACHE_FNAME), 'w').write(json.dumps(CACHE_DICTION))
    else:
        pass
    tweelist=[]
    for i in CACHE_DICTION['statuses']:
        tweelist.append((i['id_str'],i['user']['screen_name'],i['created_at'],i['text'],i['retweet_count']))
    return (tweelist) #list of list containing: id,screen name, time, text, # of retweets