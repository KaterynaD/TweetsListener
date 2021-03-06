#!/usr/bin/python
# -*- coding: utf-8 -*-
import tweepy
from tweepy import StreamListener
import json, datetime, time
import os, sys
import fnmatch
import re
from textblob import TextBlob
"""
TweetsListener.py - 06.07.16 Kate Drogaieva
This module provides classes to perform tweets collection and sentiment analysis
v3 06.07.16
"""
#===============================================================================
class TweetsListener(StreamListener):
    """
        This is a base class to listen tweets only
        and stop listening when a specific number of tweets collected
        or time listening is out
    """
#-------------------------------------------------------------------------------
    def __init__(self,
    api=None,
    search=['None'],
    time_limit=0,
    tweets_limit=0,
    start_time=datetime.datetime.now(),
    start_counter=0
    ):
        """
            search (list) - search term
            time_limit(int) - number of seconds while tweets are listen 0 means forever
            tweets_limit (int) - number of tweets to collect. 0 means no limit
            start_time (datetime) - init data for the start time in a case of listening problem and restarting
            to keep desired time_limit
            start_counter (int) - init data for the tweet counter in a case of listening problem and restarting
            to keep desired tweets_limit
        """
        self.api = api or API()
        self.search=search
        self.start_time=start_time
        self.time_limit=time_limit
        self.tweets_limit=tweets_limit
        self.counter=start_counter
#-------------------------------------------------------------------------------
    def on_data(self, data):
        # The presence of 'in_reply_to_status' indicates a "normal" tweet.
        # The presence of 'delete' indicates a tweet that was deleted after posting.
        if  'in_reply_to_status' in data:
            if self.on_status(data):
                sys.exit(0)
        return
#-------------------------------------------------------------------------------
    def on_status(self, status):
        """
            Collects tweet in an inner data structure,
            checks if there is a time stop tweet collection
        """
        self.save_tweet(self.get_tweet_data(status))
        self.counter+=1
        sys.stdout.flush()
        if ((self.counter>=self.tweets_limit) and (self.tweets_limit>0)):
            return self.on_tweets_limit()

        if (((datetime.datetime.now() - self.start_time).total_seconds()>self.time_limit) and (self.time_limit>0)):
            return self.on_time_limit()

        return False
#-------------------------------------------------------------------------------
    def on_tweets_limit(self):
        """
            When the total tweets number reached the limit
        """
        print
        print "Finished collecting tweets. Total tweets number reached the limit"
        return True
#-------------------------------------------------------------------------------
    def on_time_limit(self):
        """
            When the time to collect tweets is out
        """
        print
        print "Finished collecting tweets. Collection time is over"
        return True
#-------------------------------------------------------------------------------
    def on_error(self, status_code):
        print 'Error: ' + str(status_code)
        print 'Timeout...wait 10 sec'
        if self.time_limit>0:
            self.time_limit+=10
        time.sleep(10)
        return True
#-------------------------------------------------------------------------------
    def on_timeout(self):
        print 'Timeout...wait 10 sec'
        if self.time_limit>0:
            self.time_limit+=10
        time.sleep(10)
        return True
#-------------------------------------------------------------------------------
    def get_tweet_data(self,status):
        """
            Reads the tweet from status XML and
            adds some info in tweet{} dictionary
        """
        tweet={}
        tweet['id']=str(json.dumps(json.loads(status)['id_str']))
        tweet['created']=str(json.dumps(json.loads(status)['created_at']))
        tweet['text']=str(json.dumps(json.loads(status)['text'])).decode('raw-unicode-escape','ignore').encode('utf-8','ignore')
        tweet['retweet_count']=str(json.dumps(json.loads(status)['retweet_count']))
        tweet['favorite_count']=str(json.dumps(json.loads(status)['favorite_count']))
        tweet['lang']=str(json.dumps(json.loads(status)['lang'])).replace('null','')
        place=str(json.dumps(json.loads(status)['place'])).replace('null','')
        tweet['country']='""'
        tweet['city']='""'
        tweet['province']='""'
        tweet['coordinates']=''
        if place:
            tweet['country']=str(json.dumps(json.loads(place)['country'])).decode('raw-unicode-escape','ignore').encode('utf-8','ignore')
            place_type=str(json.dumps(json.loads(place)['place_type']))
            if place_type=='"city"':
                tweet['city']=str(json.dumps(json.loads(place)['name'])).decode('raw-unicode-escape','ignore').encode('utf-8','ignore')
            elif place_type=='"admin"':
                tweet['province']=str(json.dumps(json.loads(place)['name'])).decode('raw-unicode-escape','ignore').encode('utf-8','ignore')
            tweet['coordinates']=json.loads(place)['bounding_box']['coordinates'][0]
        return tweet
