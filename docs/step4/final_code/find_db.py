import os
import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

url = "https://api.notion.com/v1/search"

payload = {
    "filter": {
        "property": "object",
        "value": "database"
    },
    "page_size": 100
}

response = requests.post(url, headers=headers, json=payload)

print("상태코드:", response.status_code)
print()

data = response.json()

if response.status_code != 200:
    print("오류:")
    print(response.text)
    raise SystemExit

print("[접근 가능한 데이터베이스 목록]")
print()

for item in data["results"]:
    db_id = item["id"]

    title_list = item.get("title", [])
    title = ""

    for t in title_list:
        title += t.get("plain_text", "")

    print("제목:", title)
    print("ID:", db_id.replace("-", ""))
    print("-" * 50)
