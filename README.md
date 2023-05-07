# Reddit Imgur Archive

## Disclaimer

This is a personal project and is not affiliated with Imgur or Reddit.

This is a work in progress. I am not a professional programmer, so I am sure there are many things that could be done better. I am open to suggestions.

This was created in haste to automate my own personal archiving of Imgur albums. I am sharing it in case it is useful to anyone else. 

It is not intended to be a polished, user-friendly application. It is a script that I run from the command line and keep changing on the fly. It is not intended to be run by anyone else. 

I am sharing it as-is. I may update it from time to time, but I am not going to provide support for it. If you have questions, feel free to ask, but I may not be able to help you.

**I am not responsible for any damage this script may cause to your computer or your data. Use at your own risk.**
 
## Description

This is a collection of functions cobbled together to collect archived reddit submission data from the [Pushshift API](https://pushshift.io/) and compile a list of Imgur links from the submission data. 

The links can then be downloaded with the script itself, or compiled in '.crawljob' files for use with [JDownloader](http://jdownloader.org/).

## Dependencies

* Python 3.11
* [Wastebin](https://github.com/matze/wastebin) (for uploading lists of urls that would then be crawled by JDownloader)
* [JDownloader2](https://jdownloader.org/jdownloader2) (optional)
  * You can use the docker image https://hub.docker.com/r/jlesage/jdownloader-2/ to run JDownloader in a container.

See [requirements.txt](./requirements.txt) for a list of required Python packages.

 ## Usage


 This is a collection of functions that can be used to collect Imgur links from archived Reddit submissions. It is not intended to be run as a standalone application.

 Check the documentation for each function for more information.

 One way to use this is to create a new Python file and import the functions you want to use. 

 See [main.py](./src/main.py) for an example of how to use the functions.

Then run the file from the command line:

```bash
python main.py
```

**NOTE:** A lot of the paths hardcoded in this repo presume that it will be run in a devcontainer with the following volumes mounted:
 - /app - This is where the code is stored
 - /data - This is where the crawljob files will be stored and any other data that needs to be persisted
 - /folderwatch - This is where JDownloader will watch for crawljob files

The devcontainer configuration is not yet included (I am still working on making a generic one).
 
### Workflow

My workflow while developing this script was:

1. Extract a list of subreddits from my multireddits using the function reddit.get_multireddit_subreddits()
2. Use the function reddit.archive_subreddit to archive the submissions from each subreddit
3. Use the function imgur.write_imgur_urls_from_subreddit_to_file to write the Imgur links to a file
4. Use the function imgur.create_crawljob_file_from_imgur_urls to create a crawljob file for JDownloader2