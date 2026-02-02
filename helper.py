from urlextract import URLExtract
from wordcloud import WordCloud
import pandas as pd
from collections import Counter
import emoji
import re

extract = URLExtract()

def fetch_stats(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    num_messages = df.shape[0]

    words = []
    for message in df['message']:
        if pd.notna(message):
            words.extend(str(message).split())

    num_media_messages = df[df['message'].str.contains('<Media omitted>', na=False)].shape[0]

    links = []
    for message in df['message']:
        if pd.notna(message):
            links.extend(extract.find_urls(str(message)))

    return num_messages, len(words), num_media_messages, len(links)


def most_busy_users(df):
    x = df['user'].value_counts().head()
    df_percent = round((df['user'].value_counts() / df.shape[0]) * 100, 2).reset_index().rename(
        columns={'index': 'name', 'user': 'percent'})
    return x, df_percent


def create_wordcloud(selected_user, df):
    try:
        with open('stop_hinglish.txt', 'r', encoding='utf-8') as f:
            stop_words = f.read().splitlines()
    except FileNotFoundError:
        stop_words = []  # fallback if file missing

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    temp = df[df['user'] != 'group_notification'].copy()
    temp = temp[~temp['message'].isin(['<Media omitted>\n', '<Media omitted>', 'This message was deleted', None, ''])]

    if temp.empty:
        wc = WordCloud(width=500, height=500, min_font_size=10, background_color='white')
        return wc.generate('')  # empty cloud

    # Force string + remove stop words
    temp['message'] = temp['message'].astype(str).str.lower().str.strip()
    def remove_stop_words(msg):
        return " ".join(word for word in msg.split() if word not in stop_words)

    temp['message'] = temp['message'].apply(remove_stop_words)

    wc = WordCloud(width=500, height=500, min_font_size=10, background_color='white')
    text = temp['message'].str.cat(sep=" ")
    if not text.strip():
        return wc.generate('')
    return wc.generate(text)


def most_common_words(selected_user, df):
    try:
        with open('stop_hinglish.txt', 'r', encoding='utf-8') as f:
            stop_words = f.read().splitlines()
    except FileNotFoundError:
        stop_words = []

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    temp = df[df['user'] != 'group_notification'].copy()
    temp = temp[~temp['message'].isin(['<Media omitted>\n', '<Media omitted>', 'This message was deleted', None, ''])]

    if temp.empty:
        return pd.DataFrame(columns=[0, 1])

    temp['message'] = temp['message'].astype(str).str.lower().str.strip()

    words = []
    for msg in temp['message']:
        words.extend(word for word in msg.split() if word not in stop_words)

    if not words:
        return pd.DataFrame(columns=[0, 1])

    most_common_df = pd.DataFrame(Counter(words).most_common(20))
    return most_common_df


def emoji_helper(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    emojis = []
    for message in df['message']:
        if pd.notna(message):
            # Modern way to detect emojis
            emojis.extend(c for c in str(message) if emoji.is_emoji(c))

    if not emojis:
        return pd.DataFrame(columns=[0, 1])

    emoji_df = pd.DataFrame(Counter(emojis).most_common())
    return emoji_df


def monthly_timeline(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    if df.empty:
        return pd.DataFrame()

    timeline = df.groupby(['year', 'month_num', 'month'], as_index=False)['message'].count()
    timeline['time'] = timeline['month'] + "-" + timeline['year'].astype(str)
    return timeline


def daily_timeline(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    if df.empty:
        return pd.DataFrame()

    daily_timeline = df.groupby('only_date', as_index=False)['message'].count()
    return daily_timeline


def week_activity_map(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    if df.empty:
        return pd.Series(dtype=int)
    return df['day_name'].value_counts()


def month_activity_map(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    if df.empty:
        return pd.Series(dtype=int)
    return df['month'].value_counts()


def activity_heatmap(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    if df.empty:
        return pd.DataFrame()

    user_heatmap = df.pivot_table(index='day_name', columns='period',
                                  values='message', aggfunc='count').fillna(0)
    return user_heatmap