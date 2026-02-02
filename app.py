import streamlit as st
import preprocessor, helper
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

st.set_page_config(page_title="WhatsApp Chat Analyzer", layout="wide")

st.title("WhatsApp Chat Analyzer")
st.sidebar.title("Upload & Settings")

uploaded_file = st.sidebar.file_uploader("Choose a WhatsApp chat .txt file", type=["txt"])

if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()

    # Handle encoding safely
    try:
        data = bytes_data.decode('utf-8')
    except UnicodeDecodeError:
        try:
            data = bytes_data.decode('windows-1252')  # or latin-1
        except UnicodeDecodeError:
            data = bytes_data.decode('utf-8', errors='replace')

    df = preprocessor.preprocess(data)

    # Fetch unique users
    user_list = df['user'].unique().tolist()

    # Safely remove 'group_notification' (present in group chats, not in personal)
    user_list = [user for user in user_list if user != 'group_notification']

    user_list.sort()
    user_list.insert(0, "Overall")

    selected_user = st.sidebar.selectbox("Show analysis for", user_list)

    if st.sidebar.button("Show Analysis"):

        # Stats Area (works for both personal and group chats)
        num_messages, words, num_media_messages, num_links = helper.fetch_stats(selected_user, df)

        st.subheader("📊 Top Statistics")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Messages", num_messages)
        with col2:
            st.metric("Total Words", words)
        with col3:
            st.metric("Media Shared", num_media_messages)
        with col4:
            st.metric("Links Shared", num_links)

        # Monthly Timeline (time-based, works for all chats)
        st.subheader("Monthly Timeline")
        timeline = helper.monthly_timeline(selected_user, df)
        if not timeline.empty:
            fig, ax = plt.subplots()
            ax.plot(timeline['time'], timeline['message'], color='green', marker='o')
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.info("No monthly timeline data available.")

        # Daily Timeline
        st.subheader("Daily Timeline")
        daily_timeline = helper.daily_timeline(selected_user, df)
        if not daily_timeline.empty:
            fig, ax = plt.subplots()
            ax.plot(daily_timeline['only_date'], daily_timeline['message'], color='black')
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.info("No daily timeline data available.")

        # Activity Map
        st.subheader("Activity Map")
        col1, col2 = st.columns(2)

        with col1:
            st.caption("Most Busy Day")
            busy_day = helper.week_activity_map(selected_user, df)
            if not busy_day.empty:
                fig, ax = plt.subplots()
                ax.bar(busy_day.index, busy_day.values, color='purple')
                plt.xticks(rotation=45)
                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.info("No busy day data available.")

        with col2:
            st.caption("Most Busy Month")
            busy_month = helper.month_activity_map(selected_user, df)
            if not busy_month.empty:
                fig, ax = plt.subplots()
                ax.bar(busy_month.index, busy_month.values, color='orange')
                plt.xticks(rotation=45)
                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.info("No busy month data available.")

        # Weekly Heatmap (with check to prevent error when empty)
        st.subheader("Weekly Activity Heatmap")
        user_heatmap = helper.activity_heatmap(selected_user, df)
        if not user_heatmap.empty and user_heatmap.shape[0] > 0 and user_heatmap.shape[1] > 0:
            user_heatmap = user_heatmap.astype(int)
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.heatmap(user_heatmap, ax=ax, cmap='YlGnBu', annot=True, fmt="d")
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.info("No activity heatmap data available. The chat may not have enough messages or timestamps were not parsed correctly.")

        # Most Busy Users (only for group chats, skipped in personal)
        if selected_user == 'Overall' and len(user_list) > 2:  # if more than 2 users → group
            st.subheader("Most Busy Users")
            x, new_df = helper.most_busy_users(df)

            col1, col2 = st.columns([3, 2])

            with col1:
                fig, ax = plt.subplots()
                ax.bar(x.index, x.values, color='red')
                plt.xticks(rotation=45)
                plt.tight_layout()
                st.pyplot(fig)

            with col2:
                st.dataframe(new_df.style.background_gradient(cmap='Reds'))
        elif selected_user == 'Overall' and len(user_list) <= 2:
            st.info("This is a personal chat, so 'Most Busy Users' analysis is not available.")

               # WordCloud
        st.subheader("Word Cloud")
        try:
            df_wc = helper.create_wordcloud(selected_user, df)
            if df_wc is not None:
                fig, ax = plt.subplots()
                ax.imshow(df_wc)
                ax.axis("off")
                st.pyplot(fig)
            else:
                st.info("No text available to generate Word Cloud.")
        except Exception as e:
            st.warning(f"Word Cloud could not be generated: {str(e)}")
        # Most Common Words
        st.subheader("Most Common Words")
        most_common_df = helper.most_common_words(selected_user, df)
        if not most_common_df.empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.barh(most_common_df[0], most_common_df[1], color='teal')
            ax.invert_yaxis()  # highest at the top
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.info("No common words data available.")

        # Emoji Analysis
        st.subheader("Emoji Analysis")
        emoji_df = helper.emoji_helper(selected_user, df)

        col1, col2 = st.columns([3, 2])

        with col1:
            if not emoji_df.empty:
                st.dataframe(emoji_df.head(20).style.background_gradient(cmap='Blues'))
            else:
                st.info("No emoji data available.")

        with col2:
            if not emoji_df.empty:
                fig, ax = plt.subplots()
                ax.pie(emoji_df[1].head(8), labels=emoji_df[0].head(8),
                       autopct="%0.1f%%", shadow=True, startangle=90)
                ax.axis("equal")
                st.pyplot(fig)
            else:
                st.info("No emojis found in this chat.")