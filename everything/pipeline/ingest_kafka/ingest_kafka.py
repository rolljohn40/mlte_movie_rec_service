from os import path
import sys, os
from datetime import datetime
from json import dumps, loads
from time import sleep
from random import randint
import numpy as np
import logging
#  ssh -L 9092:localhost:9092 tunnel@128.2.204.215 -NT --
from kafka import KafkaConsumer, TopicPartition
from everything.pipeline.ingest_kafka.cleaning.clean_kafka_data import clean_kafka_rating, clean_kafka_recommendation_request, clean_kafka_watch_timestamp, log_unknown_request

# Update this for your own recitation section :)
topic = 'movielog6'

def create_kafka_consumer_earliest_latest(bootstrap_servers=['localhost:9092'], auto_offset_reset='latest', enable_auto_commit=True, auto_commit_interval_ms=1000, topic=topic):
    """
    Create a KafkaConsumer object.

    Parameters:
    - topic (str): The Kafka topic to subscribe to.
    - bootstrap_servers (list): List of Kafka broker addresses. Defaults to ['localhost:9092'].
    - auto_offset_reset (str): Action to take when no initial offset is present or if the current offset does not exist. Defaults to 'latest'. 
        Valid values are 'earliest', 'latest', 'none'.
    - enable_auto_commit (bool): If True, the consumer's offset will be periodically committed in the background. Defaults to True.
    - auto_commit_interval_ms (int): The frequency in milliseconds at which the consumer's offsets are committed. Defaults to 1000.

    Returns:
    - KafkaConsumer: A KafkaConsumer object configured with the specified parameters.
    """
    # this function only inteded for creating consumer from earliest or latest offset
    if auto_offset_reset not in ['earliest','latest']: raise ValueError("auto_offset_reset must be 'earliest' or 'latest'")
    else:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=enable_auto_commit,
            auto_commit_interval_ms=auto_commit_interval_ms
        )
    return consumer

####### currently not implemented, unsure how to consume from both partitions if seeking specific offset
####### default when seeking is to only consume the partition used when seeking
# def get_offset_timestamp_dict(consumer: KafkaConsumer, partitions: )

# def getConsumerPartitions(consumer: KafkaConsumer, topic: str):


# def create_kafka_consumer_from_offset(topic, timestamp: int, bootstrap_servers=['localhost:9092'], auto_offset_reset='latest', enable_auto_commit=True, auto_commit_interval_ms=1000):
#     consumer = KafkaConsumer(
#             topic,
#             bootstrap_servers=bootstrap_servers,
#             auto_offset_reset=auto_offset_reset,
#             enable_auto_commit=enable_auto_commit,
#             auto_commit_interval_ms=auto_commit_interval_ms
#         )
    
#     return consumer
########  

def read_from_kafka(consumer: KafkaConsumer):

    for message in consumer:
        
        # error_message = None
        message_decode = message.value.decode('utf-8')
  
        split_record = message_decode.split(',')
        # check if recommendation request
        if 'recommendation' in message_decode:
            
            # call recommendation cleaning, do we want to store?
            # handles clean, calls module to store
            error_message = clean_kafka_recommendation_request(split_record)
            
            
        elif 'GET /data/' in message_decode:
            
            # call timestamp cleaning
            # handles clean, calls module to store
            error_message = clean_kafka_watch_timestamp(split_record)
            
            
        elif 'GET /rate/' in message_decode:
            
            # call rating cleaning
            # store data in db
            error_message = clean_kafka_rating(split_record)
            
        else:
            # write to log file that request not recognized
            error_message = "request not recongized: " + message_decode
        
        if error_message is not None:
            if 'format' in error_message:
                logging.warning("Data Drift: " + error_message + "," + message_decode)
            elif 'not add' in error_message:
                logging.error('Failed to add in DB: ' + error_message + "," + message_decode)
            else:
                logging.error(f"Error {error_message}: {message_decode}")
  
    