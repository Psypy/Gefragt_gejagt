import pandas as pd
import numpy as np
import unicodedata
import re

gg = pd.read_csv('Gefragt_gejagt_data.csv')
print(gg.columns)
datum = gg.loc[0, 'Datum']

# Drop rows that reprsent shows that have not been aired (i.e. have no data)
gg = gg[gg.index <= 551]

# Normalizing unicode data in strings
gg['Datum'] = gg['Datum'].apply(lambda x: unicodedata.normalize("NFKD", x))
gg['Finalisten'] = gg['Finalisten'].apply(lambda x: unicodedata.normalize("NFKD", x))

# Clean the "Nr. (gesamt) column
nr_gesamt_cols = gg.filter(like='gesamt', axis=1)
gg['episode'] = nr_gesamt_cols[nr_gesamt_cols.columns[0]]\
    .combine_first(nr_gesamt_cols[nr_gesamt_cols.columns[1]])\
    .combine_first(nr_gesamt_cols[nr_gesamt_cols.columns[2]])\
    .combine_first(nr_gesamt_cols[nr_gesamt_cols.columns[1]])

# Drop the no irrelevant "Nr. (gesamt)" columns
gg = gg.drop(nr_gesamt_cols.columns, axis=1)

# TODO Das ist vielleicht eher Teil des Feature engineerings und nicht data cleaning
# Indication flawless victory of chaser
gg['flawless'] = np.where(gg['Zeit bzw. Punkte des Jägers'].str.contains("fehlerlos"), 1, 0)

# Indication victory of chaser or contenders
gg['win_chaser'] = np.where(gg['Zeit bzw. Punkte des Jägers'].str.contains("Punkte"), 0, 1)

# Time it took for Jäger to win
def extract_time(str):
    '''Function to extract duration of chase from "Zeit bzw. Punkte des Jägers" column'''

    # Set duration to 120 if chaser lost (i.e. "Punkte" is in string)
    if "Punkte" in str:
        duration = 120
    else:
        duration = 0
        # Search for minutes and seconds
        minutes = re.search(r'(\d+)(?:\sMin.)', str)
        seconds = re.search(r'(\d+)(?:\sSek.)', str)

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