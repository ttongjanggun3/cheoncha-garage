import pandas as pd
import re

files = [
    r"C:\Users\김규원\Desktop\대학교\천차많별\천차 출석표\5월 3주차 출석부(5 18~5 24).csv",
    r"C:\Users\김규원\Desktop\대학교\천차많별\천차 출석표\5월 4주차 출석부 (5 25~5 31).csv"
]

checked_values = ["yes", "true", "1", "o", "v", "✓", "checked", "체크", "참", "y", "t"]

all_data = []

for file in files:
    df = pd.read_csv(file)
    df.columns = df.columns.str.strip()
    df["이름"] = df["이름"].astype(str).str.strip()

    attendance_cols = []

    for col in df.columns:
        if re.fullmatch(r"(월|화|수|목|금|토|일)(A|B|C)?", col):
            attendance_cols.append(col)

        elif "청소" in col:
            attendance_cols.append(col)

        elif "노션" in col:
            attendance_cols.append(col)

    print("\n파일:", file)
    print("계산에 사용한 열:", attendance_cols)

    for col in attendance_cols:
        df[col] = (
            df[col]
            .astype(str)
            .str.strip()
            .str.lower()
            .isin(checked_values)
        )

    print(df.loc[df["이름"] == "김규원", attendance_cols])
    df["출석횟수"] = df[attendance_cols].sum(axis=1)

    all_data.append(df[["이름", "출석횟수"]])

total_df = pd.concat(all_data, ignore_index=True)

result = total_df.groupby("이름")["출석횟수"].sum().reset_index()

# 이 부분 바꾸면 됨
required = 6

result["부족"] = result["출석횟수"].apply(lambda x: max(required - x, 0))
result["초과(횟수)"] = result["출석횟수"].apply(lambda x: max(x - required, 0))

# 열 이름 변경
result = result.rename(columns={"출석횟수": "총출석"})

# 경고 대상자 따로 저장: 부족 2회 이상
warning_people = result[result["부족"] >= 2]

# 정렬
result = result.sort_values("이름").reset_index(drop=True)

# 번호 열 추가
result.insert(0, "번호", range(1, len(result) + 1))

# 표 형태로 출력
print(result.to_string(index=False))

# 경고 대상자 출력
print("\n[경고 대상자]")
if len(warning_people) == 0:
    print("경고 대상자가 없습니다.")
else:
    warning_people = warning_people.sort_values("이름")
    for _, row in warning_people.iterrows():
        print(f'{row["이름"]}: 부족 {int(row["부족"])}회')
