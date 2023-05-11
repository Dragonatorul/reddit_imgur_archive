import os
import json
import urllib.request
import zipfile
from bs4 import BeautifulSoup
import requests

from dotenv import load_dotenv
import httpx
from tqdm import tqdm as tqdm_sync
from tqdm.asyncio import tqdm as tqdm_async
from apprise import Apprise, AppriseAsset, AppriseConfig, NotifyType, NotifyFormat
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright, TimeoutError as PlaywrightAsyncTimeoutError
import playwright


from urllib.parse import urlparse
import asyncio

load_dotenv()


#
# # Function to download file from url
# def download_file(url, file_path):
#     """
#     This function downloads a file from a url and saves it to the specified file path.
#
#     :param url: The url to download the file from
#     :param file_path: The path to save the file to
#     :return: None
#     """
#     # Create a request to the url
#     request = urllib.request.Request(url)
#     # Firefox user agent
#     USER_AGENT = ""
#     # Set the user agent header to the user agent specified in the .env file
#     request.add_header('User-Agent', USER_AGENT)
#     # Open the url
#     with urllib.request.urlopen(request) as response:
#         # Read the response
#         data = response.read()
#         # Write the response to the file
#         with open(file_path, 'wb') as file:
#             file.write(data)


def get_imgur_url(submission_json, filter_moderated=True):
    """
    Get the imgur url from a submission json file

    :param submission_json: The submission json file
    :param filter_moderated: Whether to filter out moderated submissions
    :return: The imgur url
    """
    with open(submission_json) as json_file:
        submission = json.load(json_file)
        if filter_moderated:
            if "removed_by_category" in submission.keys():
                if submission["removed_by_category"] is not None:
                    return None
        if 'domain' in submission.keys() and 'url' in submission.keys():
            if submission['domain'] is not None and submission['url'] is not None:
                if 'imgur' in submission['domain'] and 'imgur' in submission['url']:
                    return submission['url']
    return None


def get_imgur_urls_from_subreddit(subreddit_folder):
    """
    Get all imgur urls from a subreddit folder and return them in a list

    :param subreddit_folder: The folder containing the subreddit json files
    :return: A list of imgur urls
    """
    # Get all json files in the subreddit folder
    json_files = [os.path.join(subreddit_folder, f) for f in os.listdir(subreddit_folder) if f.endswith('.json')]
    # Get all imgur urls from the json files
    imgur_urls = [get_imgur_url(json_file) for json_file in json_files]
    # Remove None values
    imgur_urls = [url for url in imgur_urls if url is not None]
    return imgur_urls


def write_imgur_urls_from_subreddit_to_file(subreddit_folder_path,
                                            output_folder=None,
                                            output_file=None,
                                            recreate_file=False):
    """
    Write all imgur urls from a subreddit folder to a file

    :param subreddit_folder: The folder containing the subreddit json files
    :param output_file: The file to write the imgur urls to
    """
    # If no output file is specified, use the subreddit folder name
    if output_file is None:
        # Get the folder name from the subreddit folder path
        subreddit_folder = subreddit_folder_path.split('/')[-1]
        output_file = subreddit_folder + '.txt'
    # If no output folder is specified, use the current working directory
    if output_folder is None:
        output_folder = os.getcwd()
    # Create the output folder if it does not exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    # Create the output file path
    output_file_path = os.path.join(output_folder, output_file)
    # If the output file already exists, delete it if recreate_file is True
    if recreate_file and os.path.exists(output_file_path):
        os.remove(output_file_path)
    # Get the subreddit name from the subreddit_folder_path
    subreddit_name = subreddit_folder_path.split('/')[-1]
    # Get a list of all the '.json' files in the subreddit folder recursively
    json_files = [os.path.join(root, file) for root, dirs, files in os.walk(subreddit_folder_path) for file in files if
                  file.endswith('.json')]
    for i in tqdm_sync(range(len(json_files)),
                       desc=f'Parsing {subreddit_name} json files',
                       unit='file'):
        # Get the imgur url from the json file
        imgur_url = get_imgur_url(json_files[i])
        if imgur_url is not None:
            # Write the imgur url to the output file
            with open(output_file_path, 'a') as f:
                f.write(imgur_url + '\n')
    # # Traverse the subreddit folder recursively
    # for root, dirs, files in os.walk(subreddit_folder_path):
    #     for file in files:
    #         if file.endswith('.json'):
    #             # Get the imgur url from the json file
    #             imgur_url = get_imgur_url(os.path.join(root, file))
    #             if imgur_url is not None:
    #                 # Write the imgur url to the output file
    #                 with open(output_file_path, 'a') as f:
    #                     f.write(imgur_url + '\n')


