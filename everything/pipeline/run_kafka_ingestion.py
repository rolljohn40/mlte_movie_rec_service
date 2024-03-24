import argparse
import logging
# from .ingest_kafka.ingest_kafka import create_kafka_consumer_earliest_latest, read_from_kafka
from everything.pipeline.ingest_kafka.ingest_kafka import *

parser = argparse.ArgumentParser(description="Begin digest from kafka")
# parser.add_argument('arg1', type=str, help="address to kafka stream like 'localhost:9092")
parser.add_argument('arg1', type=str, help="earliest or latest offset")

# handles processing from kafka, uses modules within .\ingest_kafka for processing
if __name__=='__main__':

    logging.basicConfig(
        format="%(asctime)s (PID %(process)d) [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
        level=logging.INFO,
    )

    args = parser.parse_args()
    
    # todo have to open the ssh connection to kafka first

    # create consumer
    consumer = create_kafka_consumer_earliest_latest(auto_offset_reset=args.arg1)
    # consume stream
    read_from_kafka(consumer= consumer)



