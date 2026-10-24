# pip install kagglehub pandas
import os, kagglehub, pandas as pd

path = kagglehub.dataset_download("jainamgada45/indian-government-schemes")
for f in os.listdir(path):
    print("FILE:", f)
    if f.endswith(".csv"):
        df = pd.read_csv(os.path.join(path, f))
        print("Shape:", df.shape)
        print("Columns:", list(df.columns))
        print(df.iloc[0].to_string())