def transform_imgur_url_for_download(imgur_url):
    """
    Transform an imgur url to a downloadable url

    :param imgur_url: The imgur url to transform
    :return: The downloadable url
    """
    url_components = urlparse(imgur_url)
    return_val = ""
    match url_components.netloc:
        case 'imgur.com':
            if '.' in url_components.path:
                return_val = f"https://{url_components.netloc}{url_components.path}"
            elif '/a/' in url_components.path:
                return_val = f"https://{url_components.netloc}{url_components.path}/zip"
            elif '/gallery/' in url_components.path:
                print(f"WARNING NOT SUPPORTED: Gallery: {imgur_url}")
                return None
            else:
                return_val = f"https://{url_components.netloc}{url_components.path}.png"
        case 'i.imgur.com':
            return_val = f"https://{url_components.netloc}{url_components.path}"
        case 'm.imgur.com':
            return_val = f"https://i.imgur.com{url_components.path}"
        case _:  # default
            print(f"WARNING NOT SUPPORTED: {imgur_url}")
            return None
    url_components = urlparse(return_val)
    if url_components.path.endswith('.gifv'):
        return_val = return_val.replace('.gifv', '.mp4')
    return return_val


def get_headers():
    
    if "USER_AGENT" in os.environ:
        user_agent = os.environ["USER_AGENT"]
    else:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Sec-GPC": "1",
        "TE": "trailers"
    }
    return headers