#-------------------------------------------------------------------------------
    def save_tweet(self,tweet):
        """
            Should be used to save the tweet from the tweet dictionary
            It just prints dot in the base class
        """
        print '.',
        return
#===============================================================================
class TWeetSentimentAnalyzed(TweetsListener):
    """
        The class analyzes the tweet emotion
        based on emoticons in the tweet if any
        or or applies NLP procedures from textblob package
        to perform sentiment analysis
    """
#-------------------------------------------------------------------------------
    def __init__(self,
    api=None,
    search=['None'],
    time_limit=0,
    tweets_limit=0,
    start_time=datetime.datetime.now(),
    start_counter=0
    ):
        """
            In addition to the base class the constructor
            defines POSITIV, NEGATIVE or other emoticons
        """
        TweetsListener.__init__(self,
        api,
        search,
        time_limit,
        tweets_limit,
        start_time,
        start_counter)
        self.POSITIVE = 'Positive'
        self.NEGATIVE = 'Negative'
        self.NEUTRAL = 'Neutral'
        self.CONFUSED = 'Confused'
        self.emoticons = {self.POSITIVE:'😀|😁|😂|😃|😄|😅|😆|😇|😈|😉|😊|😋|😌|😍|😎|😏|😗|😘|😙|😚|😛|😜|😝|😸|😹|😺|😻|😼|😽',
                     self.NEGATIVE : '😒|😓|😔|😖|😞|😟|😠|😡|😢|😣|😤|😥|😦|😧|😨|😩|😪|😫|😬|😭|😾|😿|😰|😱|🙀',
                     self.NEUTRAL : '😐|😑|😳|😮|😯|😶|😴|😵|😲',
                     self.CONFUSED: '😕'
                     }
#-------------------------------------------------------------------------------
    def get_tweet_data(self,status):
        """
            The same as in the base class plus
            sentiment analysis of the tweet
        """
        tweet=TweetsListener.get_tweet_data(self,status)
        self.sentiment_analysis(tweet)
        return tweet
#-------------------------------------------------------------------------------
    def sentiment_analysis(self,tweet):
        """
            Runs the sentiments analysis based on emoticons in the tweet
            If there are no emoticons or the sentiment is NEUTRAL or CONFUSED
            runs a sentiment analysis from TextBlob package
        """
        tweet['emoticons'] = []
        tweet['sentiments'] = []
        self.sentiment_analysis_by_emoticons(tweet)
        if ((len(tweet['sentiments']) == 0) or (tweet['sentiments'] == self.NEUTRAL) or (tweet['sentiments'] == self.CONFUSED)):
            self.sentiment_analysis_by_text(tweet)
#-------------------------------------------------------------------------------
    def sentiment_analysis_by_emoticons(self,tweet):
        """
            Based on the emoticons set the sentiment for the tweet
        """
        for sentiment, emoticons_icons in self.emoticons.iteritems():
            matched_emoticons = re.findall(emoticons_icons, tweet['text'])
            if len(matched_emoticons) > 0:
                tweet['emoticons'].extend(matched_emoticons)
                tweet['sentiments'].append(sentiment)
        if self.POSITIVE in tweet['sentiments'] and self.NEGATIVE in tweet['sentiments']:
            tweet['sentiments'] = self.CONFUSED
        elif self.POSITIVE in tweet['sentiments']:
            tweet['sentiments'] = self.POSITIVE
        elif self.NEGATIVE in tweet['sentiments']:
            tweet['sentiments'] = self.NEGATIVE
        else:
            tweet['sentiments'] = self.CONFUSED
