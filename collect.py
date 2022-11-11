#!/usr/bin/env python3
import os
from glob import glob

import yaml
import pandas as pd
import tweepy

consumer_key = ""
consumer_secret = ""
access_token = ""
access_token_secret = ""
user_name = ""

def make_dirs(root_path):
    if not os.path.exists(root_path):
        os.makedirs(root_path)

def load_config():
    with open("config.yml", "r") as yamlfile:
        data = yaml.load(yamlfile, Loader=yaml.FullLoader)
        print("Read successful")
        assert "consumer_key" in data, ""
        assert "consumer_secret" in data, ""
        assert "access_token" in data, ""
        assert "access_token_secret" in data, ""
        assert "user_name" in data, ""
        return data

def get_twitter_api(config):
    assert len(config["consumer_key"]) > 0, ""
    assert len(config["consumer_secret"]) > 0, ""
    assert len(config["access_token"]) > 0, ""
    assert len(config["access_token_secret"]) > 0, ""
    auth = tweepy.OAuthHandler(
        config["consumer_key"],
        config["consumer_secret"]
    )
    auth.set_access_token(
        config["access_token"],
        config["access_token_secret"]
    )

    api = tweepy.API(auth)
    return api


def get_cursor(api, user_name, since_id):
    assert len(user_name) > 0, ""
    return tweepy.Cursor(
        api.user_timeline, screen_name=user_name, count=200, since_id=since_id, tweet_mode="extended"
    ).items()


def main():
    config = load_config()
    root_path = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.join(root_path, "tweets/")
    root_path = os.path.join(root_path, config["user_name"])
    make_dirs(root_path)

    pickle_path = os.path.join(root_path, "pickle/")
    make_dirs(pickle_path)


    # get latest recent
    recents = [x for x in glob(pickle_path + "day-*")]
    if len(recents):
        recents.sort()
        latest = recents[-1]
        print(f"Latest: {latest}")

        data = pd.read_pickle(latest)

        days = {}
        latest_day = (
            pd.to_datetime(data["created_at"], utc=True)
            .apply(lambda x: x.strftime("%Y-%m-%d"))
            .unique()[-1]
        )
        print(f"Latest day: {latest_day}")

        tweet_ids = data["tweet"].apply(lambda x: x.id_str)
        since_id = tweet_ids.max()
    else:
        since_id = None

    api = get_twitter_api(config)
    target_tweets = get_cursor(api, config["user_name"], since_id)

    tweets = []
    for tweet in target_tweets:
        tweets.append(
            {
                "day": pd.to_datetime(tweet.created_at).strftime("%Y-%m-%d"),
                "created_at": tweet.created_at,
                "tweet": tweet,
            }
        )

    if tweets:
        print("{} tweets, latest at {}".format(len(tweets), tweets[0]["created_at"]))
        tweets.reverse()
        tweets = pd.DataFrame(tweets)
        for day in tweets["day"].unique().tolist():
            pickle_file = os.path.join(pickle_path, f"day-{day}.pickle")
            if os.path.exists(pickle_file):
                data = pd.read_pickle(pickle_file)
                data = pd.concat([data, tweets[["created_at", "tweet"]]])
                # uniquify here
                print("Appending to file: {}".format(pickle_file))
                data.to_pickle(pickle_file)
            else:
                print("Saving new file: {}".format(pickle_file))
                tweets[tweets["day"] == day][["created_at", "tweet"]].to_pickle(pickle_file)
    else:
        print("No new tweets")


if __name__ == '__main__':
   main()
