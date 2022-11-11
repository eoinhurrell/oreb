# Oreb

"Fish heads?"

In prep for the failwhale.

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