#-------------------------------------------------------------------------------
    def sentiment_analysis_by_text(self,tweet):
        """
            Set the sentiment of the tweet based on the polarity
            from TextBlob sentiment analysis
        """
        blob = TextBlob(tweet['text'].decode('ascii', errors="replace"))
        sentiment_polarity = blob.sentiment.polarity
        if sentiment_polarity < 0:
            sentiment = self.NEGATIVE
        elif sentiment_polarity <= 0.25:
            sentiment = self.NEUTRAL
        else:
            sentiment = self.POSITIVE
        tweet['sentiments'] = sentiment
#===============================================================================
class TWeetsToFile(TweetsListener):
    """
        The class saves collected tweets in a csv file
    """
#-------------------------------------------------------------------------------
    def __init__(self,
    api=None,
    search=['None'],
    time_limit=0,
    tweets_limit=0,
    start_time=datetime.datetime.now(),
    start_counter=0,
    file_path='.',
    file_name='tweets_',
    file_extension='.csv',
    file_size_limit=0,
    tweets_in_file=0,
    file_size=0
    ):
        """
            file_path (string) - where to save the file_path. Default current directry (.)
            file_name (string) - file name. Default 'tweets_'
            file_extension (string) - file extension. Default '.csv'
            file_size_limit (int) - file size in bytes when the class stops tweets collecting.
            If tweets_in_file or file_size are not 0, the total file size is taken into account
            Default 0, to ignore the parameter
            tweets_in_file (int) - maximum number of tweets in the file. When it's reached the class openes a new file. Default 0, to ignore the parameter
            file_size (int) - maximum current file size in bytes. When it's reached the class openes a new file. Default 0 to ignore the parameter.
        """
        TweetsListener.__init__(self,
        api,
        search,
        time_limit,
        tweets_limit,
        start_time,
        start_counter)
        self.file_path=file_path
        self.file_name=file_name
        self.file_extension=file_extension
        self.tweets_file=self.file_path + self.file_name + self.file_extension
        self.file_size_limit=file_size_limit
        self.tweets_in_file=tweets_in_file
        self.file_size=file_size
        self.file_line_counter=0
        if self.tweets_in_file>0 or self.file_size>0:
           self.split_to_files=True
           self.file_number=0
        else:
           self.split_to_files=False
#-------------------------------------------------------------------------------
    def on_status(self, status):
        """
            saves the tweet and
            compares collected files size to the file_size_limit
        """
        Result=TweetsListener.on_status(self,status)
        if not Result:
            current_files_size=sum(os.path.getsize(self.file_path+f) for f in fnmatch.filter(os.listdir(self.file_path), self.file_name+'*'+self.file_extension))
            if (current_files_size>self.file_size_limit and self.file_size_limit>0):
                    Result=self.on_file_size_limit()
        return Result
#-------------------------------------------------------------------------------
    def on_file_size_limit(self):
        """
            When the total File Size limit was reached
        """
        print
        print "Finished collecting tweets. Total File Size limit was reached"
        return True
#-------------------------------------------------------------------------------
    def on_save_tweet(self):
        """
            When the tweet is saved
            It openes a new file if lemets are reached
        """
        #.......................................................................
        def start_new_file():
            self.file_number+=1
            self.tweets_file=self.file_path + self.file_name +"_part_"+str(self.file_number)+ self.file_extension
            self.file_line_counter=0
            return
        #.......................................................................
        if self.split_to_files:
            current_file_size=os.path.getsize(self.tweets_file)
            if ((current_file_size>self.file_size) and (self.file_size>0)):
                print "Current file size reached the limit. Opening new file..."
                start_new_file()
        if ((self.file_line_counter>self.tweets_in_file) and (self.tweets_in_file>0)):
                print "Number of tweets in the current file reached the limit. Opening new file..."
                start_new_file()
