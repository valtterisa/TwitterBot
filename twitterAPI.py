import tweepy
from urllib.request import urlopen
from bs4 import BeautifulSoup

#########################################################################################
# Twitter API setup

# reading keys from file

# open keys.txt file
file = open("/keys.txt","r")
read = file.readlines()

# create new array for elements
modified = []

# read keys from textfile
for line in read:
    modified.append(line.strip())

# keys
api_key = modified[0]
api_key_secret = modified[1]
access_token = modified[2]
access_token_secret = modified[3] 

# basic authentication 
authenticator = tweepy.OAuthHandler(api_key, api_key_secret)
authenticator.set_access_token(access_token, access_token_secret)

api = tweepy.API(authenticator, wait_on_rate_limit = True)

print("auth OK...")
#########################################################################################

# functions

# GET data from Google Finance about indexes
def get_index_data(url):

    print("finding data...")

    # define array for collecting values
    data = []

    # read data from internet
    html = urlopen(url, timeout = 10).read()
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
    return data

# Tweet data
def tweetAll() :

    # URLs for wanted indexes

    # url0 = "https://www.google.com/finance/quote/DAX:INDEXDB"
    url1 =  "https://www.google.com/finance/quote/OMXHPI:INDEXNASDAQ"
    # url3 =
    # url4 =
    # url5 =
    # url6 =
    # url7 =

    # dax_data = get_index_data(url0)[0] + ": " + get_index_data(url0)[1] + " " + get_index_data(url0)[2] 
    omxhpi_data = get_index_data(url1)[0] + ": " + get_index_data(url1)[1] + " " + get_index_data(url1)[2]

    # Posting tweet
    print("updating twitter status...")
    api.update_status(omxhpi_data + "\n" + "#talous")
    print("Status updated!")

tweetAll()
