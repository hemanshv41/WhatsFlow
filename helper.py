import pandas as pd
from collections import Counter
import emoji
import re
import random
from urllib.parse import urlparse
from wordcloud import WordCloud
from datetime import datetime, timedelta

def get_kpis(df):
    """
    INTERVIEW TALKING POINTS:
    - Counts standard dashboard KPI metrics:
      - Total Messages: Count of non-system messages.
      - Total Members: Unique senders.
      - Media Omitted: Text records containing standard omission markers.
      - Links Count: Total URLs identified in message body.
    """
    # Exclude system alerts (e.g. encryption or group creation logs)
    user_df = df[df['is_system'] == False]
    
    total_messages = len(user_df)
    total_members = user_df['sender'].nunique()
    
    # Check for media markers commonly written by Android/iOS
    media_markers = r'(?:<media omitted>|\[media omitted\]|image omitted|video omitted|document omitted|<media minimal>)'
    media_df = user_df[user_df['message'].str.lower().str.contains(media_markers, regex=True, na=False)]
    total_media = len(media_df)
    
    # Extract links using standard URL regex
    url_pattern = r'(https?://[^\s]+)'
    all_links = []
    for msg in user_df['message']:
        found = re.findall(url_pattern, msg)
        all_links.extend(found)
    total_links = len(all_links)
    
    return total_messages, total_members, total_media, total_links

def get_active_users(df):
    """
    INTERVIEW TALKING POINTS:
    - Computes participation shares per sender.
    - Uses standard pandas value_counts() and returns a clean DataFrame.
    """
    user_df = df[df['is_system'] == False]
    counts = user_df['sender'].value_counts().reset_index()
    counts.columns = ['user', 'messages']
    
    total_msgs = counts['messages'].sum()
    if total_msgs > 0:
        counts['percentage'] = (counts['messages'] / total_msgs * 100).round(1)
    else:
        counts['percentage'] = 0
    return counts

def get_word_cloud_and_rankings(df, custom_stopwords=None):
    """
    INTERVIEW TALKING POINTS:
    - Preprocesses chat messages to remove stopwords and links.
    - Returns a WordCloud styled with retro arcade neon colors.
    - Returns a DataFrame of the top 20 most frequent words.
    """
    user_df = df[df['is_system'] == False]
    
    # Exclude media markers from the word frequency counts
    media_markers = r'(?:<media omitted>|\[media omitted\]|image omitted|video omitted|document omitted|<media minimal>)'
    text_df = user_df[~user_df['message'].str.lower().str.contains(media_markers, regex=True, na=False)]
    
    # Stopwords list to filter out common filler words
    stopwords = {
        'to', 'and', 'the', 'a', 'of', 'in', 'for', 'on', 'is', 'i', 'you', 'me', 'my', 'we', 'he', 'she', 'it', 
        'this', 'that', 'with', 'at', 'but', 'are', 'was', 'have', 'has', 'had', 'do', 'so', 'just', 'like', 'get', 
        'go', 'all', 'be', 'or', 'if', 'your', 'our', 'u', 'ur', 'ok', 'okay', 'can', 'will', 'would', 'omitted', 
        'media', 'message', 'deleted'
    }
    if custom_stopwords:
        stopwords.update(custom_stopwords)
        
    words = []
    url_pattern = r'https?://[^\s]+'
    
    for msg in text_df['message']:
        # Remove URLs
        cleaned_msg = re.sub(url_pattern, '', msg)
        # Tokenize only alphabetical words between 2 and 15 letters long
        tokens = re.findall(r'\b[a-zA-Z]{2,15}\b', cleaned_msg.lower())
        filtered_tokens = [w for w in tokens if w not in stopwords]
        words.extend(filtered_tokens)
        
    if not words:
        return None, pd.DataFrame(columns=['word', 'count'])
        
    counts = Counter(words)
    top_words_df = pd.DataFrame(counts.most_common(20), columns=['word', 'count'])
    
    # Retro neon color palette generator for WordCloud (neon green, pink, cyan, yellow)
    def retro_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
        colors = ["#39ff14", "#ff007f", "#00ffff", "#ffff00"]
        return random.choice(colors)
        
    wc = WordCloud(
        width=800,
        height=400,
        background_color='#12131a',
        color_func=retro_color_func,
        max_words=80
    ).generate_from_frequencies(counts)
    
    return wc, top_words_df

def get_emoji_analysis(df):
    """
    INTERVIEW TALKING POINTS:
    - Iterates over characters in messages and extracts standard emoji icons.
    - Counts and sorts frequencies.
    """
    user_df = df[df['is_system'] == False]
    emojis = []
    for msg in user_df['message']:
        # Filter characters that match recognized emojis
        emojis.extend([char for char in msg if emoji.is_emoji(char)])
        
    if not emojis:
        return pd.DataFrame(columns=['emoji', 'count'])
        
    counts = Counter(emojis)
    emoji_df = pd.DataFrame(counts.most_common(15), columns=['emoji', 'count'])
    return emoji_df

def get_timelines(df):
    """
    INTERVIEW TALKING POINTS:
    - Aggregates messages chronologically over months and dates.
    """
    user_df = df[df['is_system'] == False].copy()
    
    # Monthly activity timeline
    user_df['month_year'] = user_df['date'].dt.to_period('M').astype(str)
    monthly = user_df.groupby('month_year').size().reset_index(name='messages')
    
    # Daily activity timeline
    user_df['date_only'] = user_df['date'].dt.date
    daily = user_df.groupby('date_only').size().reset_index(name='messages')
    
    return monthly, daily