#-------------------------------------------------------------------------------
    def save_tweet(self,tweet):
        """
            Saves the tweet in a csv file
        """
        with open(self.tweets_file, "ab") as output:
            output.write(tweet['id']+','+tweet['created']+','+tweet['text']+','+tweet['retweet_count']+','+tweet['favorite_count']+','+tweet['lang']+','+tweet['country']+','+tweet['city']+','+tweet['province']+'\n')
        self.file_line_counter+=1
        self.on_save_tweet()
#===============================================================================
class TWeetsCoordinatesToFile(TWeetsToFile):
    """
        In addition to the tweet itself, the class saves GEO info
        in a separate file. "_geo_" is added to the file name
        The GEO file is csv, many-to-one relations to the tweets file
        All files total size is taken into account to stop tweets collection at file_size_limit
        Only tweets file are splitted in multiply files
    """
#-------------------------------------------------------------------------------
    def __init__(self,
    api=None,
    search=['None'],
    time_limit=0,
    tweets_limit=0,
    start_time=datetime.datetime.now(),
    start_counter=0,
    file_path='.',
    file_name='tweets_',
    file_extension='.csv',
    file_size_limit=0,
    tweets_in_file=0,
    file_size=0
    ):
        TWeetsToFile.__init__(self,
        api,
        search,
        time_limit,
        tweets_limit,
        start_time,
        start_counter,
        file_path,
        file_name,
        file_extension,
        file_size_limit,
        tweets_in_file,
        file_size)
        self.tweets_geo_file=self.file_path + self.file_name  +"_geo_"+ self.file_extension
#-------------------------------------------------------------------------------
    def save_coordinates(self,tweet):
        """
            Saves coordinates in a file
        """
        if tweet['coordinates']:
            with open(self.tweets_geo_file, "ab") as output:
                i=1
                for c in tweet['coordinates']:
                    output.write(tweet['id']+','+tweet['country']+','+tweet['city']+','+tweet['province']+','+str(i)+', '+str(c[0])+', '+str(c[1])+'\n')
                    i+=1
#-------------------------------------------------------------------------------
    def save_tweet(self,tweet):
        TWeetsToFile.save_tweet(self,tweet)
        self.save_coordinates(tweet)
#===============================================================================
class TWeets(TWeetsCoordinatesToFile,TWeetSentimentAnalyzed):
    """
        The class saves the tweet, it's sentiments in a csv file and
        the coordinates in a separate file
    """
#-------------------------------------------------------------------------------
    def __init__(self,
    api=None,
    search=['None'],
    time_limit=0,
    tweets_limit=0,
    start_time=datetime.datetime.now(),
    start_counter=0,
    file_path='.',
    file_name='tweets_',
    file_extension='.csv',
    file_size_limit=0,
    tweets_in_file=0,
    file_size=0
    ):
        TWeetSentimentAnalyzed.__init__(self,
            api,
            search,
            time_limit,
            tweets_limit,
            start_time,
            start_counter)
        TWeetsCoordinatesToFile.__init__(self,
            api,
            search,
            time_limit,
            tweets_limit,
            start_time,
            start_counter,
            file_path,
            file_name,
            file_extension,
            file_size_limit,
            tweets_in_file,
            file_size)
        if not os.path.isfile(self.tweets_geo_file):
            with open(self.tweets_geo_file, "wb") as output:
                output.write('"Id","Country","City","State","PointOrder","Longitude","Latitude"\n')
        if not os.path.isfile(self.tweets_file):
            with open(self.tweets_file, "wb") as output:
                output.write('"SearchTerm","Id","Created","Retweeted","Favorited","Lang","Country","City","State","Sentiment"\n')

        return
#-------------------------------------------------------------------------------
    def save_tweet(self,tweet):
        with open(self.tweets_file, "ab") as output:
            output.write('"'+search[0]+'",'+tweet['id']+','+tweet['created']+','+tweet['retweet_count']+','+tweet['favorite_count']+','+tweet['lang']+','+tweet['country']+','+tweet['city']+','+tweet['province']+', "'+tweet['sentiments']+'"\n')
        self.file_line_counter+=1
        self.on_save_tweet()
        TWeetsCoordinatesToFile.save_coordinates(self,tweet)
