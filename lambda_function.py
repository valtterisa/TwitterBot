import tweepy
from ratelimit import limits, sleep_and_retry
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import logging
from urllib.request import urlopen
import datetime


# Load environment variables from the .env file
load_dotenv()

client = tweepy.Client(     #Twitter API client
    consumer_key=os.getenv("API_KEY"),
    consumer_secret=os.getenv("API_KEY_SECRET"),
    access_token=os.getenv("ACCESS_TOKEN"),
    access_token_secret=os.getenv("ACCESS_TOKEN_SECRET")
)

print("auth OK...")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

EMERGENCY_FILE_PATH = "tmp/last_index_data.txt"  # Path to file containing last emergency data

# Decorator for rate limiting
@sleep_and_retry
@limits(calls=50, period=900)  # 50 requests every 15 minutes
def make_request(url):      #User-Agent function
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f'API response: {response.status_code}')
    
    return response

def get_last_index_data():   #Get latest index data
    try:
        with open(EMERGENCY_FILE_PATH, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return None

def set_last_index_data(last_index_data):     #Set index status
    with open(f"/{EMERGENCY_FILE_PATH}", "w") as file:
        last_index_data_str = "\n".join(last_index_data)
        file.write(last_index_data)

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
    print("returned data: ",data)
    return data

def tweet_all(data):    #Tweet data
    logger.info("Finding data...")
    # add current date and time (day/month/year) 
    time_now = datetime.datetime.now().strftime("%d/%m/%Y")

    # URLs for wanted indexes

    # url0 = "https://www.google.com/finance/quote/DAX:INDEXDB"
    url1 =  "https://www.google.com/finance/quote/OMXHPI:INDEXNASDAQ" # OMX Helsinki PI
    url2 = "https://www.google.com/finance/quote/FNFIEURPI:INDEXNASDAQ" # First North Finland EUR PI
    url3 = "https://www.google.com/finance/quote/OMXH25:INDEXNASDAQ" # OMX Helsinki 25

    # dax_data = get_index_data(url0)[0] + ": " + get_index_data(url0)[1] + " " + get_index_data(url0)[2] 
    omxhpi_data = get_index_data(url1)[0] + ": " + get_index_data(url1)[1] + " (" + get_index_data(url1)[2] + "%)"
    fnfpi_data = get_index_data(url2)[0] + ": " + get_index_data(url2)[1] + " (" + get_index_data(url2)[2] + "%)"
    omxh25_data = get_index_data(url3)[0] + ": " + get_index_data(url3)[1] + " (" + get_index_data(url3)[2] + "%)"
    tweet = ("Helsingin pörssi " + time_now + "\n" +
                    omxhpi_data + "\n" +
                    omxh25_data + "\n" +
                    fnfpi_data + "\n" +
                    "#talous")

    last_emergency = get_last_index_data()
    

def lambda_handler(event, context):     #Lambda handler
    data = get_index_data(url)

    if data:
        tweet_all(data)

# This block is necessary for local testing (not for AWS Lambda)
if __name__ == "__main__":
    lambda_handler(None, None)