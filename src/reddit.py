# This project uses Pushshift's API to scrape Reddit data.
# The goal is to extract all the imgur links from a list of subreddits.

# Import libraries
from pmaw import PushshiftAPI
from dotenv import load_dotenv

import datetime
import json
import logging
import os
import logging.handlers
import praw
import getpass

import apprise


load_dotenv()

# Configure logging to log to both the console and a rotating log file named 'log.txt' in the 'Logs' directory
# The log file will be rotated every 10 MB and will keep the 5 most recent logs
# The log file will be encoded in UTF-8

# Create the 'Logs' directory if it doesn't exist
os.makedirs('Logs', exist_ok=True)

# Create the rotating log file handler
log_file_handler = logging.handlers.RotatingFileHandler('Logs/log.txt', 
                                                        maxBytes=10 * 1024 * 1024, 
                                                        backupCount=5000,
                                                        encoding='utf-8')
# Create the console log handler
log_console_handler = logging.StreamHandler()

# Set the log format
log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Set the log file handler format
log_file_handler.setFormatter(log_format)
# Set the console log handler format
log_console_handler.setFormatter(log_format)

# Create the logger
logging.basicConfig(level=logging.INFO, handlers=[log_file_handler, log_console_handler])


# Function to log a message to the console and the log file
def log(message):
    logging.info(message)


CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
USER_AGENT = os.getenv('USER_AGENT')
USERNAME = os.getenv('USERNAME')


# Function to test the Reddit API connection with PRAW
def test_reddit_api():
    # Initialize the Reddit API
    reddit = praw.Reddit(client_id=CLIENT_ID,
                         client_secret=CLIENT_SECRET,
                         user_agent=USER_AGENT)
    # Get the subreddit
    subreddit = reddit.subreddit('all')
    # Get the top 10 posts from the subreddit
    for submission in subreddit.top(limit=10):
        # Print the submission title
        print(submission.title)


# Function to get the subreddits of all the user's multireddits and write them to a text file
def get_multireddit_subreddits():
    # Get the user's password in a secure console prompt
    password = getpass.getpass('Password: ')
    # Initialize the Reddit API
    reddit = praw.Reddit(client_id=CLIENT_ID,
                         client_secret=CLIENT_SECRET,
                         user_agent=USER_AGENT,
                         username=USERNAME,
                         password=password)
    # Get the user's multireddits
    multireddits = reddit.user.multireddits()
    # Write the subreddits to a text file named '{multireddit}_subreddits.txt'
    for multireddit in multireddits:
        # Create the path to the multireddit file relative to the current directory
        multireddit_path = f'./Multireddits/{multireddit}_subreddits.txt'
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(multireddit_path), exist_ok=True)
        # Check if the multireddit has already been archived
        if os.path.exists(multireddit_path):
            log(f'{multireddit} already exists.')
            continue
        # Write the subreddits to the path
        with open(multireddit_path, 'w+') as f:
            for subreddit in multireddit.subreddits:
                f.write(subreddit.display_name + '\n')
        # Print the multireddit path
        log(f'Wrote {multireddit} to {multireddit_path}')


# Function to parse the multireddit subreddits and consolidate them into a single file
# The function checks for duplicate subreddits and only stores a unique list of subreddits
def parse_multireddit_subreddits():
    # Create a set to store the subreddits
    subreddits = set()
    # Get the multireddits
    multireddits = os.listdir('./Multireddits')
    # Iterate through the multireddits
    for multireddit in multireddits:
        # Create the path to the multireddit file relative to the current directory
        multireddit_path = f'./Multireddits/'
        # Traverse the directory tree starting with the multireddit_path and parse all the '*.txt' files
        for root, dirs, files in os.walk(multireddit_path):
            for file in files:
                # Check if the file is a text file
                if file.endswith('.txt'):
                    # Create the path to the file relative to the current directory
                    file_path = os.path.join(root, file)
                    # Open the file
                    with open(file_path, 'r') as f:
                        # Iterate through the lines in the file
                        for line in f:
                            # Add the subreddit to the set
                            subreddits.add(line.strip())
    # Write the subreddits to a text file named 'subreddits.txt'
    with open('./consolidated_subreddits.txt', 'w+') as f:
        for subreddit in subreddits:
            f.write(subreddit + '\n')
    # Print the number of subreddits
    log(f'Parsed {len(subreddits)} subreddits.')


# Function to archive a given subreddit
# The function will get all the submissions from the subreddit in separate requests for each month
# The function will then write each submission to a text file with the path format 'subreddit/YYYY-MM/submission_id.json'
def archive_subreddit(subreddit):
    # Skip if the subreddit folder already exists
    if os.path.exists(f'./Archive/{subreddit}'):
        log(f'r/{subreddit} already exists.')
        return
    log(f'Archiving r/{subreddit}')
    # Initialize the API
    api = PushshiftAPI(
        num_workers=os.cpu_count() * 5,
        file_checkpoint=10,
        # jitter='full'
    )
    # Get the submissions from the subreddit
    submissions = api.search_submissions(subreddit=subreddit,
                                         mem_safe=True,
                                         safe_exit=True)
    # Write the submissions to a json file with the path format 'subreddit/YYYY-MM/YYYY-MM-DD_submission_id.json'
    for submission in submissions:
        # Get the date of the submission
        submission_date = datetime.datetime.fromtimestamp(submission['created_utc'])
        # Get the year and month of the submission
        submission_year = submission_date.strftime('%Y')
        submission_month = submission_date.strftime('%m')
        # Create the path to the submission file relative to the current directory
        submission_path = f'./Archive/{subreddit}/{submission_year}/{submission_month}/' \
                          f'{submission_year}-{submission_month}-{str(submission_date.day).rjust(2, "0")}' \
                          f'_{submission["id"]}.json'
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(submission_path), exist_ok=True)
        # Check if the submission has already been archived
        if os.path.exists(submission_path):
            log(f'Submission {submission["id"]} already exists.')
            continue
        # Write the submission to the path with pretty formatting and create the file if it doesn't exist
        with open(submission_path, 'w+') as f:
            json.dump(submission, f, indent=2)
        # Print the submission path
        log(f'Wrote submission {submission["id"]} to {submission_path}')


def get_imgur_links(subreddit):
    # Initialize the API
    api = PushshiftAPI(file_checkpoint=10)
    # Get the submissions from the subreddit
    submissions = api.search_submissions(subreddit=subreddit, mem_safe=True)
    # Get the imgur links from the submissions
    imgur_links = []
    for submission in submissions:
        # If the url is None, skip it
        if submission['url'] is None:
            continue
        if 'imgur.com' in submission['url']:
            imgur_links.append(submission['url'])
    # Write the imgur links to a text file named 'imgur_links.txt'
    with open(f'{subreddit}_imgur_links.txt', 'w') as f:
        for imgur_link in imgur_links:
            f.write(imgur_link + '\n')
    # Print the number of imgur links found
    print(f'Found {len(imgur_links)} imgur links in r/{subreddit}.')
    return imgur_links


def run():
    # Get the list of subreddits from a text file named 'subreddits.txt'
    with open('consolidated_subreddits.txt', 'r') as f:
        subreddits = f.read().splitlines()
        # print(subreddits)
    # Archive all the subreddits
    for subreddit in subreddits:
        # Archive the subreddit
        archive_subreddit(subreddit)
    # # Get all the imgur links from the subreddits
    # for subreddit in subreddits:
    #     # print(subreddit)
    #     imgur_links = get_imgur_links(subreddit)


if __name__ == '__main__':
    run()
