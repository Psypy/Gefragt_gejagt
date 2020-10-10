import requests
from bs4 import BeautifulSoup
import pandas as pd

url = "https://de.wikipedia.org/wiki/Gefragt_%E2%80%93_Gejagt/Episodenliste"

s = requests.Session()
response = s.get(url, timeout=10)
content = response.text

parser = BeautifulSoup(content, 'html.parser')
tables = parser.find_all('table')

# Initiate dataframe and append all html tables
gg = pd.DataFrame()

for t in tables:
    df = pd.read_html(str(t))[0]
    print(type(df))
    gg = pd.concat([gg, df], axis=0)

gg.to_csv('Gefragt_gejagt_data.csv', index=False)
