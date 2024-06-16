import typesense
from typesense.collections import Collection
import json


class TypesenseService:
    client: typesense.Client

    def __init__(self):

        self.client = typesense.Client({
            'api_key': 'xyz',
            'nodes': [{
                'host': 'typesense',
                'port': '8108',
                'protocol': 'http'
            }],
            'connection_timeout_seconds': 2
        })

    def create_collections(self):
        return self.client.collections.create({
            "name": "videos",
            "fields": [
                {"name": "url", "type": "string"},
                {"name": "interval_type", "type": "string"},
                {"name": "description", "type": "string"},
                {"name": "content", "type": "string[]"},
                {"name": "start_stop_interval", "type": "string[]"},
            ],
        })

    def retrieve_videos_collection(self):
        retrieve_response = self.client.collections['videos'].retrieve()
        print("videos", retrieve_response)
        return retrieve_response

    # Add a video

    def add_videos(self, data: json):
        collect: Collection = self.client.collections['videos']
        res = collect.documents.create(data)
        print(res)

    # Upsert the same document

    def update_videos(self, data: json):
        collect: Collection = self.client.collections['videos']
        res = collect.documents.upsert(data)
        print(res)

    def import_videos(self, data: json):
        video_collect: Collection = self.client.collections['videos']
        res = video_collect.documents.import_(data)
        print(res)

    # Search for documents in a collection
    def search(self, search_word, collect, field):
        videos_collect: Collection = self.client.collections[collect]
        res = videos_collect.documents.search({
            'q': search_word,
            'query_by': field
        })

        print("\n\nsearch res", res)
        return res
