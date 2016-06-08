# TweetsListener
<p><b>TweetsListener.py</b> provides classes to perform tweets collection and sentiment analysis

<p>There are several classes based on <b>StreamListener</b> from <b>tweepy</b>
<ol>
<li><b>TweetsListener</b> is a base class to listen tweets only and stop listening when a specific number of tweets collected or time listening is out.
If both parameters are 0 then it can run forever.
<li><b>TWeetSentimentAnalyzed</b> analyzes the tweet emotions based on emoticons in the tweet if any  or applies NLP procedures from <b>TextBlob
</b> package to perform sentiment analysis
<li><b>TWeetsToFile</b> saves collected tweets in a csv file. In addition to the limit number of tweets or maximum time  collection reached,
the collection of tweets can be stopped when the file reaches a limit. The class can split the data in several files,
based on the tweets number or an individual file size.
<li>In addition to the tweet itself, <b>TWeetsCoordinatesToFile</b>  saves GEO info
    in a separate file. "_geo_" is added to the file name
    The GEO file is in csv format, many-to-one relations to the tweets file
    All files total size is taken into account to stop tweets collection at file_size_limit
    Only tweets file is splitted in multiply files
<li><b>TWeets</b> class inherits   TWeetsCoordinatesToFile and TWeetSentimentAnalyzed methods. It saves the tweet, it's sentiments in a csv file and
    the coordinates in a separate file
<li><b>TWeetsTotals</b> saves only total sentiments daily in a csv file. There is also hourly data but they are overwritten
</ol>

<img src="https://raw.githubusercontent.com/KaterynaD/TweetsListener/master/TweetsListener%20Classes.png">
<p>The script has a usage example of the classes
<p>To run the script you need to have a Twitter Developer Account.
<p>The usage example expects the account details and other parameters in a project resources yaml-formatted file.

<p>To collect tweets, use the following command, where search_term is your search term and ProjectResources.yml is optional, project resources file in yaml format.
If it is not provided, ProjectResources.yml is used by default
<p><center><b>python TweetsListener.py search_term ProjectResources.yml</b></center>
<p>To use a multi-word term, enclose it in quotation marks

