import pandas as pd
import datetime
from crawl_bot_validation import is_google_owned_resource
import tqdm


class CrawlLogAnalyzer:
    """
    Analyze crawl logs to identify trends.
    """

    def __init__(self, log_file_name: str, validators: list[str] = []) -> None:
        self.log_file_name = log_file_name
        # header row is not present in the log file, but uses
        # the following format:
        # regex from https://regex101.com/library/P801k2
        log_file = pd.read_csv(
            log_file_name,
            sep=r'\s(?=(?:[^"]*"[^"]*")*[^"]*$)(?![^\[]*\])',
            header=None,
            usecols=[0, 3, 4, 5, 6, 7, 8],
            engine="python",
        )

        self.log_file = log_file
        labels = [
            "ip",
            "time_local",
            "request",
            "status",
            "body_bytes_sent",
            "http_referer",
            "http_user_agent",
        ]

        # rename columns
        self.log_file.columns = labels

        if "googlebot" in validators:
            print("Filtering out all non-Googlebot IPs...")
            # unique ips where "google" is in the user agent
            unique_ips = self.log_file[
                self.log_file["http_user_agent"].str.contains("Google", na=False)
            ]["ip"].unique()
            # get googlebot ips
            googlebot_ips = [
                ip for ip in tqdm.tqdm(unique_ips) if is_google_owned_resource(ip)
            ]

            # filter out googlebot ips
            self.log_file = self.log_file[~self.log_file["ip"].isin(googlebot_ips)]

        # split up request column into path and protocol
        self.log_file["path"] = self.log_file["request"].apply(
            lambda x: x.split(" ")[1] if len(x.split(" ")) > 1 else x
        )
        self.log_file["protocol"] = self.log_file["request"].apply(
            lambda x: x.split(" ")[2] if len(x.split(" ")) > 2 else x
        )

        # drop the original request column
        self.log_file.drop("request", axis=1, inplace=True)

        # get rid of the first column

    def get_unique(self, col: str) -> list:
        """
        Get the unique values in a column.

        Args:
            col (str): The column to analyze.

        Returns:
            list: A list of unique values in the column.

        Example:
            ```python
            from seotools.logs import CrawLogAnalyzer

            analyzer = CrawlLogAnalyzer("access.log")

            analyzer.get_unique("request")
            ```
        """
        return self.log_file[col].unique()

    def get_count(self, col: str) -> dict:
        """
        Count the number of times a value appears in a column.

        Args:
            col (str): The column to analyze.

        Returns:
            dict: A dictionary of values and the number of times they appear in the column.
        """
        data = self.log_file[col].value_counts().to_dict()

        return {k: v for k, v in data.items() if k != "-"}

    def crawl_frequency_by_url(self, url: str) -> int:
        """
        Find the number of times a URL has been crawled.

        Args:
            url (str): The URL to analyze.

        Returns:
            int: The number of times the URL was crawled.
        """

        return self.log_file[self.log_file[0] == url].shape[0]

    def _get_avg_space_between_crawls(self, crawls_by_date, url):
        # get average space between crawls
        dates = list(crawls_by_date.keys())
        # cast dates to ints 01/Aug/2020

        dates = [datetime.datetime.strptime(date, "%d/%b/%Y") for date in dates]

        # get difference between dates

        diffs = [dates[i] - dates[i - 1] for i in range(1, len(dates))]

        # convert to days
        diffs = [diff.days for diff in diffs]

        # get average
        avg_diff = sum(diffs) / len(diffs)

        # get average daily crawls for the url
        avg_daily_crawls = self.log_file[self.log_file["path"] == url].shape[0] / len(
            dates
        )

        return avg_diff, avg_daily_crawls

    def get_top_urls(self, n: int = 10) -> dict:
        """
        Find the top n most crawled URLs.

        Args:
            n (int): The number of URLs to return.

        Returns:
            dict: A dictionary of URLs and the number of times they were crawled.
        """
        return self.log_file["path"].value_counts().head(n).to_dict()

    def crawl_frequency_aggregate(self, url: str = None, path: str = None) -> dict:
        """
        Find the number of times a URL has been crawled by date.

        Args:
            url (str): The URL to analyze.
            path (str): The path to analyze.

        Returns:
            dict: A dictionary of dates and the number of times the URL was crawled on that date.

        Example:
            ```python
            from seotools.logs import CrawLogAnalyzer

            analyzer = CrawlLogAnalyzer("access.log")

            analyzer.crawl_frequency_aggregate(url="...")
            ```
        """

        crawls_by_date = {}

        if path:
            url = path
        else:
            url = url

        if not path and not url:
            raise Exception("You must provide either a path or a URL.")

        self.log_file["formatted_date"] = self.log_file["time_local"].apply(
            lambda x: x.split(":")[0].replace("[", "")
        )

        print("Getting crawl frequency...")

        for date in tqdm.tqdm(self.log_file["formatted_date"].unique()):
            if url:
                crawls_by_date[date] = self.log_file[
                    (self.log_file["formatted_date"] == date)
                    & (self.log_file["path"] == url)
                ].shape[0]
            else:
                crawls_by_date[date] = self.log_file[
                    self.log_file["formatted_date"] == date
                ].shape[0]

        # order by date
        crawls_by_date = {
            k: v for k, v in sorted(crawls_by_date.items(), key=lambda item: item[0])
        }

        # return how avg. space between crawls
        avg_diff, avg_daily_crawls = self._get_avg_space_between_crawls(
            crawls_by_date, url
        )

        return crawls_by_date, avg_diff, avg_daily_crawls
