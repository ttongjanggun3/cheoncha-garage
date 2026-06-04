import os
import requests
from dotenv import load_dotenv

# .env 파일에 저장된 환경변수를 불러온다.
# 여기서는 Notion API 토큰을 가져오기 위해 사용한다.
load_dotenv()

# .env 파일에서 Notion API 토큰을 가져온다.
NOTION_TOKEN = os.getenv("NOTION_TOKEN")

# Notion API에 요청을 보낼 때 필요한 인증 정보이다.
# Authorization에는 Notion에서 발급받은 토큰을 넣는다.
headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

# Notion의 search API 주소이다.
# 이 API를 이용하면 연결된 페이지나 데이터베이스를 검색할 수 있다.
url = "https://api.notion.com/v1/search"

# 검색 조건을 설정한다.
# object가 database인 것만 찾도록 하여,
# 현재 토큰으로 접근 가능한 데이터베이스 목록만 가져온다.
payload = {
    "filter": {
        "property": "object",
        "value": "database"
    },
    "page_size": 100
}

# Notion API에 데이터베이스 목록을 요청한다.
response = requests.post(url, headers=headers, json=payload)

# 요청이 성공했는지 상태코드를 출력한다.
# 200이면 성공, 401/403/404 등은 오류이다.
print("상태코드:", response.status_code)
print()

# Notion에서 받은 응답을 Python에서 사용할 수 있는 딕셔너리 형태로 바꾼다.
data = response.json()

# 요청이 실패한 경우 오류 내용을 출력하고 프로그램을 종료한다.
if response.status_code != 200:
    print("오류:")
    print(response.text)
    raise SystemExit

print("[접근 가능한 데이터베이스 목록]")
print()

# 검색 결과로 받은 데이터베이스들을 하나씩 확인한다.
for item in data["results"]:
    # 데이터베이스 ID를 가져온다.
    db_id = item["id"]

    # 데이터베이스 제목은 title 리스트 안에 들어 있으므로,
    # plain_text 값만 꺼내서 하나의 문자열로 합친다.
    title_list = item.get("title", [])
    title = ""

    for t in title_list:
        title += t.get("plain_text", "")

    # 사용자가 .env에 넣기 쉽도록 제목과 ID를 출력한다.
    # ID의 하이픈은 제거해서 출력한다.
    print("제목:", title)
    print("ID:", db_id.replace("-", ""))
    print("-" * 50)