def get_weekday_hour_heatmap(df):
    """
    INTERVIEW TALKING POINTS:
    - Generates weekday-hourly pivot data for activity heatmaps.
    - Chronologically sorts days from Monday to Sunday.
    """
    user_df = df[df['is_system'] == False].copy()
    
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Group and Pivot
    counts_df = user_df.groupby(['day_name', 'hour']).size().reset_index(name='messages')
    pivot = counts_df.pivot(index='day_name', columns='hour', values='messages').fillna(0)
    
    # Ensure all weekdays and 24 hours are represented
    pivot = pivot.reindex(day_order).fillna(0)
    for hr in range(24):
        if hr not in pivot.columns:
            pivot[hr] = 0
            
    return pivot[sorted(pivot.columns)]

def get_shared_links(df):
    """
    INTERVIEW TALKING POINTS:
    - Extract shared URLs and their base domains using urllib.parse.urlparse.
    """
    user_df = df[df['is_system'] == False]
    url_pattern = r'(https?://[^\s]+)'
    
    records = []
    for _, row in user_df.iterrows():
        urls = re.findall(url_pattern, row['message'])
        for url in urls:
            cleaned_url = url.rstrip('.,;:)("]')
            domain = urlparse(cleaned_url).netloc.replace('www.', '')
            records.append({
                'sender': row['sender'],
                'date': row['date'],
                'url': cleaned_url,
                'domain': domain
            })
            
    links_df = pd.DataFrame(records)
    if links_df.empty:
        return pd.DataFrame(columns=['sender', 'date', 'url', 'domain']), pd.DataFrame(columns=['domain', 'count'])
        
    domain_counts = links_df['domain'].value_counts().reset_index()
    domain_counts.columns = ['domain', 'count']
    return links_df, domain_counts

def calculate_reply_latency(df):
    """
    INTERVIEW TALKING POINTS:
    - Loops through chronologically sorted messages.
    - Identifies when the sender changes.
    - Calculates the delay in minutes.
    - Averages reply speeds under 120 minutes (2 hours) to focus on conversational pacing.
    """
    sorted_df = df.sort_values('date').copy()
    reply_records = []
    
    for i in range(1, len(sorted_df)):
        curr = sorted_df.iloc[i]
        prev = sorted_df.iloc[i-1]
        
        # Exclude system automated notifications
        if curr['is_system'] or prev['is_system']:
            continue
            
        # If sender changed, calculate delay
        if curr['sender'] != prev['sender']:
            delay_minutes = (curr['date'] - prev['date']).total_seconds() / 60.0
            
            # Focus on conversational responses (less than 2 hours delay)
            if 0 < delay_minutes <= 120:
                reply_records.append({
                    'user': curr['sender'],
                    'latency': delay_minutes
                })
                
    latency_df = pd.DataFrame(reply_records)
    if latency_df.empty:
        return pd.DataFrame(columns=['user', 'avg_reply_mins'])
        
    summary = latency_df.groupby('user')['latency'].mean().round(1).reset_index()
    summary.columns = ['user', 'avg_reply_mins']
    
    # Sort from fastest (smallest latency) to slowest
    return summary.sort_values('avg_reply_mins', ascending=True)

def generate_mock_chat():
    """
    INTERVIEW TALKING POINTS:
    - Generates simple retro 8-bit themed mock data to explore the dashboard.
    """
    members = ["Aarav_Arcade", "Priya_Pixel", "Kabir_CRT"]
    emojis = ["🎮", "👾", "🔥", "👍", "😂", "🚀", "✨"]
    links = [
        "https://github.com/streamlit/streamlit",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://news.ycombinator.com"
    ]
    
    chats = [
        "Hey pixel squads! Ready for retro coding today? 🎮",
        "Absolutely Aarav! Let's get the 8-bit graphics working.",
        "I am building a CRT layout in Streamlit. It looks sick! 👾",
        "Can you share the repo link?",
        "Sure, here it is: https://github.com/streamlit/streamlit",
        "Oh wow! Streamlit is extremely simple to program! 👍",
        "Did you see this retro tutorial? https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "Hahaha that is absolute gold! 😂",
        "Let me upload some retro art assets. <Media omitted>",
        "Checking out ycombinator now: https://news.ycombinator.com",
        "We are launching this pixel application tonight! 🚀",
        "Awesome! CRT screen rendering is perfect. ✨"
    ]
    
    # Generate 120 simple messages over the last 10 days
    start = datetime.now() - timedelta(days=10)
    current_time = start
    lines = []
    
    # Encryption notice
    lines.append(f"{current_time.strftime('%m/%d/%y, %I:%M %p')} - Messages and calls are end-to-end encrypted.")
    current_time += timedelta(minutes=2)
    lines.append(f"{current_time.strftime('%m/%d/%y, %I:%M %p')} - Aarav_Arcade created group \"Retro Pixel Squad\"")
    current_time += timedelta(hours=1)
    
    last_sender = None
    for _ in range(120):
        # Pick sender
        if last_sender and random.random() < 0.3:
            sender = last_sender
            current_time += timedelta(seconds=random.randint(10, 60))
        else:
            sender = random.choice([m for m in members if m != last_sender])
            current_time += timedelta(minutes=random.randint(1, 30))
            
        last_sender = sender
        phrase = random.choice(chats)
        
        # Add random retro emojis sometimes
        if random.random() < 0.2:
            phrase += " " + random.choice(emojis)
            
        timestamp = current_time.strftime('%m/%d/%y, %I:%M %p')
        lines.append(f"{timestamp} - {sender}: {phrase}")
        
    return "\n".join(lines)