def download_imgur_url(file_with_imgur_urls, output_folder, only_validate_urls=False):
    """
    Download a list of imgur urls from a file

    :param file_with_imgur_urls: The file containing the imgur urls
    :param output_folder: The folder to save the downloaded files to
    """
    # Create the output folder if it does not exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    # Read the imgur urls from the file
    with open(file_with_imgur_urls, 'r') as f:
        imgur_urls = f.readlines()
    # Transform the imgur urls to downloadable urls
    imgur_urls = [transform_imgur_url_for_download(imgur_url) for imgur_url in imgur_urls]
    # Remove None values
    imgur_urls = [url for url in imgur_urls if url is not None]
    # Create a list of the filenames
    # If the url ends with /zip, the filename is the id.zip
    # If the url ends with .<ext>, the filename is the id.<ext>
    # If the url ends with nothing, the filename is the id.jpg
    filenames = []
    for imgur_url in imgur_urls:
        if imgur_url.endswith('/zip'):
            filenames.append(imgur_url.split('/')[-2] + '.zip')
        elif '.' in imgur_url.split('/')[-1]:
            filenames.append(imgur_url.split('/')[-1])
        else:
            filenames.append(imgur_url.split('/')[-1] + '.jpg')
    filenames_with_path = [os.path.join(output_folder, filename) for filename in filenames]
    # Create a list of the imgur urls and filenames
    imgur_urls_and_filenames = list(zip(imgur_urls, filenames_with_path))
    # Recursively traverse the output folder and get all the files
    existing_files = []
    for root, dirs, files in os.walk(output_folder):
        for file in files:
            existing_files.append(file)
    # Remove the existing files from the imgur urls and filenames list
    imgur_urls_and_filenames = [imgur_url_and_filename for imgur_url_and_filename in imgur_urls_and_filenames if
                                imgur_url_and_filename[1] not in existing_files]


    async def download(download_url, 
                       file_path, 
                       recursive_step=0, 
                       original_url=None, 
                       write_failed_to_path=None,
                       only_validate_url=False,
                       validated_urls_path=None,
                       sleep=1
                       ):
        """
        Download a file from a url

        The function can also only validate urls, without downloading them
        The validation process checks if the url is redirected and can save the redirected url to a file
        It treats the following status codes as valid:
        200: OK
        301: Moved Permanently
        302: Found
        303: See Other
        307: Temporary Redirect
        308: Permanent Redirect

        It treats the following edge cases:
        - If the request does not receive a valid status code it will treat it as invalid
        - If the request is redirtected to a url that contains the 'download' keyword it will redirect it to the
            url 'https://i.imgur.com/<id>.png' where <id> is the id in the original url
            We presume the original url is in the form of 'https://imgur.com/download/<id>/'
            This is usually the case for albums that contain only one image and which we tried to download as a zip file

        :param download_url: The url to download the file from
        :param file_path: The path to write the file to
        :param recursive_step: The recursive step
        :param original_url: The original url
        :param write_failed_to_path: The path to write the failed urls to
        :param only_validate_url: Only validate the url, do not download
        :param validated_urls_path: The path to write the validated urls to
        :return: None
        """

        headers = get_headers()

        MAX_RECURSIVE_STEP = 10
        SLEEP_TIME = sleep if sleep is not None else 1
        if recursive_step >= MAX_RECURSIVE_STEP - 1:
            if write_failed_to_path is not None:
                # Add the original_url and file_path to a file with a list of imgur urls and filenames failed downloads
                with open(write_failed_to_path, 'a') as f:
                    f.write(f"{original_url},{file_path}\n")
            print(f"WARNING: {original_url} failed to download")
            return
        if recursive_step in range(0, 3) and 'download' in download_url.lower():
            print(f"WARNING: {download_url} contains download")
            imgur_id = download_url.split('/')[-1]
            new_download_url = f"https://i.imgur.com/{imgur_id}.png"
            return await download(new_download_url, file_path, recursive_step + 1, original_url=original_url)
        print(f"Downloading {download_url} to {file_path}")
        # Create a http client session
        async with httpx.AsyncClient(headers=headers) as http:
            async with http.stream(method='GET', url=download_url) as res:
                # If response is 403 and the url contains 'download' wait and try again with the original url
                if res.status_code == 403 and 'download' in download_url.lower():
                    print(f"WARNING: {res.status_code} - {download_url}")
                    await asyncio.sleep(SLEEP_TIME)
                    return await download(original_url, file_path, recursive_step + 1)
                # Follow the redirect if the response is a redirect
                if res.is_redirect:
                    new_download_url = res.headers['Location']
                    if 'removed' in new_download_url.lower():
                        print(f"ERROR: {res.status_code} - {download_url} => {new_download_url}")
                        return None
                    if recursive_step < MAX_RECURSIVE_STEP:
                        return await download(new_download_url,
                                              file_path,
                                              recursive_step + 1,
                                              original_url=download_url)  # Recursively call the download function
                    else:
                        print(f"ERROR: MAX RECURSION {res.status_code} - {download_url} => {new_download_url}")
                        return None
                # Check if the response is successful
                if res.status_code != 200:
                    print(f"ERROR: {res.status_code} - {download_url}")
                    # If the response url contains 'download' wait and try again after 1s
                    if ('download' in res.url.path) and (recursive_step < MAX_RECURSIVE_STEP):
                        await asyncio.sleep(3)
                        return await download(download_url, file_path, recursive_step + 1)
                    return None
                # Get the file size from the response headers
                if 'Content-Length' in res.headers:
                    size = int(res.headers['Content-Length'])
                else:
                    size = 0
                name = file_path.split('/')[-1]
                # Check if the file exists and if the file size is the same
                # If the 'size' is 0, the file size is unknown and the file will be downloaded
                if os.path.exists(file_path) and size != 0 and os.path.getsize(file_path) == size:
                    print(f"SKIP: {name}")
                    return None
                if size == 0 \
                    and os.path.exists(file_path) \
                    and file_path.endswith('.zip') \
                    and zipfile.is_zipfile(file_path):
                    print(f"SKIP: {name}")
                    return None
                # Rate limit the downloads to 1 per second
                await asyncio.sleep(SLEEP_TIME)
                # Write the response to a file
                if not only_validate_url:
                    file_out = open(file_path, 'wb')
                    async for chunk in tqdm_async(iterable=res.aiter_bytes(1),
                                                desc=name, unit='iB',
                                                unit_scale=True,
                                                unit_divisor=1024,
                                                total=size):
                        file_out.write(chunk)
                    file_out.close()
                elif validated_urls_path is not None:
                    with open(validated_urls_path, 'a') as f:
                        f.write(f"{original_url}\n")

    if only_validate_urls:
        # Define validated_urls_path from file_with_imgur_urls
        if file_with_imgur_urls.endswith('.txt'):
            validated_urls_path = file_with_imgur_urls.replace('.txt', '_validated.txt')
        else:
            print(f"ERROR: {file_with_imgur_urls} is not a .txt file")
    # Download the imgur urls and show a progress bar using tqdm
    for i in tqdm_sync(range(len(imgur_urls_and_filenames)), desc='Downloading', unit='file'):
        imgur_url, filename_with_path = imgur_urls_and_filenames[i]
        # Download the imgur url and show a progress bar using tqdm.asyncio or only validate the urls
        asyncio.run(
            download(imgur_url, 
                     filename_with_path, 
                     0, 
                     only_validate_url=only_validate_urls, 
                     validated_urls_path=validated_urls_path))


