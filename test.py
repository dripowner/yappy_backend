import requests
import json
import os
import sys
import typesense
from typesense.collections import Collection
from typesense.exceptions import TypesenseClientError

curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))


client = typesense.Client({
    'api_key': 'xyz',
    'nodes': [{
        'host': 'localhost',
        'port': '8108',
        'protocol': 'http'
    }],
    'connection_timeout_seconds': 2
})

# Drop pre-existing collection if any
try:
    client.collections['videos'].delete()
except Exception as e:
    pass

try:
    client.collections['video_intervals'].delete()
except Exception as e:
    pass
try:
    client.collections['video_intervals_access'].delete()
except Exception as e:
    pass


# Create a collection

def create_collections():
    create_response = client.collections.create({
        "name": "videos",
        "fields": [
            {"name": "url", "type": "string"},
            {"name": "interval_type", "type": "string"},
            {"name": "description", "type": "string"},
            {"name": "content", "type": "string[]"},
            {"name": "start_stop_interval", "type": "string[]"},
        ],
    })

    # create_response = client.collections.create({
    #     "name":  "video_intervals_access",
    #     "fields": [
    #         {"name": "video_id", "type": "string", "reference": "videos.id"},
    #         {"name": "interval_id", "type": "string",
    #             "reference": "video_intervals.id"},
    #     ]
    # })

    # print(create_response)


# create_collections()

# Retrieve the collection we just created


def retrieve_videos_collection():
    retrieve_response = client.collections['videos'].retrieve()
    print("videos", retrieve_response)


# def retrieve_video_intervals_collection():
#     retrieve_response = client.collections['video_intervals'].retrieve()
#     print("video_intervals", retrieve_response)


def retrieve_all_collection():
    # Try retrieving all collections
    retrieve_all_response = client.collections.retrieve()
    print("retrieve_all_response", retrieve_all_response)


retrieve_videos_collection()
# retrieve_video_intervals_collection()
retrieve_all_collection()


# Add a video
def add_videos(data: json):
    collect: Collection = client.collections['videos']
    res = collect.documents.create(data)
    print(res)


# Upsert the same document
def update_videos(data: json):
    collect: Collection = client.collections['videos']
    res = collect.documents.upsert(data)
    print(res)


def import_videos(data: json):
    video_collect: Collection = client.collections['videos']
    res = video_collect.documents.import_(data)
    print(res)


videos = [
    {
        "url": "http://example.com/video1.mp4",
        "description": "Example video 1",
        "content": ["some text", "some ocr text"],
        "interval_type": "video",
        "content": ["content segment 1", "content segment 2"],
        "start_stop_interval": ["00:00:00-00:02:00", "00:05:00-00:07:00"]
    },
    {
        "url": "http://example.com/video1.mp4",
        "description": "Example video 1",
        "content": ["some text", "some ocr text"],
        "interval_type": "video",
        "start_stop_interval": ["00:00:00-00:02:00", "00:05:00-00:07:00"]
    },
    {
        "url": "http://example.com/video2.mp4",
        "description": "Example video 2",
        "content": ["some transcription 1", "some transcription 2"],
        "interval_type": "audio",
        "start_stop_interval": ["00:00:00-00:02:00", "00:05:00-00:07:00"]
    },
]

# add_videos(videos[0])

import_videos(videos)


# def add_video_intervals(data: json):
#     video_intervals_collect: Collection = client.collections['video_intervals']
#     res = video_intervals_collect.documents.create(data)
#     print(res)


# # Upsert the same document
# def update_video_intervals(data: json):
#     video_intervals_collect: Collection = client.collections['video_intervals']
#     res = video_intervals_collect.documents.upsert(data)
#     print(res)


# def import_video_intervals(data: json):
#     video_intervals_collect: Collection = client.collections['video_intervals']
#     print(video_intervals_collect.documents.import_(data))


# video_intervals = [
#     {"id": "1", "videos_id": "1", "interval_type": "video", "start_interval": 0.0,
#         "end_interval": 30.0, },
#     {"id": "2", "videos_id": "1", "interval_type": "audio", "start_interval": 0.0,
#         "end_interval": 32.0, "content": ["some transcription"]},
#     {"id": "3", "videos_id": "2", "interval_type": "llm", "start_interval": 0.0,
#         "end_interval": 30.0, "content":}
# ]


# add_video_intervals(video_intervals[0])
# import_video_intervals(video_intervals)


# TODO: implement it

# # Or update it
# video_updated = {"id": "1", "url": "http://example.com/video1.mp4",
#                  "description": "First updated video"}
# print(client.collections['videos'].documents['1'].update(
#     video_updated))


# Export the documents from a collection
def export_videos():
    video_intervals_collect: Collection = client.collections['video_intervals']
    export_output = video_intervals_collect.documents.export()
    print(export_output)


# Fetch a document in a collection

# print(client.collections['videos'].documents['1'].retrieve())


# Search for documents in a collection
def search(search_word, collect, field):
    videos_collect: Collection = client.collections[collect]

    print("\n\nsearch res", videos_collect.documents.search({
        'q': search_word,
        'query_by': field
    }))


search("2", 'videos', 'description,content')


# # Make multiple search requests at the same time


def print_strings(*args):
    for string in args:
        req_body = {"searches": [
            {
                'collection': 'videos',
                "include_fields": "$video_intervals(*)",
                'q': "*",
            }
        ]}
        res = client.multi_search.perform(
            req_body, {})

        print("\n\nprint_strings ", res)


# print_strings("First")

# # Remove a document from a collection


def remove_document(collection_name, amount):
    print(
        client.collections[f"'{collection_name}'"].documents[f"'{amount}'"].delete())

# # Drop the collection


def drop_collection(collection_name):
    drop_response = client.collections[f"'{collection_name}'"].delete()
    print(drop_response)


# # Import documents into a collection
# def import_docs(docs_to_import, collection_name):
#     docs_to_import = []

#     for exported_doc_str in export_output.split('\n'):
#         docs_to_import.append(json.loads(exported_doc_str))

#     import_results = client.collections[f"'{collection_name}'"].documents.import_(
#         docs_to_import)
#     print(import_results)

    # TODO: Not for now

    # # Upserting documents
    # import_results = client.collections['books'].documents.import_(docs_to_import, {
    #     'action': 'upsert',
    #     'return_id': True
    # })
    # print(import_results)

    # # Schema change: add optional field
    # schema_change = {"fields": [
    #     {"name": "in_stock", "optional": True, "type": "bool"}]}
    # print(client.collections['books'].update(schema_change))

    # # Update value matching a filter
    # updated_doc = {'publication_year': 2009}
    # print(client.collections['books'].documents.update(
    #     updated_doc, {'filter_by': 'publication_year: 2008'}))

    # # Drop the field
    # schema_change = {"fields": [{"name": "in_stock", "drop": True}]}
    # print(client.collections['books'].update(schema_change))

    # # Deleting documents matching a filter query
    # print(client.collections['books'].documents.delete(
    #     {'filter_by': 'ratings_count: 4780653'}))

    # # Try importing empty list
    # try:
    #     import_results = client.collections['books'].documents.import_(
    #         [], {"action": "upsert"})
    #     print(import_results)
    # except TypesenseClientError as e:
    #     print("Detected import of empty document list.")