#===============================================================================
class TWeetsTotals(TWeetSentimentAnalyzed):
    """
        The class saves only total sentiments daily in a csv file
        There is also hourly data but they are overwritten
    """
#-------------------------------------------------------------------------------
    def __init__(self,
    api=None,
    search=['None'],
    time_limit=0,
    tweets_limit=0,
    start_time=datetime.datetime.now(),
    start_counter=0,
    start_Positive=0,
    start_Negative=0,
    start_Neutral=0,
    start_Confused=0,
    start_RecordTime=datetime.datetime.now(),
    file_path='.',
    file_name='tweets_',
    file_extension='.csv'
    ):
        """
            start_Positive, start_Negative, start_Neutral, start_Confused (int, default 0),
            start_RecordTime (datetime, now()) are used to init the class in a case
            of unexpected failure and restarting to keep the numbers
        """
        TWeetSentimentAnalyzed.__init__(self,
            api,
            search,
            time_limit,
            tweets_limit,
            start_time,
            start_counter)
        self.Positive_num=start_Positive
        self.Negative_num=start_Negative
        self.Neutral_num=start_Neutral
        self.Confused_num=start_Confused
        self.RecordTime=start_RecordTime
        self.file_path=file_path
        self.file_name=file_name
        self.file_extension=file_extension
        self.totals_file=self.file_path + self.file_name  +"_daily_totals_"+ self.file_extension
        self.current_file=self.file_path + self.file_name  +"_current_"+ self.file_extension
        if not os.path.isfile(self.totals_file):
            with open(self.totals_file, "wb") as output:
                output.write('"SearchTerm", "EndDateTime", "Positive", "Negative", "Neutral", "Confused"\n')

        return
#-------------------------------------------------------------------------------
    def save_tweet(self,tweet):
        """
            Saves the totals daily and intermediate results hourly
        """
        if tweet['sentiments']=='Positive':
            self.Positive_num+=1
        elif tweet['sentiments']=='Negative':
            self.Negative_num+=1
        elif tweet['sentiments']=='Neutral':
            self.Neutral_num+=1
        elif tweet['sentiments']=='Confused':
            self.Confused_num+=1
        with open(self.current_file, "wb") as output:
            output.write('"SearchTerm", "Positive", "Negative", "Neutral", "Confused"\n')
            output.write('"'+search[0]+'", '+str(self.Positive_num)+', '+str(self.Negative_num)+', '+str(self.Neutral_num)+', '+str(self.Confused_num)+'\n')
        if datetime.datetime.now().day<>self.RecordTime.day:
            with open(self.totals_file, "ab") as output:
                output.write('"'+search[0]+'", "'+datetime.datetime.now().strftime("%d-%m-%Y %H:%M")+'", '+str(self.Positive_num)+', '+str(self.Negative_num)+', '+str(self.Neutral_num)+', '+str(self.Confused_num)+'\n')
            self.RecordTime=datetime.datetime.now()
            self.Positive_num=0
            self.Negative_num=0
            self.Neutral_num=0
            self.Confused_num=0