# def validate_imgur_urls(file_with_imgur_urls, output_folder):
#     """
#     Validate the imgur urls from the file_with_imgur_urls

#     :param file_with_imgur_urls: The file containing the imgur urls
#     :return: None
#     """
#     download_imgur_url( file_with_imgur_urls,
#                         output_folder=output_folder,
#                         only_validate_urls=True)

def get_urls_from_folders(folder_path):
    """
    Get a list of all the imgur urls from the subfolders in the folder_path

    :param folder_path: The path to the folder containing the subfolders
    :return: A list of all the imgur urls from the subfolders in the folder_path
    """
    # Get a list of all the subfolders in the folder_path
    subfolders = [f.path for f in os.scandir(folder_path) if f.is_dir()]
    # write the imgur urls from each subfolder to a file
    for subfolder in tqdm_sync(subfolders, desc='Subfolders', unit='folder'):
        # print(f"Getting imgur urls from {subfolder}")
        write_imgur_urls_from_subreddit_to_file(subfolder,
                                                output_folder='./data/subreddit_links',
                                                recreate_file=False)
    # Notify the user when the script is finished using apprise and Discord webhook from the environment variable DISCORD_WEBHOOK_URL
    if 'DISCORD_WEBHOOK_URL' in os.environ:
        apprise_url = os.environ['DISCORD_WEBHOOK_URL']
        apprise = Apprise()
        apprise.add(AppriseAsset())
        apprise.add(AppriseConfig())
        apprise.add(AppriseConfig(config={'url': apprise_url}))
        apprise.notify(
            body="Finished parsing imgur urls",
            title="Imgur Downloader",
            notify_type=NotifyType.INFO,
            body_format=NotifyFormat.HTML,
            tag="imgur",
            attach=None,
            interpret_escapes=False,
            config=None,
        )


# Wastebin post
# {
#   "text": "<paste content>",
#   "extension": "<file extension, optional>",
#   "expires": <number of seconds from now, optional>,
#   "burn_after_reading": <true/false, optional>
# }
def create_wastebin_post(text,
                         extension=None,
                         expires=None,
                         burn_after_reading=False):
    """
    Create a post on wastebin

    :param text: The text to post on wastebin
    :param extension: The file extension of the text
    :param expires: The number of seconds from now the post will expire
    :param burn_after_reading: If the post should be deleted after reading
    :return: The url to the post
    """
    # Create the post data
    post_data = {
        'text': text,
        'extension': extension,
        'expires': expires,
        'burn_after_reading': burn_after_reading
    }
    if "WASTEBIN_URL" in os.environ:
        wastebin_url = os.environ["WASTEBIN_URL"]
    else:
        print(f"ERROR: WASTEBIN_URL environment variable not set")
    # Create the post request
    r = requests.post(wastebin_url, json=post_data)
    # Check if the post was successful
    if r.status_code == 200:
        return f"{wastebin_url}{r.json()['path']}?fmt=raw"
    else:
        return None


