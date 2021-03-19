# RedditLinkScraper
A small Python tool built using PRAW for collecting links to specified domain names from one or more subreddits.

By default, it will search for comments in any of the returned posts that contained links to the desired domain(s), whether the parent post is a link or not. This can be optionally disabled at the command line (see below).

Note: Reddit enforces rate limits that mean this script will likely scan between 80-100 posts per minute. Authentication can be provided as a .yaml config file (see example) or as a list of comma-separated values at the command-line 

This script opens multiple PRAW instances and makes use of the Python multi-threading module to gain a small performance boost. In my initial testing, this improved post throughput when comment search was left on by approximately 33% from 65 posts/min to 85 posts/min when searching all metrics (hot/top/new/controversial) with a 1000 item limit across two subreddits and two domains (approx 8K posts and tens of thousands of comments).
It also attempts to ensure that it minimizes the number of comments it retrieves from duplicate posts (i.e. in Top and Hot). It attempts to do this across threads but may not always succeed.

Written for Python 3 (3.6 required due to liberal use of fstrings). **Third party modules needed**: praw, ruamel.yaml (can be removed if you do not want to use YAML, comment out 5, 13, 189-191), and pandas. Default modules used: pathlib, time, datetime, argparse, sys, concurrent.futures
<br>
<br>
Output reports the following statistics:

* Posts: post ID, title, url, subreddit, score/upvote ratio (note: these are approximate/obfuscated), post flair.
* Comments: comment ID, body (including Markdown), subreddit, score parent post title/ID

To add details, consult the PRAW documentation for submissions/comments and modify the LinkPost and/or LinkComment class init methods and the instantiation calls in the global method, scrape_links().
<br>
<br>
To use, run in a terminal window: python ./path_to_source/reddit_link_scraper.py

usage: reddit_link_scraper.py [-h] -s list,of,subs -d list,of,domains -o client_id,client_secret,password,username,user_agent [-p PATH] /path/to/save/output/ [-l LIMIT] #of posts to search [--new] [--controversial] [--hot] [--top] [--quiet] [--nocomments]

_A script for grabbing links from Reddit posts/comments._

optional arguments:

<pre>  -h, --help              show this help message and exit
  
  -s SUBS, --subs   Subreddit(s) to target. If multiple, separate by comma/no spaces.
  
  -d DOMAINS, --domains   DOMAINS Domains to collect URLs from. If multiple, separate by comma/no spaces.
                        
  -o OAUTH, --oauth 
                          OAuth information, either comma separated values in order (client_id, client_secret, password, username, user_agent) or a path to a key/value file in YAML format.
                        
  -p PATH, --path PATH    Path to save output files (Posts_[DATETIME].csv and Comments_[DATETIME].csv). If not is specified, uses source directory.
  
  -l LIMIT, --limit       Maximum number of posts to search (default = 1000; max = 1000)
                          
  -n, --new               Search new posts.
  
  -c, --controversial     Search controversial posts.
  
  --hot                   Search hot posts.
  
  -t TOP, --top TOP       Search top posts. Requires a time: hour, day, week, month, year, all.
  
  -q, --quiet             Supress progress reports until jobs are complete.
  
  -x, --nocomments        Do not collect post comments (helps with Reddit's rate limit if you do not need them.)</pre>

