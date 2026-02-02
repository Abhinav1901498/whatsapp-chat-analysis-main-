import re
import pandas as pd

def preprocess(data):
    # नया WhatsApp format: [hh:mm am/pm, dd/mm/yyyy] Name: Message
    pattern = r'\[\d{1,2}:\d{2}\s(?:am|pm),\s\d{1,2}/\d{1,2}/\d{4}\]\s'

    # split messages (pattern से पहले वाला हिस्सा खाली हो सकता है)
    parts = re.split(pattern, data)
    dates = re.findall(pattern, data)

    # पहला हिस्सा (header या खाली) हटाओ
    messages = parts[1:] if len(parts) > 1 else []

    # length match करो
    min_len = min(len(messages), len(dates))
    messages = messages[:min_len]
    dates = dates[:min_len]

    if not dates or not messages:
        return pd.DataFrame()  # safety

    df = pd.DataFrame({'user_message': messages, 'message_date': dates})

    # datetime parse: [hh:mm am/pm, dd/mm/yyyy]
    df['message_date'] = pd.to_datetime(
        df['message_date'],
        format='[%I:%M %p, %d/%m/%Y] ',
        errors='coerce'
    )

    # invalid dates हटाओ
    df = df.dropna(subset=['message_date'])
    df.rename(columns={'message_date': 'date'}, inplace=True)

    # user और message अलग करो
    users = []
    messages_list = []
    for msg in df['user_message']:
        # Name: Message (name में space हो सकता है)
        match = re.match(r'^(.*?):\s(.*)$', msg.strip())
        if match:
            users.append(match.group(1).strip())
            messages_list.append(match.group(2).strip())
        else:
            users.append('group_notification')
            messages_list.append(msg.strip())

    df['user'] = users
    df['message'] = messages_list
    df.drop(columns=['user_message'], inplace=True)

    # clean message
    df['message'] = df['message'].astype(str).str.strip()
    df = df[df['message'] != '']

    # date features
    df['only_date'] = df['date'].dt.date
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute

    # period (hour range)
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