import reddit
import imgur
import os

from dotenv import load_dotenv


load_dotenv()


def run_main():
    if "TEST_FILENAME" in os.environ:
        test_filename = os.environ["TEST_FILENAME"]
    else:
        test_filename = "test.txt"
    url_source_folder = "/data/subreddit_links"
    url_source = url_source_folder + "/" + test_filename

    imgur.create_crawlfile_from_text_file(
        url_source,
        output_folder="/data/imgur_links",
        recreate_file=True
    )
    pass


if __name__ == '__main__':
    run_main()
