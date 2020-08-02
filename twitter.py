"""
@author: halowidy
"""

import re
import tweepy
from tweepy import OAuthHandler
import pickle
import csv
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
import nltk
from nltk.tag.perceptron import PerceptronTagger
nltk.download('averaged_perceptron_tagger')

class TwitterClient(object):

    def __init__(self, query, lang='id', retweets_only=False, with_sentiment=False, tweet_mode='extended'):
        # Key dan Token Twitter API
        consumer_key = 'TNmF6yzQUnSuyFmEC6LgWznu0'
        consumer_secret = 'ZaO0cGeeOWf60iiNubcJ9fJVv7D43grn991RrAxOLcCT0Hhulc'
        access_token = '380323583-4YpZE01j42JfOzHD2jhdR9yWaaQNagOL1epYiujM'
        access_token_secret ='58jufIl2imF4nnCq1w8BI2bd8yY5m2cDrvRNYUVlYCY5N'
        # Attempt authentication
        try:
            self.auth = OAuthHandler(consumer_key, consumer_secret)
            self.auth.set_access_token(access_token, access_token_secret)
            self.query = query
            self.lang = lang
            self.retweets_only = retweets_only
            self.with_sentiment = with_sentiment
            self.api = tweepy.API(self.auth, timeout=100)
            self.tweet_count_max = 3
            self.tweet_mode = tweet_mode
        except:
            print("Error: Authentication Failed")

    def set_query(self, query=''):
        self.query = query

    def set_lang(self, lang='id'):
        self.lang = lang

    def set_retweet_checking(self, retweets_only='false'):
        self.retweets_only = retweets_only

    def set_tweet_mode(self, tweet_mode="extended"):
        self.tweet_mode = tweet_mode

    def set_with_sentiment(self, with_sentiment='false'):
        self.with_sentiment = with_sentiment

    def clean_tweet(self, tweet):
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

    def norm_slangword(self,tweet):
        tweet = self.clean_tweet(tweet)
        slangword_kamus = csv.reader(open('files/slangword_list.csv')) #
        slangword_kamus = dict((rows[0],rows[1]) for rows in slangword_kamus)
        for key in slangword_kamus:
            tweet = tweet.replace(key, slangword_kamus[key])
        return tweet

    def norm_stopword(self, tweet):
        tweet = self.norm_slangword(tweet)
        with open('files/stopword_bahasa.txt', "r") as file:
            stopword = file.read().splitlines()
            for word in stopword:
                tweet = tweet.replace(word,"")
            return tweet

    def stemmer(self, tweet):
        tweet = self.norm_stopword(tweet)
        factory = StemmerFactory()
        stemmer = factory.create_stemmer()
        tweet = stemmer.stem(tweet)
        return tweet

    def pos_tagger(self, tweet):
        tweet = self.stemmer(tweet)
        TAGPICKLE='files/averaged_perceptron_tagger_id.pickle'
        tagger = PerceptronTagger(load=TAGPICKLE)
#
        tag_result =tagger.tag(tweet.split())
        tweet= " ".join([x+"_"+y for x,y in tag_result])
        return tweet

    def get_tweet_sentiment(self, tweet):
        tweet = self.pos_tagger(tweet)
        with open('cls tfidf/classifierNB.pickle','rb') as f : clf = pickle.load(f)
        with open('cls tfidf/tfidfmodelNB.pickle','rb') as f : tfidf = pickle.load(f)
        analysis = clf.predict(tfidf.transform([tweet]).toarray())
        if analysis > 0:
            return 'positive'
        elif analysis == 0:
            return 'neutral'
        else:
            return 'negative'

    def get_tweets(self):
        tweets = []

        try:
            recd_tweets = self.api.search(q=self.query,tm=self.tweet_mode,
                                          count=self.tweet_count_max )
            if not recd_tweets:
                pass
            for tweet in recd_tweets:
                parsed_tweet = {}

                parsed_tweet['text'] = tweet.text
                parsed_tweet['user'] = tweet.user.screen_name
                
                if self.with_sentiment == 1:
                    parsed_tweet['sentiment'] = self.get_tweet_sentiment(tweet.text)
                else:
                    parsed_tweet['sentiment'] = 'unavailable'

                if tweet.retweet_count > 0 and self.retweets_only == 1:
                    if parsed_tweet not in tweets:
                        tweets.append(parsed_tweet)
                elif not self.retweets_only:
                    if parsed_tweet not in tweets:
                        tweets.append(parsed_tweet)
            return tweets

        except tweepy.TweepError as e:
            print("Error : " + str(e))
