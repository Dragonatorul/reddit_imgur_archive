import reddit
import imgur
import download
import os

from dotenv import load_dotenv


load_dotenv()


def create_crawl_file():
    if "TEST_FILENAME" in os.environ:
        test_filename = os.environ["TEST_FILENAME"]
    else:
        test_filename = "test.txt"
    url_source_folder = "/data/subreddit_links"
    url_source = url_source_folder + "/" + test_filename

    # create the crawl file for each file in folder url_source_folder
    for filename in os.listdir(url_source_folder):
        imgur.create_crawlfile_from_text_file(
            file_name=url_source_folder + "/" + filename,
            output_folder="./data/crawljobs",
            recreate_file=True
        )
    pass


def test_pyload():
    response = download.test_connection()
    print(response)
    pass


def add_pyload_package_from_file():
    if "TEST_FILE_PATH" in os.environ:
        test_file_path = os.environ["TEST_FILE_PATH"]
    else:
        print("TEST_FILE_PATH environment variable not set")
        return None
    # get the package name from the file name
    package_name = os.path.basename(test_file_path).split(".")[0]

    # get the links from the file
    with open(test_file_path, "r") as f:
        links = f.readlines()
    links = [link.strip() for link in links]

    # add the package
    response = download.add_package(package_name, links)


def validate_imgur_links():
    if "TEST_FILE_PATH" in os.environ:
        test_file_path = os.environ["TEST_FILE_PATH"]
    else:
        print("TEST_FILE_PATH environment variable not set")
        return None
    # get the package name from the file name
    new_file_name = f"{os.path.basename(test_file_path).split('.')[0]}_validated.txt"

    with open(test_file_path, "r") as f:
        for line in f.readlines():
            link = line.strip()
            validated_link = imgur.validate_imgur_url(link)
            print(f"{link} -> {validated_link}")


def run_main():
    # test_pyload()
    # add_pyload_package_from_file()
    validate_imgur_links()
    # link = "https://imgur.com/a/aWY6ljk"
    # print(imgur.validate_imgur_url(link))
    # create_crawl_file()
    pass


if __name__ == '__main__':
    run_main()
