import pandas as pd
from dotenv import load_dotenv
import os
load_dotenv()

path_to_database = os.getenv('path_to_database')

print("start loading database")
#df = pd.read_excel(path_to_database, sheet_name="Sheet1")
df = pd.read_csv(path_to_database, encoding="utf-8", sep=";")

print(f"loaded database , shape = ", df.shape)

