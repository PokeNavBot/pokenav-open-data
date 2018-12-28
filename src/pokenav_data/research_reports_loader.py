import logging
import requests
import time
from datetime import datetime, timedelta
from google.cloud import bigquery
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def get_args():
    from argparse import ArgumentParser
    parser = ArgumentParser(description="Loads the research reports table from the research stream API.")
    parser.add_argument("-v", "--verbose", action="count", help="the logging verbosity (more gives more detail)")
    parser.add_argument("--lookback", default=10, help="Number of minutes to lookback in the stream (default: %(default)s)")
    parser.add_argument("--interval", default=3, help="Time between attempts to pull from the stream (default: %(default)s)")
    parser.add_argument("--endpoint", default="https://api.pokenavbot.com/research/v1/stream", help="The research stream endpoint url (default: %(default)s)")
    parser.add_argument("--dataset-id", default="pokenav", help="Name of the dataset to load into (default: %(default)s)")
    parser.add_argument("--table-id", default="research_reports", help="Name of the table to load into (default: %(default)s)")
    args = parser.parse_args()

    if args.verbose == 1:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(format="%(levelname)s %(asctime)s: %(message)s")
    logger.setLevel(level)

    # connect to bigquery and fetch the table
    args.client = bigquery.Client()
    args.table_ref = args.client.dataset(args.dataset_id).table(args.table_id)
    args.table = args.client.get_table(args.table_ref)

    return args


def fetch_research_reports(endpoint, lookback):
    response = requests.get(endpoint, params=dict(lookback=lookback))
    if response.status_code != 200:
        logger.info('Unable to fetch research stream, received status code: {}'.format(response.status_code))
        return []

    data = response.json()
    results = data.get('results', [])
    next_fragment = data.get('next')
    if next_fragment:
        o = urlparse(endpoint)
        next_url = '{uri.scheme}://{uri.netloc}{fragment}'.format(uri=o, fragment=next_fragment)
        results += fetch_research_reports(next_url, lookback)

    return results


def fetch_and_process_research_reports(args):
    research_reports = fetch_research_reports(args.endpoint, args.lookback)
    row_ids = [report['id'] for report in research_reports]
    logger.info('Read {} records from research stream, processing...'.format(len(research_reports)))
    errors = args.client.insert_rows_json(args.table, research_reports, row_ids=row_ids, skip_invalid_rows=True)
    if errors:
        logger.error('Error: {}'.format(", ".join(errors)))


def main():
    args = get_args()

    logger.debug('Starting consumptions of research stream...')

    while True:
        next_attempt = datetime.utcnow() + timedelta(minutes=3)

        try:
            fetch_and_process_research_reports(args)
        except Exception as ex:
            logger.error('Error: {}'.format(ex))

        time_to_sleep = (next_attempt - datetime.utcnow()).total_seconds()
        if time_to_sleep > 0:
            logger.info('Read research stream, sleeping until {}'.format(next_attempt.isoformat()))
            time.sleep(time_to_sleep)