# Function to create jDownloader2 .crawljob files from a list of imgur urls
# Function first posts a list of max 10000 urls to wastebin and then creates a .crawljob file
# .crawljob json file format:
# [{
# "extractPasswords": ["Password1","Password2"],
# "downloadPassword": "123456Test",
# "enabled": "TRUE",
# "text": "http://cdn8.appwork.org/speed.zip",
# "packageName": "MyPackageName",
# "filename": "NewFilename.zip",
# "comment": "SuperUsefulComment",
# "autoConfirm": "TRUE",
# "autoStart": "TRUE",
# "extractAfterDownload": "FALSE",
# "forcedStart": "FALSE",
# "downloadFolder": "C:\\Users\\test\\Downloads",
# "overwritePackagizerEnabled": false
# }]
def create_crawljob_file_from_imgur_urls(imgur_urls,
                                         crawljob_name,
                                         limit=10000,
                                         output_folder='./data/crawljobs',
                                         download_folder=None,
                                         recreate_file=False):
    """
    Create a jDownloader2 .crawljob file from a list of imgur urls

    :param imgur_urls: A list of imgur urls
    :param crawljob_name: The name of the .crawljob file
    :param limit: The maximum number of imgur urls to post to wastebin
    :param output_folder: The folder to save the .crawljob file
    :param download_folder: The download folder to be specified in the .crawljob file and used by jDownloader2
    :param recreate_file: If the .crawljob file should be recreated if it already exists
    :return: None
    """
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    # Create the wastebin post with .txt extension and 1 day expiration
    # The wastebin post will contain the imgur urls separated by a new line
    # If the imgur urls are more than the limit, multiple wastebin posts will be created
    wastebin_urls = []
    for i in range(0, len(imgur_urls), limit):
        wastebin_urls.append(create_wastebin_post('\n'.join(imgur_urls[i:i + limit]),
                                                  expires=604800))
    # Create the .crawljob file
    crawljob_file_path = os.path.join(output_folder, f'{crawljob_name}.crawljob')
    # Check if the file exists and if the file should be recreated
    if os.path.exists(crawljob_file_path) and not recreate_file:
        return None
    # Define a dictionary with the crawljob file data for each wastebin url
    crawljob_data = []
    for wastebin_url in wastebin_urls:
        data_item = {
            "text": wastebin_url,
            "packageName": crawljob_name,
            "comment": f"Created by Imgur Downloader. Part {wastebin_urls.index(wastebin_url) + 1} of {len(wastebin_urls)}",
            "autoConfirm": "TRUE",
            "autoStart": "TRUE",
            "extractAfterDownload": "FALSE",
            "overwritePackagizerEnabled": True,
            "downloadFolder": download_folder if download_folder else "/output/imgur/<jd:packagename>",
            "deepAnalyseEnabled": True,
            "addOfflineLink": False
        }
        crawljob_data.append(data_item)
    # Create the .crawljob file
    with open(crawljob_file_path, 'w') as f:
        f.write(json.dumps(crawljob_data, indent=2))


def create_crawlfile_from_text_file(file_name,
                                    output_folder='./data/crawljobs',
                                    recreate_file=False):
    """
    Create a jDownloader2 .crawljob file from a text file containing imgur urls

    :param file_name: The name of the text file containing imgur urls
    :param output_folder: The folder to save the .crawljob file
    :param recreate_file: If the .crawljob file should be recreated if it already exists
    :return: None
    """
    # Read the file with combined file name and extension 
    with open(file_name, 'r') as f:
        # Read each line from the file and create a list of imgur urls
        imgur_urls = f.readlines()
    # Remove the new line character from each line
    imgur_urls = [url.strip() for url in imgur_urls]
    # Get the crawljob name from the file name without the extension
    crawljob_name = os.path.splitext(os.path.basename(file_name))[0]
    # Create the crawljob file from the imgur urls
    create_crawljob_file_from_imgur_urls(imgur_urls,
                                         crawljob_name=crawljob_name,
                                         output_folder=output_folder,
                                         recreate_file=recreate_file)


