#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import praw
import ruamel.yaml
from pathlib import Path
import time
from datetime import datetime as dt
import pandas as pd
from argparse import ArgumentParser
import sys
import concurrent.futures

yaml = ruamel.yaml.YAML(typ="safe")
cwd = Path(__file__).parents[0]
final_posts = []
final_cmts = []
checked_posts = []
checked_cmts = []

### Simple classes to store revelent posting info
class LinkPost:
    '''Stores select information about posts.'''
    def __init__(self, post_id, title, url, sub, score, flair, upvote_ratio):
        self.post_id = post_id
        self.title = title
        self.url = url
        self.sub = sub
        self.score = score
        self.flair = flair
        self.upvote_ratio = upvote_ratio

class LinkComment:
    '''Stores select information about comments.'''
    def __init__(self, comment_id, post_id, body, score, sub, post_title, post_flair):
        self.comment_id = comment_id
        self.post_id = post_id
        self.body = body
        self.sub = sub
        self.score = score
        self.post_title = post_title
        self.post_flair = post_flair

### Simple class to to model jobs.
class ScrapeJob:
    '''Stores information about jobs to run.'''
    def __init__(self, jobid, auth, sub, domains, sort, limit):
        self.auth = auth
        self.jobid = jobid
        self.sub = sub
        self.domains = domains
        self.sort = sort
        self.limit = limit

    @property
    def jobnum(self):
        return f"{self.jobid}/{len(jobs)}"

    def __str__(self):
        if self.sort == "hot":
            return f"Job {self.jobnum}, searching the hottest {self.limit} posts from /r/{self.sub} for links to {', '.join(i for i in self.domains)}."
        elif self.sort == "new":
            return f"Job {self.jobnum}, searching the newest {self.limit} posts from /r/{self.sub} for links to {', '.join(i for i in self.domains)}."
        elif self.sort == "controversial":
            return f"Job {self.jobnum}, searching the most controversial {self.limit} posts from /r/{self.sub} for links to {', '.join(i for i in self.domains)}."
        else:
            return f"Job {self.jobnum}, searching the top {self.limit} posts from /r/{self.sub} for links to {', '.join(i for i in self.domains)}."

###########  Start Argument Parsing ###########
parser = ArgumentParser(
    description="A script for grabbing links from Reddit posts/comments.")
parser.add_argument("-s", "--subs", type=str, required=True, help="Subreddit(s) to target. If multiple, separate by comma/no spaces.")
parser.add_argument("-d", "--domains", type=str, required=True, help="Domains to collect URLs from. If multiple, separate by comma/no spaces.")
parser.add_argument("-o","--oauth",type=str, required=True, help="OAuth information, either comma separated values in order (client_id, client_secret, password, username, user_agent) or a path to a key/value file in YAML format.")
parser.add_argument("-p","--path",type=str,required=False, default=cwd, help=f"Path to save output files (Posts_[DATETIME].csv and Comments_[DATETIME].csv). If not is specified, uses source directory.")
parser.add_argument("-l","--limit",type=int,required=False, default=1000, help="Maximum number of posts to search (default = 1000; max = 1000)")
parser.add_argument("-t","--top", type=str, required=False, help="Search top posts. Requires a time: hour, day, week, month, year, all.")
parser.add_argument("--hot", action="store_true", help="Search hot posts.")
parser.add_argument("-n","--new", action="store_true", help="Search new posts.")
parser.add_argument("-c","--controversial", action="store_true", help="Search controversial posts.")
parser.add_argument("-q","--quiet",action="store_true", help="Suppress progress reports until jobs are complete.")
parser.add_argument("-x","--nocomments", action="store_true", help="Do not collect post comments (helps with Reddit's rate limit if you do not need them.)")
args = parser.parse_args()

verbose = not(args.quiet) # Global var used by scrape_links
comments = not(args.nocomments) # Used scrape_links & when deciding whether to write csv for comments.

########### End Argument Parsing ###########

