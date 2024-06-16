# Yappy backend

| Поле | Тип | Описание | 
|------------|---------|--------------------------------| 
| id | string | Уникальный идентификатор видео | 
| url | string | URL видео | 
| description | string | Описание видео |

```
curl -X POST 'http://localhost:8108/collections' \
-H 'X-TYPESENSE-API-KEY: ${TYPESENSE_ADMIN_API_KEY}' \
-H 'Content-Type: application/json' \
-d '{
  "name": "videos",
  "fields": [
    {"name": "id", "type": "string"},
    {"name": "url", "type": "string"},
    {"name": "description", "type": "string"}
  ]
}'
```

| Поле | Тип | Описание | 
|-----------------|----------|----------------------------------| 
| video_id | string | Уникальный идентификатор видео (внешний ключ) | 
| interval_type | string | Тип интервала (video, audio, llm)| 
| start_interval| float | Время начала интервала (в секундах) | 
| end_interval | float | Время окончания интервала (в секундах) | 
| content | string[] | Содержимое интервальных данных (caption, ocr, transcription, tags) |




```
curl -X POST 'http://localhost:8108/collections' \
-H 'X-TYPESENSE-API-KEY: ${TYPESENSE_ADMIN_API_KEY}' \
-H 'Content-Type: application/json' \
-d '{
  "name": "video_intervals",
  "fields": [
    {"name": "video_id", "type": "string"},
    {"name": "interval_type", "type": "string"},
    {"name": "start_interval", "type": "float"},
    {"name": "end_interval", "type": "float"},
    {"name": "content", "type": "string[]"}
  ]
}'
```

```
import requests

videos = [
    {"id": "1", "url": "http://example.com/video1.mp4", "description": "First video"},
    {"id": "2", "url": "http://example.com/video2.mp4", "description": "Second video"}
]

headers = {
    'X-TYPESENSE-API-KEY': 'YOUR_API_KEY',
    'Content-Type': 'application/json'
}

response = requests.post(
    'http://localhost:8108/collections/videos/documents/import',
    headers=headers,
    json=videos
)

print(response.status_code, response.json())
```

```
import requests

intervals = [
    {"video_id": "1", "interval_type": "video", "start_interval": 0.0, "end_interval": 30.0, "content": ["some text", "some ocr text"]},
    {"video_id": "1", "interval_type": "audio", "start_interval": 0.0, "end_interval": 32.0, "content": ["some transcription"]},
    {"video_id": "2", "interval_type": "llm", "start_interval": 0.0, "end_interval": 30.0, "content": ["tag1", "tag2"]}
]

headers = {
    'X-TYPESENSE-API-KEY': 'YOUR_API_KEY',
    'Content-Type': 'application/json'
}

response = requests.post(
    'http://localhost:8108/collections/video_intervals/documents/import',
    headers=headers,
    json=intervals
)

print(response.status_code, response.json())
```

```
curl -X POST 'http://localhost:8108/collections/video_intervals/documents/search' \
-H 'X-TYPESENSE-API-KEY: YOUR_API_KEY' \
-H 'Content-Type: application/json' \
-d '{
  "q": "search text",
  "query_by": "content",
  "sort_by": "_text_match:desc",
  "num_typos": 2,
  "per_page": 10
}'
```


```
response_json = {
  "hits": [
    {
      "document": {
        "video_id": "1",
        "start_interval": 0.0,
        "end_interval": 30.0,
        "content": ["some text", "some ocr text"]
      }
    },
    # другие документы
  ]
}

# Получение информации о видео для связывания тайм-кодов с URL
# Это можно сделать один раз для уникальных video_id из ответа поиска
video_info = requests.get(
    'http://localhost:8108/collections/videos/documents',
    headers=headers
).json()

video_dict = {video["id"]: video["url"] for video in video_info}

for hit in response_json["hits"]:
  doc = hit["document"]
  video_id = doc["video_id"]
  start_time = int(doc["start_interval"])
  video_url = video_dict.get(video_id, "#")
  link = f"{video_url}?t={start_time}"
  print(link)  # или сохраните или обработайте ссылку для отображения пользователю

  ```