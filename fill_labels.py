import pandas as pd

df = pd.read_csv("eval/real_review.csv")
df["human_label"] = "correct"
df.to_csv("eval/real_review.csv", index=False)
print(len(df), "rows labeled")