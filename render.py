#!/usr/bin/env python3
import os
import time
from glob import glob
from pathlib import Path
from string import Template

import yaml
import pandas as pd
from requests_html import HTMLSession, user_agent
import tweepy


headers = {
    "User-Agent": user_agent(),
}

org_tweet = Template(
    """* $when - $tweet_id
$text
   | $screen_name | * $favs | RT $RTs | $source | $sensitive
   | urls: $urls
   | media: $media
"""
)
consumer_key = ""
consumer_secret = ""
access_token = ""
access_token_secret = ""

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


def process_media(media, render_folder):
    media_path = "file:./media/" + str(media["id"]) + ".jpg"
    abs_media_path = render_folder + "/" + str(media["id"]) + ".jpg"

    if not os.path.exists(abs_media_path):
        session = HTMLSession()
        img_resp = session.get(media["media_url"], headers=headers)
        if img_resp.status_code == 200:
            with open(abs_media_path, "wb") as f:
                for chunk in img_resp:
                    f.write(chunk)
        pass
    return "[[{}][{}]]".format(media_path, media_path)


def filter_tweet_urls(urls):
    return [
        x
        for x in urls
        if not x.get("expanded_url", x.get("url", "")).startswith("https://twitter.com")
    ]


def get_tweet_from_url(url):
    tweet_id = url[url.rfind("/") + 1 :]
    return api.get_status(tweet_id)


def format_tweet(tweet, render_folder=None, recur=True):
    full_text = tweet.full_text
    full_text = "\n".join(["    " + x for x in full_text.split("\n")])
    if "retweeted_status" in dir(tweet):
        full_text = "    RT @{}:".format(
            tweet.retweeted_status.user.screen_name,
        )
        quoted = format_tweet(tweet.retweeted_status, render_folder=render_folder)
        quoted = "\n".join(["\t>" + x for x in quoted.split("\n")])
        full_text += "\n" + quoted

    if "quoted_status" in dir(tweet):
        quoted = format_tweet(tweet.quoted_status, render_folder=render_folder)
        quoted = "\n".join(["\t>" + x for x in quoted.split("\n")])
        full_text += "\n" + quoted

    for x in tweet.entities.get("urls", []):
        if x.get("expanded_url", x.get("url", "")).startswith("https://twitter.com"):
            try:
                referenced = get_tweet_from_url(x.get("expanded_url", x.get("url", "")))
                referenced = format_tweet(referenced, render_folder=render_folder)
                referenced = "\n".join(["\t>" + x for x in referenced.split("\n")])
                full_text += "\n" + referenced
            except:
                pass
    sensitive = ""
    try:
        if tweet.possibly_sensitive:
            sensitive = "--X--"
    except:
        pass

    def make_urls(tweet):
        urls = []
        for url_item in filter_tweet_urls(tweet.entities.get("urls", [])):
            url = str(x.get("expanded_url", x.get("url", "")))
            if url.find("youtu") != -1:
                try:
                    session = HTMLSession()
                    resp = session.get(url, headers=headers)
                    # TODO hacky
                    res = resp.text
                    vid = resp.text.find("videoDetail")
                    if vid == -1:
                        raise KeyError
                    vidc = res[vid : vid + 5000]
                    if vidc.find("lengthSeconds") != -1:
                        vidc = (
                            vidc[vidc.find("title") + 8 : vidc.find("lengthSeconds")]
                            .replace("\\", "")
                            .replace('","', "")
                        )
                    else:
                        vidc = (
                            vidc[vidc.find("title") + 8 :]
                            .replace("\\", "")
                            .replace('","', "")
                        )
                    url += " ({})".format(vidc)
                except:
                    pass
            elif url.find("bitchu") != -1:
                try:
                    session = HTMLSession()
                    resp = session.get(url, headers=headers)
                    al = resp.text
                    vidc = al[al.find("<title>") + 7 : al.find("</title>")]
                    url += " ({})".format(vidc)
                except:
                    pass
            urls.append(url)
        return " | ".join(urls)

    return org_tweet.substitute(
        when=tweet.created_at.isoformat(),
        tweet_id=tweet.id_str,
        text=full_text,
        screen_name=tweet.user.screen_name,
        favs=tweet.favorite_count,
        RTs=tweet.retweet_count,
        source=tweet.source,
        sensitive=sensitive,
        urls=make_urls(tweet),
        media=" | ".join(
            [
                process_media(x, render_folder=render_folder)
                for x in tweet.entities.get("media", [])
            ]
        ),
    )


def make_render(api, recent_name, render_name):
    print("Rendering {}".format(recent_name))
    data = pd.read_pickle(recent_name)
    render_folder = render_name.replace("content.txt", "media")
    print("media to:" + render_folder)
    Path(render_folder).mkdir(parents=True, exist_ok=True)

    tweets = data["tweet"].tolist()
    tweets = sorted(tweets, key=lambda x: x.created_at)
    print(" - from {}".format(tweets[0].created_at))
    print(" - to {}".format(tweets[-1].created_at))
    tweets = [format_tweet(tweet, render_folder=render_folder) for tweet in tweets]

    with open(render_name, "w") as fout:
        fout.write("-*-org-*- {}\n".format(recent_name))
        fout.write("".join(tweets))
    print("Rendered {} tweets".format(len(tweets)))


def append_render(api, recent_name, render_name):
    render_folder = render_name.replace("content.txt", "media")
    print("media to:" + render_folder)
    Path(render_folder).mkdir(parents=True, exist_ok=True)

    data = pd.read_pickle(recent_name)
    tweets = data["tweet"].tolist()
    tweets = sorted(tweets, key=lambda x: x.created_at.timestamp())
    tweets.reverse()
    with open(render_name) as fin:
        for line in fin:
            if line.startswith("* "):
                try:
                    tweets.pop()
                except:
                    pass
    if tweets:
        tweets.reverse()
        tweets = [format_tweet(tweet, render_folder=render_folder) for tweet in tweets]
        with open(render_name, "a") as fout:
            fout.write("".join(tweets))
        print("Appended {} tweets".format(len(tweets)))


def main():
    config = load_config()
    root_path = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.join(root_path, "tweets/")
    root_path = os.path.join(root_path, config["user_name"])
    root_pickle_path = os.path.join(root_path, "pickle/")
    root_render_path = os.path.join(root_path, "renders/")

    api = get_twitter_api(config)
    print(root_pickle_path)
    recents = [x for x in glob(root_pickle_path + "day-*")]
    recents.sort()
    # recents = recents[recents.index(root_pickle_path + "day-2022-01-01.pickle") - 1 :]
    # recents = recents[-14:]
    for recent in recents:
        render_name = recent.replace(".pickle", "/content.txt").replace(
            "/pickle/", "/renders/"
        )
        Path(render_name).parent.mkdir(parents=True, exist_ok=True)
        if not os.path.exists(render_name):
            make_render(api, recent, render_name)
            print(render_name)
        else:
            append_render(api, recent, render_name)

if __name__ == '__main__':
    main()
