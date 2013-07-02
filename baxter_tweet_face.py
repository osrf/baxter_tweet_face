#!/usr/bin/env python
from __future__ import print_function

import os
import urllib

import Image

import cv2
from cv2 import imread

import rospy

from cv_bridge import CvBridge

import sensor_msgs.msg

import twitter

CONSUMER_KEY = "ugNynQImhyBGcLHJAqR3NQ"
CONSUMER_SECRET = "9U6YewqN3NtGrLR6u5XWgAEKRt3VJ7H75DBIvm8XZuY"

MY_TWITTER_CREDS = os.path.expanduser('~/.baxter_tweet_face_credentials')
if not os.path.exists(MY_TWITTER_CREDS):
    twitter.oauth_dance("baxter_tweet_face", CONSUMER_KEY, CONSUMER_SECRET,
                        MY_TWITTER_CREDS)

oauth_token, oauth_secret = twitter.read_token_file(MY_TWITTER_CREDS)

oauth = twitter.OAuth(oauth_token, oauth_secret, CONSUMER_KEY, CONSUMER_SECRET)

ts = twitter.TwitterStream(auth=oauth)

it = ts.statuses.filter(track="#OSRFBaxter")

cv_bridge = CvBridge()

rospy.init_node("baxter_tweet_face", disable_signals=True)
img_pub = rospy.Publisher('/sdk/xdisplay', sensor_msgs.msg.Image, latch=True)
i = 0
for tweet in it:
    print("Received tweet!")
    entities = tweet.get('entities', {})
    urls = entities.get('urls', [])
    url_key = 'expanded_url'
    if not urls:
        urls = entities.get('media', [])
        url_key = 'media_url'
    if urls:
        url = urls[0].get(url_key, None)
        print("There is a url: " + url)
        if url is None:
            print("Could not get expeanded url...")
            continue
        url_ext = url.split('.')[-1]
        print("Looking at extension: " + url_ext)
        if url_ext.lower() not in ['jpeg', 'jpg', 'png']:
            print("Invalid extension, not a supported image.")
            continue
        img_type = 'png' if url_ext.lower() == 'png' else 'jpeg'
        print("Image type is " + img_type)
        print("Attempting to fetch url: " + url)
        image_data = urllib.urlopen(url).read()
        if not os.path.isdir("images"):
            os.makedirs("images")
        image_file_name = os.path.join("images", str(i) + '.' + img_type)
        with open(image_file_name, 'wb') as f:
            i += 1
            f.write(image_data)
        # Frame the image (http://stackoverflow.com/questions/4744372/reducing-the-width-height-of-an-image-to-fit-a-given-aspect-ratio-how-python)
        image = Image.open(image_file_name)
        width = image.size[0]
        height = image.size[1]

        aspect = width / float(height)

        ideal_width = 1024
        ideal_height = 600

        ideal_aspect = ideal_width / float(ideal_height)

        if aspect > ideal_aspect:
            # Then crop the left and right edges:
            new_width = int(ideal_aspect * height)
            offset = (width - new_width) / 2
            resize = (offset, 0, width - offset, height)
        else:
            # ... crop the top and bottom:
            new_height = int(width / ideal_aspect)
            offset = (height - new_height) / 2
            resize = (0, offset, width, height - offset)
        cropped = image.crop(resize).resize((ideal_width, ideal_height), Image.ANTIALIAS)
        os.remove(image_file_name)
        cropped.save(image_file_name)
        # Convert to cv_image
        cv_image = imread(image_file_name)
        cv_image = cv2.cv.fromarray(cv_image)
        img_msg = cv_bridge.cv_to_imgmsg(cv_image)
        print("Publishing the image!")
        img_pub.publish(img_msg)
    else:
        print("No urls in the tweet...")
        print(tweet)
