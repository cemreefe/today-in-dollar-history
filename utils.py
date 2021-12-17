from os import stat
import requests
import math
import json
from bs4 import BeautifulSoup
import time
import re

def get_usd_try():
  # get usd try conversion rate from API
  # response = requests.get('https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies/usd.json')
  # response_data = response.json()
  # usd_try = response_data['usd']['try']
  response = requests.get('https://www.oyakyatirim.com.tr/OtherMarkets/GetSpotGraph?code=USDTRL')
  usd_try = response.json()[-1][1]

  print('## USD/TRY Exchange rate:', usd_try, '\n')
  return usd_try

def get_details(h2object):
  title = h2object.find_all('span')[1].get('id') or h2object.find_all('span')[0].get('id')

  items = h2object.find_next('ul').find_all('li', recursive=False)
  items = [e.text.strip() for e in items]
  items = [item[18:] if item.startswith('tarihi bilinmeyen') else item for item in items]

  return {'title':title, 'items':items}


def get_h2_info(year):
  # get year data from wikipedia
  response = requests.get(f'https://tr.wikipedia.org/wiki/{year}')
  soup = BeautifulSoup(response.text, 'html.parser')

  h2s = soup.find_all('h2')

  for h2 in h2s:
    print(h2, '\n')

  if h2s[0].get('id') == 'mw-toc-heading':
    h2s = h2s[1:]

  event_categories = h2s[:3]

  tweet_details = []

  subcat_details = [get_details(events_info) for events_info in event_categories ]
  subcat_exists  = [
    subcat['items'] and (i == (len(subcat_details)-1) or (subcat['items'] != subcat_details[i+1]['items'])) 
    for i, subcat in enumerate(subcat_details)
  ]

  for exists, details in zip(subcat_exists, subcat_details):
    if exists:
      tweet_details = [details]
      break

  return tweet_details

def get_tweets(tweet_data, year, usd_try, log=False):

  # doesn't take into account the paginator 
  # so give some extra space
  max_allowed_tweet_length = 240 

  nl = '\n'
  
  title = tweet_data['title'].lower()
  
  if title == 'olaylar':
    if year < 2022:
      title = f"{year} Yılında neler olmuştu?"
    else:
      title = f"{year} Yılında neler olacak?"

  elif title == 'doğumlar':
    title = f"{year} Yılında kimler doğmuştu?"

  elif title == 'ölümler':
    title = f"{year} Yılında kimler ölmüştü?"
  
  max_body_length = max_allowed_tweet_length - len(title) - 3

  tweet_bodies = ['']

  for item in tweet_data['items']:

    items = []

    if len(item) > max_body_length:
      if log:
        print(f"Error item too long <{item}>")
      items = item.split('\n')
      # for multi-line case
      for item in items:
        try:
          assert len(item) <= max_body_length
        except:
          if log:
            print('Splitting also does not work.')
          continue
    
    # for compatibility with multi-line case
    items = items or [item]

    for item in items:
      item = re.sub(r"\[.*?\]", "", item)
      if len(tweet_bodies[-1]) + len(item) + 3 > max_body_length:
        tweet_bodies.append('')
      tweet_bodies[-1] += '\n• ' + item 

  if len(tweet_bodies) > 1:
    tweets = [
      f"$1 = ₺{usd_try:.2f} 💸{nl}{title} {str(i+1)+'/'+str(len(tweet_bodies))}{body}" 
      for i, body in enumerate(tweet_bodies)
    ]
  else:
    tweets = [
      f"$1 = ₺{usd_try:.2f} 💸{nl}{title}{tweet_bodies[0]}"
    ]
  
  return tweets

# flatten list of lists
def flatten(t):
  return [item for sublist in t for item in sublist]

def get_thread(year, usd_try):

    info    = get_h2_info(year)

    if not info:
      return None

    tweets  = [ get_tweets(i, year, usd_try) for i in info ]

    thread  = flatten(tweets)

    return thread

def log_exists(year):
  f = open('log.json', 'r')
  logs = json.loads(f.read())
  f.close()

  return year in [ yrs['year'] for yrs in logs['done']]

def log_create(year, status_id):
  f = open('log.json', 'r')
  logs = json.loads(f.read())
  f.close()
  f = open('log.json', 'w')
  logs['done'].append({'year':year, 'id':status_id, 'timestamp':int(time.time())})
  f.write(json.dumps(logs, indent=2))
  f.close()

def get_log_for_year(year):
  f = open('log.json', 'r')
  logs = json.loads(f.read())
  f.close()

  for log in logs['done']:
    if log['year'] == year:
      return log
