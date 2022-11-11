# Oreb

"Fish heads?"

In prep for the failwhale.

## To get Twitter API details
 - Go to https://developer.twitter.com and sign up if needed.
 - In Projects & Apps, click Add App, then Create New.
 - Choose Development.
 - Name it whatever you’d like, but oreb would match the repo name.
 - Finish setup. You will be taken to the app’s dashboard.
 - Under Authentication Tokens is a section labeled Access Token and Secret. It should have a little subhed that says For @your_twitter_handle. Click Generate.
 - Copy the API Key and paste it inside the quotes in the config.yml file you made on the line labeled consumer_key. It should look like consumer_key: "what-you-copied".
 - Copy the API Key Secret and paste it inside the quotes next to consumer_secret.
 - Copy the Access Token and paste it inside the quotes next to access_token_key.
 - Copy the Access Token Secret and paste it inside the quotes next to access_token_secret.
## How to use
To begin with you need Python. Probably the easiest way to get set up with Python is to download and install [Anaconda Python](https://www.anaconda.com/) for your OS. 

Download this repo into its own directory (I'll call it <DIRECTORY>)

Open a terminal, run

    cd <DIRECTORY>
    pip install pdm
    pdm install

Now, open the `config.yml` file and input the details of the user whose tweets you want to backup, and the Twitter API details you've created for yourself.

`pdm run collect` collects tweets, and saves them as tweepy objects. They will be stored in `<DIRECTORY>/tweets/<user_name>/pickle`

`pdm run render` renders all the collected tweets in a maybe awkward way, and downloads the media associated with them, if possible. They will be stored in `<DIRECTORY>/tweets/<user_name>/renders`, one folder per day, with each folder containing a `content.txt`, which contains the tweet, and a `media` folder, which contains any images attached to tweets. A known issue is that it only gets the first image uploaded of a group.
