from utils import *
import tweepy
from creds import CredsManager
import sys

cm = CredsManager()

auth = tweepy.OAuthHandler(cm.API_key, cm.API_secret_key)
auth.set_access_token(cm.access_token, cm.access_token_secret)
api = tweepy.API(auth)

publish = True

# authenticate bot
try:
    api.verify_credentials()
    print("Authentication Successful")
except:
    print("Authentication Error, setting publish=False..")
    publish = False

# get usd/try exchange rate
usd_try = get_usd_try()

# get year from exchange rate
year    = round(usd_try*100)

# if that tweet already exists, retweet it
if log_exists(year):
    print(f'Already tweeted about year {year}.')
    log = get_log_for_year(year)
    log_status_id = log['id']
    log_timestamp = log['timestamp']
    if time.time() - log_timestamp > 60*60*24:
        print(f'Retweeting that tweet: {log_status_id}')
        api.retweet(log_status_id)
    else:
        print('Not retweeting because it was in last 24hrs.')
    print('Exiting...')
    sys.exit()
    

# create thread of 1 to n tweets
thread  = get_thread(year, usd_try)

# publish the thread
if publish and thread:
    # Create thread
    tweet_instances = []

    for tweet_text in thread:
        # no previous tweets in thread
        if not tweet_instances:
            tweet_instance = api.update_status(status=tweet_text)
        # prevous tweets exist in thread
        else:
            # respond to latest tweet in thread
            tweet_instance = api.update_status(status=tweet_text, 
                in_reply_to_status_id=tweet_instances[-1].id, 
                auto_populate_reply_metadata=True
            )
        tweet_instances.append(tweet_instance)

    log_create(year, tweet_instances[0].id)

if thread:
    for tweet in thread:
        print(f"[{len(tweet)} chars]\n", tweet, '\n')
else:
    print(f'No thread found, thread={thread}')