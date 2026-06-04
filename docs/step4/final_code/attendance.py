import os, re, requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("NOTION_TOKEN")
DB_IDS = os.getenv("NOTION_DATABASE_IDS").split(",")
REQUIRED = int(os.getenv("REQUIRED"))

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

rows = []

for db_id in DB_IDS:
    db_id = db_id.strip()
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    res = requests.post(url, headers=headers)
    data = res.json()

    if res.status_code != 200:
        print("읽기 실패:", db_id)
        print(data)
        continue

    for page in data["results"]:
        props = page["properties"]
        name = props["이름"]["title"][0]["plain_text"].strip()

        count = 0
        for col, prop in props.items():
            is_day = re.fullmatch(r"(월|화|수|목|금|토|일)(A|B|C)?", col)
            is_extra = ("청소" in col) or ("노션" in col)

            if (is_day or is_extra) and prop["type"] == "checkbox" and prop["checkbox"]:
                count += 1

        rows.append([name, count])

df = pd.DataFrame(rows, columns=["이름", "출석횟수"])

result = df.groupby("이름")["출석횟수"].sum().reset_index()
result["부족"] = result["출석횟수"].apply(lambda x: max(REQUIRED - x, 0))
result["초과(횟수)"] = result["출석횟수"].apply(lambda x: max(x - REQUIRED, 0))
result = result.rename(columns={"출석횟수": "총출석"})
result = result.sort_values("이름").reset_index(drop=True)
result.insert(0, "번호", range(1, len(result) + 1))

print(result.to_string(index=False))

warning = result[result["부족"] >= 2]

with open("경고공지.txt", "w", encoding="utf-8") as f:
    f.write("📌 출석 현황 안내\n\n")
    f.write(f"기준 출석 횟수는 {REQUIRED}회입니다.\n\n")

    if len(warning) == 0:
        f.write("현재 경고 대상자는 없습니다.\n")
    else:
        f.write("[경고 대상자]\n")
        for _, row in warning.iterrows():
            f.write(f'- {row["이름"]}: 부족 {int(row["부족"])}회\n')

result.to_excel("출석결과.xlsx", index=False)


#html 만들기
result.to_excel("출석결과.xlsx", index=False)
# 부족 횟수에 따라 상태를 표시한다.
# 부족 0회: 정상, 부족 1회: 주의, 부족 2회 이상: 경고
result["상태"] = result["부족"].apply(
    lambda x: "정상" if x == 0 else ("주의" if x == 1 else "경고")
)

# HTML에 표시할 표를 만든다.
html_table = result.to_html(index=False, classes="attendance-table")

# HTML 파일 생성
with open("출석현황.html", "w", encoding="utf-8") as f:
    f.write(f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>천차 Garage 출석 현황</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            background-color: #f7f7f7;
        }}

        h1 {{
            text-align: center;
            color: #222;
        }}

        .summary {{
            text-align: center;
            margin-bottom: 25px;
            font-size: 18px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            background-color: white;
        }}

        th, td {{
            border: 1px solid #ddd;
            padding: 10px;
            text-align: center;
        }}

        th {{
            background-color: #333;
            color: white;
        }}

        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}

        .notice {{
            margin-top: 25px;
            padding: 15px;
            background-color: #fff3cd;
            border: 1px solid #ffeeba;
        }}
    </style>
</head>
<body>
    <h1>🏎️ 천차 Garage 출석 현황 🏎️</h1>

    <div class="summary">
        기준 출석 횟수: <strong>{REQUIRED}회</strong>
    </div>

    {html_table}

    <div class="notice">
        <strong>상태 기준</strong><br>
        정상: 부족 0회<br>
        주의: 부족 1회<br>
        경고: 부족 2회 이상
    </div>
</body>
</html>
""")
    
print("\n저장 완료: 출석결과.xlsx, 경고공지.txt, 출석현황.html")
