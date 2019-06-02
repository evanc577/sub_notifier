import http.client, urllib
import time
import logging
import html
import sys
import os
from psaw import PushshiftAPI
import yaml

LOOKBACK = 3600 * 24 # number of seconds back to check
INTERVAL = 10   # number of seconds between checks

# set up logging
if len(sys.argv) == 2:
    logfile = sys.argv[1]
else:
    logfile='log.txt'

logging.basicConfig(level=logging.INFO, filename=logfile, format='%(asctime)s - %(message)s')
logging.getLogger().addHandler(logging.StreamHandler())
logging.info('started script')

# load pushover token and user
try:
    path = os.path.dirname(os.path.realpath(__file__))	
    path = os.path.join(path, 'pushover.yaml')
    with open(path) as f:
        po_config = yaml.safe_load(f)
except IOError:
    logging.error('could not open pushover.yaml')
    sys.exit(1)

# parse pushover config
try:
    token = po_config['token']
    user = po_config['user']
except:
    logging.error('could not parse pushover.yaml')
    sys.exit(1)


try:
    api = PushshiftAPI()
except:
    logging.error('could not connect to Pushshift api')
    sys.exit(1)

seen_ids = set()    # set of seen submissions
prev_epoch = int(time.time())   # time of previous check
    
while True:
    cur_epoch = int(time.time())

    # get submissions
    try:
        submissions = list(api.search_submissions(subreddit='dreamcatcher', after=prev_epoch-LOOKBACK, sort='asc'))
    except:
        logging.error('could not retrieve submissions')
        time.sleep(5)
        continue

    prev_epoch = cur_epoch

    # check submissions
    for s in submissions:
        if s.id in seen_ids:
            continue
        seen_ids.add(s.id)

        # push unseen submissions
        first = True
        while first or response.status != 200:
            first = False
            logging.info('try: %.20s - https://redd.it/%s' % (s.title, s.id))
            attempts = 1
            try:
                conn = http.client.HTTPSConnection("api.pushover.net:443")
                conn.request("POST", "/1/messages.json",
                             urllib.parse.urlencode({
                                 "token": token,
                                 "user": user,
                                 "title": "New post on r/dreamcatcher",
                                 "message": html.unescape(s.title),
                                 "timestamp": s.created_utc,
                                 "url": "https://redd.it/{}".format(s.id),
                                                    }),
                             { "Content-type": "application/x-www-form-urlencoded" })

                # check response
                response = conn.getresponse()
                response.read()
            except:
                logging.error('error sending push notification, attempt %d' % attempts)
                if attempts >= 3:
                    break
                else:
                    attempts += 1
                    continue

            if response.status == 200:  # ok
                logging.info('received response %d ... ok' % (response.status))
                break
            elif 400 <= response.status < 500:  # bad request
                logging.info('received response %d' % (response.status))
                break
            else:   # other error, retry
                logging.info('received response %d' % (response.status))
                sleep(1)
                continue


    time.sleep(INTERVAL)
