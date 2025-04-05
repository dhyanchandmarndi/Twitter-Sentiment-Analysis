from flask import Flask, request, jsonify, render_template
import requests
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

nltk.download('vader_lexicon', download_dir='/tmp/nltk_data')
if '/tmp/nltk_data' not in nltk.data.path:
    nltk.data.path.append('/tmp/nltk_data')

app.config["MONGO_URI"] = os.getenv("MONGO_DB_URL")
mongo = PyMongo(app)

tweets_collection = mongo.db.tweets

sia = SentimentIntensityAnalyzer()

BEARER_TOKENS = [
    os.getenv("BEARER_TOKENS1"),
    os.getenv("BEARER_TOKENS2"),
    os.getenv("BEARER_TOKENS3")
]

current_key_index = 0

TWITTER_API_URL = "https://api.twitter.com/2/tweets/search/recent"

def get_next_api_key():
    """Cycles through the list of API keys."""
    global current_key_index
    current_key_index = (current_key_index + 1) % len(BEARER_TOKENS)
    return BEARER_TOKENS[current_key_index]

def fetch_tweets(query, max_results=25, next_token=None):
    """Fetch tweets from Twitter API, cycling through keys if rate-limited."""
    global current_key_index
    attempts = 0

    while attempts < len(BEARER_TOKENS):
        headers = {
            "Authorization": f"Bearer {BEARER_TOKENS[current_key_index]}",
            "Content-Type": "application/json"
        }
        
        params = {
            "query": f"{query} -is:retweet -has:links -has:media lang:en",
            "max_results": max_results,
            "tweet.fields": "id,text,created_at"
        }
        
        if next_token:
            params["next_token"] = next_token
        
        response = requests.get(TWITTER_API_URL, headers=headers, params=params)

        if response.status_code == 200:
            response_data = response.json()
            processed_tweets = [
                {"text": tweet.get("text", "").strip()}
                for tweet in response_data.get("data", [])
                if tweet.get("text", "").strip()
            ]
            return processed_tweets

        elif response.status_code == 429:
            print(f"API Key {current_key_index + 1} exceeded rate limit. Switching...")
            get_next_api_key()
            attempts += 1
        else:
            print("Error Fetching Tweets:", response.status_code, response.json())
            return {"error": response.json(), "status_code": response.status_code}
    
    return {"error": "All API keys exhausted", "status_code": 429}

def analyze_sentiment(text):
    sentiment_score = sia.polarity_scores(text)["compound"]
    
    if sentiment_score >= 0.05:
        sentiment_label = "Positive"
    elif sentiment_score <= -0.05:
        sentiment_label = "Negative"
    else:
        sentiment_label = "Neutral"

    return sentiment_score, sentiment_label

@app.route('/')
def index():
    return render_template('index.html')

def analyze_tweets_sentiment(tweets):
    sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}

    for tweet in tweets:
        tweet_text = tweet.get("text", "").strip()
        sentiment_score = sia.polarity_scores(tweet_text)["compound"]
        if sentiment_score >= 0.05:
            sentiment_counts["Positive"] += 1
        elif sentiment_score <= -0.05:
            sentiment_counts["Negative"] += 1
        else:
            sentiment_counts["Neutral"] += 1

    total = sum(sentiment_counts.values())
    if total > 0:
        sentiment_percentages = {
            "Positive": round((sentiment_counts["Positive"] / total) * 100, 2),
            "Negative": round((sentiment_counts["Negative"] / total) * 100, 2),
            "Neutral": round((sentiment_counts["Neutral"] / total) * 100, 2)
        }
    else:
        sentiment_percentages = {"Positive": 0, "Negative": 0, "Neutral": 0}

    return sentiment_percentages



@app.route('/fetch_tweets', methods=['POST'])
def get_tweets():
    hashtag = request.form.get('hashtag', '').strip()
    if not hashtag:
        return jsonify({"error": "Hashtag is required"}), 400
    
    query = f"#{hashtag}"

    
    existing_entry = tweets_collection.find_one({"hashtag": query})

    if existing_entry:
        stored_tweets = existing_entry.get("tweets", [])
        stored_tweet_texts = [tweet["text"] for tweet in stored_tweets if "text" in tweet]        
        sentiment_results = analyze_tweets_sentiment(stored_tweets)
        
    else:
        new_tweets = fetch_tweets(query=query, max_results=25)
        if isinstance(new_tweets, dict) and "error" in new_tweets:
            return jsonify({"error": new_tweets["error"]}), new_tweets.get("status_code", 500)

        if new_tweets:
            tweets_collection.insert_one({"hashtag": query, "tweets": new_tweets})
        stored_tweet_texts = [tweet["text"] for tweet in new_tweets if "text" in tweet] 
        sentiment_results = analyze_tweets_sentiment(new_tweets)
        
    return jsonify({
        "hashtag": hashtag,
        "sentiment_analysis": sentiment_results,
        "tweets": stored_tweet_texts
    })

if __name__ == '__main__':
    app.run(debug=False)
