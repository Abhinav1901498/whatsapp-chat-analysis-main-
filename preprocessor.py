import re
import pandas as pd

def preprocess(data):
    pattern = r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s-\s'

    messages = re.split(pattern, data)[1:]
    dates = re.findall(pattern, data)

    if len(messages) != len(dates):
        # safety in case parsing mismatch
        min_len = min(len(messages), len(dates))
        messages = messages[:min_len]
        dates = dates[:min_len]

    df = pd.DataFrame({'user_message': messages, 'message_date': dates})

    try:
        df['message_date'] = pd.to_datetime(df['message_date'], format='%d/%m/%Y, %H:%M - ', errors='coerce')
    except:
        df['message_date'] = pd.to_datetime(df['message_date'], format='%d/%m/%y, %H:%M - ', errors='coerce')

    df = df.dropna(subset=['message_date'])  # remove invalid dates
    df.rename(columns={'message_date': 'date'}, inplace=True)

    users = []
    messages_list = []
    for msg in df['user_message']:
        entry = re.split(r'([\w\W]+?):\s', msg, maxsplit=1)
        if len(entry) >= 3:
            users.append(entry[1])
            messages_list.append(entry[2])
        else:
            users.append('group_notification')
            messages_list.append(entry[0] if entry else '')

    df['user'] = users
    df['message'] = messages_list
    df.drop(columns=['user_message'], inplace=True)

    # Clean message column early
    df['message'] = df['message'].astype(str).str.strip()
    df = df[df['message'] != '']

    # Extract date/time features
    df['only_date'] = df['date'].dt.date
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute

    # period column
    period = []
    for h in df['hour']:
        if h == 23:
            period.append("23-00")
        elif h == 0:
            period.append("00-01")
        else:
            period.append(f"{h}-{h+1}")
    df['period'] = period

    return df