async def validate_imgur_url_with_playwright(imgur_url):
    # Use playwright to get the content of the imgur_url
    # Initialize the playwright browser
    # p = sync_playwright().start()
    async with async_playwright() as p:
        # Create a new browser context
        # context = p.firefox.launch_persistent_context(persistentContextDirectory, headless=False, slow_mo=500)
        browser = await p.firefox.launch(headless=True, slow_mo=500)
        context = await browser.new_context()
        # Create a new page
        page = await context.new_page()
        # Connect to the page
        await page.goto(imgur_url)
        # Wait for page to load
        await page.wait_for_load_state()
        # Get the page content
        page_content = await page.content()
        # Parse the content with beautifulsoup
        soup = BeautifulSoup(page_content, 'html.parser')
        button_elements = soup.find_all('div', class_='btn-wall--yes')
        if len(button_elements) > 0:
            await page.get_by_text("Yes, I'm over 18").click()
            await page.wait_for_load_state()
            page_content = await page.content()
            soup = BeautifulSoup(page_content, 'html.parser')
        await browser.close()
        # Check if it contains the class .image-placeholder
        image_elements = soup.find_all('img', class_='image-placeholder')
        if len(image_elements) == 0:
            # TODO: Check if it contains the class .post-image-container
            return None
        elif len(image_elements) == 1:
            new_imgur_url = image_elements[0]['src']
            return new_imgur_url
        elif len(image_elements) > 1:
            # TODO: Deal with multiple images
            imgur_url_list = []
            for element in image_elements:
                imgur_url_list.append(element['src'])
            return imgur_url_list
        else:
            return None

        pass


def validate_imgur_url_extensions(url_components):
    extension = url_components.path.split('.')[-1]
    if extension.lower() in ['jpg', 'jpeg', 'png', 'gif', 'gifv', 'mp4', 'webm', 'webp']:
        # Get the imgur image id from the url
        imgur_id = url_components.path.split('/')[-1].split('.')[0]
        # Switch case based on the extension
        match extension.lower():
            case 'jpg' | 'jpeg' | 'webp':
                return f"https://i.imgur.com/{imgur_id}.png"
            case 'gif' | 'gifv' | 'webm':
                return f"https://i.imgur.com/{imgur_id}.mp4"
            case 'mp4' | 'png':
                return f"https://i.imgur.com/{imgur_id}.{extension.lower()}"
            case _:  # default
                return None
    else:
        return None


def validate_imgur_url_with_playwright_and_validate_extensions(imgur_url):
    new_imgur_url = asyncio.run(validate_imgur_url_with_playwright(imgur_url))
    if new_imgur_url is None:
        return None
    url_components = urlparse(new_imgur_url)
    return validate_imgur_url_extensions(url_components)


