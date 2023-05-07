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