#============= Usage example================================
if __name__ == "__main__":
    import yaml
    try:
        ResourceFile=sys.argv[2]
    except:
        ResourceFile="ProjectResources.yml"
    resources_filepath = os.path.abspath(os.path.expanduser(ResourceFile))
    # Check if the resource file exists.
    if not os.path.exists(resources_filepath):
        sys.exit("ProjectResources.yml file is required to run the application")
    try:
        with open(ResourceFile, "r") as f:
            res = yaml.load(f)
            #data collection params
            time_limit = res["TC"]["time_limit"]
            tweets_num = res["TC"]["tweets_num"]
            file_path = res["TC"]["file_path"]
            file_name_prefix = res["TC"]["file_name_prefix"]
            file_extension =res["TC"]["file_extension"]
            file_size_limit=res["TC"]["file_size_limit"]
            tweets_in_file=res["TC"]["tweets_in_file"]
            file_size=res["TC"]["file_size"]
            # authentication params
            consumer_key = res["TwitterParams"]["OAuthConsKey"]
            consumer_secret = res["TwitterParams"]["OAuthConsSecret"]
            access_token = res["TwitterParams"]["OAuthToken"]
            access_token_secret = res["TwitterParams"]["OAuthTokenSecret"]
    except KeyError or IOError:
        sys.exit("Wrong parameters")

    # OAuth via tweepy
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)

    search = [sys.argv[1].decode('utf-8')]
    file_name = file_name_prefix+search[0]

    start_time=datetime.datetime.now()
    start_counter=0

    start_Positive=0
    start_Negative=0
    start_Neutral=0
    start_Confused=0
    start_RecordTime=datetime.datetime.now()
    #for testing
    #listener=TWeetsTotals(api, search,time_limit,tweets_num,start_time,start_counter,start_Positive,start_Negative,start_Neutral,start_Confused,start_RecordTime,file_path,file_name,file_extension)
    #stream = tweepy.Stream(auth, listener)
    #stream.filter(track=search, languages=['en'])
    #listener = TWeets(api, search,time_limit,tweets_num,start_time,start_counter,file_path,file_name,file_extension,file_size_limit,tweets_in_file,file_size)
    #listener = TWeetSentimentAnalyzed(api, search,time_limit,tweets_num,start_time,start_counter)
    #stream = tweepy.Stream(auth, listener)
    #stream.filter(track=search)
    #to run the script forever in prod
    while True:
        try:
            listener=TWeetsTotals(api, search,time_limit,tweets_num,start_time,start_counter,start_Positive,start_Negative,start_Neutral,start_Confused,start_RecordTime,file_path,file_name,file_extension)
            #listener = TweetsListener(api, search,time_limit,tweets_num,start_time,start_counter)
            #listener = TWeetsToFile(api, search,time_limit,tweets_num,start_time,start_counter,file_path,file_name,file_extension,file_size_limit,tweets_in_file,file_size)
            #listener = TWeetsCoordinatesToFile(api, search,time_limit,tweets_num,start_time,start_counter,file_path,file_name,file_extension,file_size_limit,tweets_in_file,file_size)
            #listener = TWeets(api, search,time_limit,tweets_num,start_time,start_counter,file_path,file_name,file_extension,file_size_limit,tweets_in_file,file_size)
            stream = tweepy.Stream(auth, listener)
            display_time_limit=int(round(listener.time_limit -((datetime.datetime.now() - listener.start_time).total_seconds())))
            display_tweets_limit = int(listener.tweets_limit - listener.counter)
            if listener.time_limit==0 and listener.tweets_limit>0:
                print "Collecting "+str(display_tweets_limit)+" tweets regarding "+search[0]
            elif listener.time_limit>0 and listener.tweets_limit==0:
                print "Collecting  tweets regarding "+search[0] +" Please wait no more then "+str(display_time_limit)+" sec"
            elif listener.time_limit==0 and listener.tweets_limit==0:
                print "Collecting  tweets regarding "+search[0] +" Click Ctrl+C to stop the programm"
            else:
                print "Collecting "+str(display_tweets_limit)+" tweets regarding "+search[0] +" Please wait no more then "+str(display_time_limit)+" sec"
            #stream.filter(track=search, languages=['en'],async=True)
            if file_size_limit>0:
                print "Collection stops when the total files size with tweets is more then "+str(int(file_size_limit/1024))+"Kb"
            stream.filter(track=search, languages=['en'])
        except Exception, e:
            print "An error occurred: ", e
            print "Restart in 10 sec..."
            start_time=listener.start_time
            start_counter=listener.counter
            time_limit=listener.time_limit
            if listener.__class__.__name__=='TWeetsTotals':
                start_Positive=listener.Positive_num
                start_Negative=listener.Negative_num
                start_Neutral=listener.Neutral_num
                start_Confused=listener.Confused_num
                start_RecordTime=listener.RecordTime

            stream.disconnect()
            if time_limit>0:
                time_limit+=10
            time.sleep(10)
