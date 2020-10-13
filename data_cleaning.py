import pandas as pd
import numpy as np
import unicodedata
import re

# Load data
gg = pd.read_csv('Gefragt_gejagt_data.csv')

# Drop rows that represent shows that have not been aired (i.e. have no data)
gg = gg.dropna(subset=['Jäger'], axis=0)

# Normalizing unicode data in strings
gg['Datum'] = gg['Datum'].apply(lambda x: unicodedata.normalize("NFKC", x))
gg['Finalisten'] = gg['Finalisten'].apply(lambda x: unicodedata.normalize("NFKD", x))

# Clean the "Nr. (gesamt) column
nr_gesamt_cols = gg.filter(like='gesamt', axis=1)
gg['episode'] = nr_gesamt_cols[nr_gesamt_cols.columns[0]] \
    .combine_first(nr_gesamt_cols[nr_gesamt_cols.columns[1]]) \
    .combine_first(nr_gesamt_cols[nr_gesamt_cols.columns[2]]) \
    .combine_first(nr_gesamt_cols[nr_gesamt_cols.columns[1]])

# Drop the no irrelevant "Nr. (gesamt)" columns
gg = gg.drop(nr_gesamt_cols.columns, axis=1)

# Indication flawless victory of chaser
gg['flawless'] = np.where(gg['Zeit bzw. Punkte des Jägers'].str.contains("fehlerlos"), 1, 0)

# Indication victory of chaser or contenders
gg['win_chaser'] = np.where(gg['Zeit bzw. Punkte des Jägers'].str.contains("Punkte"), 0, 1)


# Duration of the chase
def extract_time(string):
    '''Function to extract duration of chase from "Zeit bzw. Punkte des Jägers" column'''

    # Set duration to 120 if chaser lost (i.e. "Punkte" is in string)
    if "Punkte" in string:
        duration = 120
    else:
        duration = 0
        # Search for minutes and seconds
        minutes = re.search(r'(\d+)(?:\sMin.)', string)
        seconds = re.search(r'(\d+)(?:\sSek.)', string)

        if minutes is not None:
            duration = duration + int(minutes.group(1)[-1]) * 60
        if seconds is not None:
            duration = duration + int(seconds.group(1))

    return duration


gg['chase_duration'] = gg['Zeit bzw. Punkte des Jägers'].apply(extract_time)

# Indicator if chaser caught all challengers in seconds round so that a finalist had to be nominated
gg['caught_all'] = np.where(gg['Finalisten'].str.contains('alle ausgeschieden'), 1, 0)

# Number of finalists
gg['nr_finalists'] = gg['Finalisten'].apply(
    lambda x: len(x.split('mit')[0].split(','))
)

# Points of finalists
gg['finalists_pts'] = gg['Finalisten'].apply(
    lambda x: int(x.split('mit')[1].split()[0])
)

# Points of Jäger
gg['chaser_pts'] = gg['Zeit bzw. Punkte des Jägers'].apply(
    lambda x: int(x.split()[0]) if 'Punkte' in x else np.nan
)
gg['chaser_pts'] = gg['chaser_pts'].fillna(gg['finalists_pts'])
gg['chaser_pts'] = gg['chaser_pts'].astype(int)

# Setbacks in finale
gg['setbacks'] = gg['Finalisten'].apply(
    lambda x: int(x.split('+')[1].split()[0] if '+' in x else 0)
)

# Who won the finale
gg['chaser_won'] = np.where(gg['finalists_pts'] <= gg['chaser_pts'], 1, 0)

# Cleaning prize column
gg['prize'] = gg[gg.columns[6]] \
    .str.replace(".", "") \
    .str.replace("€", "") \
    .str.lstrip("0") \
    .str.strip() \
    .astype(int)

# Cleaning date column
month_dict = {"Jan.": "January", "Feb.": "February", "März": "March", "Apr": "April", "Mai": "May",
              "Juni": "June", "Juli": "July", "Sep.": "September", "Okt.": "October", "Nov.": "November",
              "Dez.": "December"}

gg['date'] = pd.to_datetime(gg['Datum'].replace(to_replace=month_dict, regex=True))

# Drop rows that refer to specials
gg = gg[~gg['Nr. (Staffel)'].str.contains('S')].copy()

# Clean episode in season
gg['episode_in_season'] = gg['Nr. (Staffel)'].astype(int)


# Categorizing episodes to seasons
def get_season(series):
    '''Function to number seasons based on episode numbers'''

    series = series.astype(int)
    season_numbers = []
    season = 0
    for episode in series:
        if episode == 1:
            season += 1

        season_numbers.append(season)

    return season_numbers


gg['season'] = get_season(gg['Nr. (Staffel)'])

# Simple index of episodes without specials
gg['episode_without_special'] = np.arange(1, len(gg) + 1, 1)

# Exporting to Excel for use in Tableau
gg.to_excel('Gefragt_gejagt.xlsx', index=False)