def scrape_links(job,verbose=verbose):
    reddit = praw.Reddit(**job.auth)
    sub = reddit.subreddit(job.sub)
    sort = job.sort
    limit = job.limit
    domains = job.domains
    link_comments = []
    link_posts = []

    ### Grab the correct post list.
    if sort == "hot":
        posts = sub.hot(limit=limit)
    elif sort == "new":
        posts = sub.new(limit=limit)
    elif sort == "controversial":
        posts = sub.controversial(limit=limit)
    else:
        posts = sub.top(time_filter=sort,limit=limit)

    # Counts for number of posts checked, links found and time elapsed.
    check_cnt = 0
    post_cnt = 0
    cmt_cnt = 0
    start = time.time()
    print(f"Started: {job}")
    # Look through posts
    for post in posts:

        if verbose:
            # Check counter and report back.
            if check_cnt == int(limit*(1/4)):
                print(f"{job}\n25% complete in {round((time.time()-start),1)} seconds...{check_cnt} posts checked, found {post_cnt} link posts and {cmt_cnt} top-level comments containing links.\n")
            elif check_cnt == int(limit*(2/4)):
                print(f"{job}\n50% complete in {round((time.time()-start),1)} seconds...{check_cnt} posts checked, found {post_cnt} link posts and {cmt_cnt} top-level comments containing links.\n")
            elif check_cnt == int(limit*(3/4)):
                print(f"{job}\n75% complete in {round((time.time()-start),1)} seconds...{check_cnt} posts checked, found {post_cnt} link posts and {cmt_cnt} top-level comments containing links.\n")
            check_cnt += 1

        if not(post.id in checked_posts):
            checked_posts.append(post.id)
            if post.num_comments > 0 and comments == True:
                post.comments.replace_more(limit=None,threshold=0)
                cmts = post.comments.list()

                for cmt in cmts:
                    body = str(cmt.body)
                    for domain in domains:
                        if domain in body and not(cmt.id in checked_cmts):
                            checked_cmts.append(cmt.id)
                            cmt_cnt += 1
                            lc = LinkComment(
                                comment_id=cmt.id,
                                post_id=post.id,
                                body=body,
                                score=cmt.score,
                                sub=sub.display_name,
                                post_title=post.title,
                                post_flair=post.link_flair_text)
                            link_comments.append(lc)

            if not(post.is_self):
                for domain in domains:
                    if domain in post.url:
                        post_cnt += 1
                        lp = LinkPost( 
                            post_id=post.id,
                            title=post.title,
                            url=post.url,
                            sub=sub.display_name,
                            score=post.score,
                            flair=post.link_flair_text,
                            upvote_ratio=post.upvote_ratio)
                        link_posts.append(lp)
    print(f"{job}\n Completed in {round((time.time()-start),1)} seconds! {check_cnt} posts checked, found {post_cnt} link posts and {cmt_cnt} top-level comments containing links.")
    return [link_posts, link_comments]

if __name__ == "__main__":
    jobs = []
    o_auth = args.oauth
    limit = args.limit
    subs = args.subs.split(",")
    domains = args.domains.split(",")
    sorts = []
    
    if args.new:
        sorts.append("new")
    if args.controversial:
        sorts.append("controversial")
    if args.hot:
        sorts.append("hot")
    if args.top:
        sorts.append(args.top)

    if sorts == []:
        sys.exit("Must provide at least one valid sorting argument. See --help for information.")
    else:
        if "," in o_auth:
            client_id, client_secret, password, uname, uagent = o_auth.split(",")
            api_keys = {"client_id":client_id,"client_secret":client_secret,
            "username":uname,"user_agent":uagent}
        else:
            with open(o_auth) as yml_stream: 
                api_keys = yaml.load(yml_stream)

        id_cnt = 0

        for sub in subs:
            for sort in sorts:
                id_cnt += 1
                sj = ScrapeJob(
                    jobid=id_cnt,
                    auth=api_keys,
                    sub=sub,
                    domains=domains,
                    sort=sort,
                    limit=limit)
                jobs.append(sj)

        print(f"{len(jobs)} scraping job(s) started.")
        print(f"Loading {', '.join('/r/'+i for i in subs)}.")
        print(f"Searching for links from: {', '.join(i for i in domains)}.")
        
        start = time.time()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(scrape_links, jobs)

            for result in results:

                final_posts = final_posts + result[0]
                final_cmts = final_cmts + result[1]
                
        out_path = Path(args.path)
        now = dt.now().strftime("%Y%m%d_%H%M%S")
        post_path = out_path / f"Posts_{now}.csv"
        cmt_path = out_path / f"Comments_{now}.csv"

        print(f"All jobs completed in {round((time.time()-start),1)} seconds!\nFiltering and saving results to {out_path}...")
        
        posts_df = pd.DataFrame([i.__dict__ for i in final_posts])
        post_dups = posts_df.duplicated(subset="post_id", keep="first").sum()
        posts_df.drop_duplicates(subset=["post_id"], keep="first", inplace=True)
        print(f"{post_dups} duplicate posts removed.\nWriting posts to {post_path}.")

        posts_df.to_csv(str(post_path),sep=",")
        if comments == True:
            cmts_df = pd.DataFrame([i.__dict__ for i in final_cmts])
            cmt_dups = cmts_df.duplicated(subset="comment_id", keep="first").sum()
            cmts_df.drop_duplicates(subset=["comment_id"], keep="first", inplace=True)
            print(f"{cmt_dups} duplicate posts removed.\nWriting comments to {cmt_path}")
            cmts_df.to_csv(str(cmt_path),sep=",")
