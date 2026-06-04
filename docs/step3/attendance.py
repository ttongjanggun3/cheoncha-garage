import os, re, requests
import pandas as pd
from dotenv import load_dotenv

# .env 파일에서 Notion 토큰, DB ID 목록, 기준 출석 횟수를 불러온다.
load_dotenv()

TOKEN = os.getenv("NOTION_TOKEN")
DB_IDS = os.getenv("NOTION_DATABASE_IDS").split(",")
REQUIRED = int(os.getenv("REQUIRED"))

# Notion API 요청에 필요한 인증 정보
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

# 각 DB에서 읽어온 [이름, 출석횟수]를 저장할 리스트
rows = []

# 여러 주차의 출석부 DB를 하나씩 읽는다.
for db_id in DB_IDS:
    db_id = db_id.strip()
    url = f"https://api.notion.com/v1/databases/{db_id}/query"

    res = requests.post(url, headers=headers)
    data = res.json()

    # DB ID 오류, 권한 오류 등이 있을 경우 다음 DB로 넘어간다.
    if res.status_code != 200:
        print("읽기 실패:", db_id)
        print(data)
        continue

    # Notion DB의 각 행은 한 사람의 출석 정보이다.
    for page in data["results"]:
        props = page["properties"]
        name = props["이름"]["title"][0]["plain_text"].strip()

        count = 0

        # 각 열을 확인하며 출석으로 인정되는 체크박스를 센다.
        for col, prop in props.items():
            # 월, 화, 금A, 토B 같은 요일/시간대 열
            is_day = re.fullmatch(r"(월|화|수|목|금|토|일)(A|B|C)?", col)

            # 수 청소, 노션 같은 추가 출석 항목
            is_extra = ("청소" in col) or ("노션" in col)

            if (is_day or is_extra) and prop["type"] == "checkbox" and prop["checkbox"]:
                count += 1

        rows.append([name, count])

# 리스트를 표 형태로 변환
df = pd.DataFrame(rows, columns=["이름", "출석횟수"])

# 같은 이름의 출석 횟수를 합산한다.
result = df.groupby("이름")["출석횟수"].sum().reset_index()

# 기준 출석 횟수와 비교해 부족/초과 횟수를 계산한다.
result["부족"] = result["출석횟수"].apply(lambda x: max(REQUIRED - x, 0))
result["초과(횟수)"] = result["출석횟수"].apply(lambda x: max(x - REQUIRED, 0))

# 결과표 정리
result = result.rename(columns={"출석횟수": "총출석"})
result = result.sort_values("이름").reset_index(drop=True)
result.insert(0, "번호", range(1, len(result) + 1))

print(result.to_string(index=False))

# 부족 횟수가 2회 이상이면 경고 대상자로 분류
warning = result[result["부족"] >= 2]

# 공지용 텍스트 파일 생성
with open("경고공지.txt", "w", encoding="utf-8") as f:
    f.write("📌 출석 현황 안내\n\n")
    f.write(f"기준 출석 횟수는 {REQUIRED}회입니다.\n\n")

    if len(warning) == 0:
        f.write("현재 경고 대상자는 없습니다.\n")
    else:
        f.write("[경고 대상자]\n")
        for _, row in warning.iterrows():
            f.write(f'- {row["이름"]}: 부족 {int(row["부족"])}회\n')

# 전체 결과를 엑셀 파일로 저장
result.to_excel("출석결과.xlsx", index=False)

print("\n저장 완료: 출석결과.xlsx, 경고공지.txt")