def validate_imgur_url(imgur_url):
    url_components = urlparse(imgur_url)
    headers = get_headers()
    if url_components.hostname.lower() in ['imgur.com', 'www.imgur.com', 'i.imgur.com', 'm.imgur.com']:
        if '.' in url_components.path:
            # Get extension from the url
            return validate_imgur_url_extensions(url_components)
        if '/gallery/' in url_components.path:
            return validate_imgur_url_with_playwright_and_validate_extensions(imgur_url)
        r = requests.get(imgur_url + '/zip', allow_redirects=False, headers=headers)
        if r.status_code == 302 or r.status_code == 301:
            redirect_url = r.headers['Location']
            # If the redirect url contains /download/ follow the redirect but don't download the file
            if '/download/' in redirect_url:
                # Get the headers only
                r = requests.get(redirect_url, stream=True, allow_redirects=False, headers=headers)
                if r.status_code == 403:
                    r.close()
                    pass
                else:
                    return f"{imgur_url}/zip" if '/zip' not in imgur_url else imgur_url
        elif r.status_code == 404:
            imgur_id = url_components.path.split('/')[-1]
            new_imgur_url = f"https://i.imgur.com/{imgur_id}.png"
            r = requests.get(new_imgur_url, allow_redirects=False, headers=headers)
            if r.status_code == 200:
                return new_imgur_url
            elif r.status_code == 302 or r.status_code == 301:
                if 'removed' in r.headers['Location'].lower():
                    return None
            elif r.status_code == 404:
                return None
            else:
                return None
        else:
            return None
            # raise Exception(f"ERROR: {r.status_code} - {imgur_url}")
                
        # Use beautifulsoup to parse the html
        r = requests.get(imgur_url, headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        r.close()
        # Find the image element in the html by finding the img element with class .image-placeholder
        image_element = soup.find('img', class_='image-placeholder')
        if image_element:
            imgur_url = image_element['src']
            url_components = urlparse(imgur_url)
        else:
            new_imgur_url = f"https://i.imgur.com/{url_components.path.split('/')[-1]}.png"
            r = requests.get(new_imgur_url, allow_redirects=False, headers=headers)
            if r.status_code == 200:
                return new_imgur_url
            elif '/a/' in url_components.path:
                # Issue a request to download the imgur album page with /zip appended to the url, but don't follow redirects
                # Get the redirect url from the response
                r = requests.get(imgur_url + '/zip', allow_redirects=False, headers=headers)
                if r.status_code == 302 or r.status_code == 301:
                    redirect_url = r.headers['Location']
                    # Split redirect_url into components
                    redirect_url_components = urlparse(redirect_url)
                    # If the redirect url contains /download/ follow the redirect but don't download the file
                    if '/download/' in redirect_url:
                        # Get the headers only
                        r = requests.get(redirect_url, stream=True, allow_redirects=False, headers=headers)
                        if r.status_code == 403:
                            # There is no zip to download, so return a link for png based on the original url
                            # return f"https://i.imgur.com/{url_components.path.split('/')[-1]}.png"
                            return validate_imgur_url_with_playwright_and_validate_extensions(imgur_url)
                        r.close()
                    if redirect_url_components.hostname.lower() == "zip.imgur.com":
                        return f"{imgur_url}/zip"
                r.close()
                return validate_imgur_url_with_playwright_and_validate_extensions(imgur_url)
            else:
                r.close()
                return None
        
    # # Get extension from the url
    # extension = url_components.path.split('.')[-1]
    # if url_components.hostname.lower() == 'i.imgur.com' and extension.lower() in ['jpg', 'jpeg', 'png', 'gif', 'gifv', 'mp4', 'webm', 'webp']:
    #     # Get the imgur image id from the url
    #     imgur_id = url_components.path.split('/')[-1].split('.')[0]
    #     # Switch case based on the extension
    #     match extension.lower():
    #         case 'jpg' | 'jpeg' | 'webp':
    #             return f"https://i.imgur.com/{imgur_id}.png"
    #         case 'gif' | 'gifv' | 'webm':
    #             return f"https://i.imgur.com/{imgur_id}.mp4"
    #         case 'mp4' | 'png':
    #             return f"https://i.imgur.com/{imgur_id}.{extension.lower()}"
    # # Check if /gallery/ is in the url
    # elif '/gallery/' in url_components.path:
    #     return None
    return None
    # elif url_components.hostname.lower() == "imgur.com":
    #     pass
    # else:
    #     pass


def execute_from_command_line():
    ### Use this function to define what you want to do when you run this particular file 
    ### from the command line. This is not good practice, but I don't have time to make it better.
    url_source_folder = "/data/subreddit_links"
    for file_name in os.listdir(url_source_folder):
        create_crawlfile_from_text_file(os.path.join(url_source_folder, file_name),
                                        output_folder='./data/crawljobs',
                                        recreate_file=True)
    pass


if __name__ == '__main__':
    execute_from_command_line()
