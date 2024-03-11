import base64
import hashlib
import os
import re
import requests
from requests_oauthlib import OAuth2Session
from flask import Flask, redirect, session, request
from urllib.request import urlopen
from bs4 import BeautifulSoup
import datetime

app = Flask(__name__)
app.secret_key = os.urandom(50)


client_id = os.environ.get("CLIENT_ID")
client_secret = os.environ.get("CLIENT_SECRET")
auth_url = "https://twitter.com/i/oauth2/authorize"
token_url = "https://api.twitter.com/2/oauth2/token"
redirect_uri = os.environ.get("REDIRECT_URI")


# Set the scopes
scopes = ["tweet.read", "users.read", "tweet.write", "offline.access"]


# Create a code verifier
code_verifier = base64.urlsafe_b64encode(os.urandom(30)).decode("utf-8")
code_verifier = re.sub("[^a-zA-Z0-9]+", "", code_verifier)

# Create a code challenge
code_challenge = hashlib.sha256(code_verifier.encode("utf-8")).digest()
code_challenge = base64.urlsafe_b64encode(code_challenge).decode("utf-8")
code_challenge = code_challenge.replace("=", "")

def make_token():
    return OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scopes)


# GET data from Google Finance about indexes
def get_index_data(url):

    print("finding data...")

    # define array for collecting values
    data = []

    # read data from internet
    html = urlopen(url, timeout = 20).read()
    soup = BeautifulSoup(html, "html.parser")

    # GET data from specific elements
    points_now = soup.find("div", attrs = {"class" : "YMlKec fxKbKc"}) # get index point data
    points_start = soup.find("div", attrs = {"class" : "P6K39c"}) # get last days closing points
    index_name = soup.find("div", attrs = {"class" : "zzDege"}) # get index name
    
    # converting to float for calculations
    points_now_format = float(points_now.text.replace(",", ""))
    points_start_format = float(points_start.text.replace(",", ""))

    # counting prosentual rise/fall of index 
    prosentual_rise = str("{0:.2f}".format(((points_now_format / points_start_format) - 1) * 100))

    # adding +-sign front of prosentual rise if prosentual_rise is positive
    if (float(prosentual_rise) > 0):
        prosentual_rise = "+" + prosentual_rise

    # append data to array
    data.append(index_name.text)
    data.append(points_now.text)
    data.append(prosentual_rise)

    # return data[]
    print("data: ",data)
    return data

# add current date and time (day/month/year) 
time_now = datetime.datetime.now().strftime("%d/%m/%Y")
# URLs for wanted indexes
# url0 = "https://www.google.com/finance/quote/DAX:INDEXDB"
url1 =  "https://www.google.com/finance/quote/OMXHPI:INDEXNASDAQ" # OMX Helsinki PI
url2 = "https://www.google.com/finance/quote/FNFIEURPI:INDEXNASDAQ" # First North Finland EUR PI
url3 = "https://www.google.com/finance/quote/OMXH25:INDEXNASDAQ" # OMX Helsinki 25
# dax_data = get_index_data(url0)[0] + ": " + get_index_data(url0)[1] + " " + get_index_data(url0)[2] 

# -- HOX HOX -- Save data to variable and use that. Now it makes requests three times per index.

omxhpi_data = get_index_data(url1)[0] + ": " + get_index_data(url1)[1] + " (" + get_index_data(url1)[2] + "%)"
fnfpi_data = get_index_data(url2)[0] + ": " + get_index_data(url2)[1] + " (" + get_index_data(url2)[2] + "%)"
omxh25_data = get_index_data(url3)[0] + ": " + get_index_data(url3)[1] + " (" + get_index_data(url3)[2] + "%)"

# Tweet data
payload = {"text": "Helsingin pörssi " + time_now + "\n" +
                omxhpi_data + "\n" +
                omxh25_data + "\n" +
                fnfpi_data + "\n" +
                "#talous"}

def post_tweet(payload, token):
    print("Tweeting!")
    return requests.request(
        "POST",
        "https://api.twitter.com/2/tweets",
        json=payload,
        headers={
            "Authorization": "Bearer {}".format(token["access_token"]),
            "Content-Type": "application/json",
        },
    )


@app.route("/")
def demo():
    global twitter
    twitter = make_token()
    authorization_url, state = twitter.authorization_url(
        auth_url, code_challenge=code_challenge, code_challenge_method="S256"
    )
    session["oauth_state"] = state
    return redirect(authorization_url)


@app.route("/oauth/callback", methods=["GET"])
def callback():
    code = request.args.get("code")
    token = twitter.fetch_token(
        token_url=token_url,
        client_secret=client_secret,
        code_verifier=code_verifier,
        code=code,
    )
   
    response = post_tweet(payload, token).json()
    return response


if __name__ == "__main__":
    app.run()

    

