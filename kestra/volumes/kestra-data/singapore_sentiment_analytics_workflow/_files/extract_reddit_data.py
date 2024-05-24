import praw
import json
import argparse

class RedditPostDataExtractor:
    def __init__(self):
        self.data = []

    def extract_data(self, hot_posts):
        if hot_posts:
            for post in hot_posts:
                post.comments.replace_more(limit=None)
                # initialise a dictionary to contain the data of the post
                post_data = {}

                # get the relevant post's data and store it inside post_data

                # get the poster's name
                if post.author is not None:
                    post_data['author'] = post.author.name
                else:
                    post_data['author'] = '[deleted]' # if the user was deleted, post.author will return None. This line will catch that scenario and instead provide the value 'deleted'

                # get the unix time in which the post was created
                post_data['unix_time'] = post.created_utc
                post_data['permalink'] = post.permalink
                post_data['score'] = post.score
                post_data['subreddit'] = post.subreddit.display_name
                post_data['post_title'] = post.title
                post_data['body'] = post.selftext

                # get the unique name of the post (name refers to the id of the post prefixed with t3_)
                # t3 represents that it is a post
                post_data['name'] = post.name

                # store the posts data in the dictionary where the name is used as the key
                self.data.append(post_data)

                # extract the comments from the post
                comments = post.comments.list()

                # extract the data in the comments and store them inside the dictionary
                self.extract_comments_data(comments)
        
        return self.data

    def extract_comments_data(self, comments):
        if comments:
            for comment in comments:
                # initialise a dictionary to contain the data of the comment
                comment_data = {}


                # get the relevant post's data and store it inside post_data

                # get the commenter name
                if comment.author is not None:
                    comment_data['author'] = comment.author.name
                else:
                    comment_data['author'] = '[deleted]' # if the user was deleted, comment.author will return None, this line will catch that scenario and instead provide the value 'deleted'

                # get the unix time in which the comment was created
                comment_data['unix_time'] = comment.created_utc
                comment_data['permalink'] = comment.permalink
                comment_data['score'] = comment.score
                comment_data['subreddit'] = comment.subreddit.display_name
                comment_data['post_title'] = comment.submission.title
                comment_data['body'] = comment.body

                # get the unique name of the comment (name refers to the id of the post prefixed with t1_)
                # t1 represents that it is a post
                comment_data['name'] = comment.name

                # store the comment's data in the dictionary where the name is used as the key
                self.data.append(comment_data)

                # extract the comment's replies from the post
                # replies = comment.replies

                # extract the data in the comments and store them inside the dictionary
                # self.extract_comments_data(replies)
        
        return
    
def get_hot_posts(reddit_instance, subreddit_name, limit):
    # Define the subreddit
    subreddit = reddit_instance.subreddit(subreddit_name)

    # Get hot posts from the subreddit
    hot_posts = subreddit.hot(limit=limit)

    # Filter out posts that are not pinned
    filtered_posts = [post for post in hot_posts if not post.stickied]
    return filtered_posts

# initialize Reddit instance
reddit = praw.Reddit(client_id='hM2BAD8XKakgkVdR2V2S-Q',
                     client_secret='dWBfOf7Ed2WxqVavqQIcZ6V72QyBLg',
                     user_agent='Prawlingv1')

# parse the parameters received from workflow
parser = argparse.ArgumentParser(description='Extract parameters from workflow.')
parser.add_argument('--subreddit', help='Name of the subreddit to extract data from')
parser.add_argument('--limit', help='The number of data rows/jsons to extract')
parser.add_argument('--execution_id', help='The execution id of the workflow, used to track the workflow which produced the json file')

args = parser.parse_args()

# choose the subreddit to extract data from
subreddit = args.subreddit
limit = int(args.limit)
execution_id = args.execution_id

# get hot posts from the subreddit
hot_posts = get_hot_posts(reddit, subreddit, limit)

# initialise a reddit data extractor object
data_extractor = RedditPostDataExtractor()

# extract data from the hot posts from r/singapore
data = data_extractor.extract_data(hot_posts)[:10]

file_name = f"/app/storage/singapore_sentiment_analytics_workflow/_files/reddit/in/{execution_id}.json"
with open(file_name, 'w') as f:
    json.dump(data, f)