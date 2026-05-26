import streamlit as st
import pandas as pd
import plotly.express as px
import io
import zipfile
from preprocess import preprocess
from helper import (
    get_kpis,
    get_active_users,
    get_word_cloud_and_rankings,
    get_emoji_analysis,
    get_timelines,
    get_weekday_hour_heatmap,
    get_shared_links,
    calculate_reply_latency,
    generate_mock_chat
)

# 1. Page Configuration & Retro CSS Style Injection
st.set_page_config(
    page_title="WhatsFlow — Retro Chat Analytics",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom retro 8-bit CSS Stylesheet with premium slate coordinate grid background and Fira Code readability
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;400;500;600;700&family=VT323&display=swap');

/* Global CRT terminal coordinate grid styling with high readability */
.stApp {
    background: radial-gradient(circle at 50% 50%, #0d0f14 0%, #050608 100%) !important;
    background-image: 
        linear-gradient(rgba(255, 255, 255, 0.005) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.005) 1px, transparent 1px) !important;
    background-size: 30px 30px !important;
    color: #e2e8f0 !important; /* Premium high-contrast off-white for body text */
    font-family: 'Fira Code', monospace !important;
    font-size: 1.1rem !important;
}

/* Sidebar CRT style */
[data-testid="stSidebar"] {
    background-color: #0b0c10 !important;
    border-right: 4px solid #00ffff !important; /* Clean Cyber Cyan border */
    color: #cbd5e1 !important;
}

[data-testid="stSidebar"] * {
    color: #cbd5e1 !important;
    font-family: 'Fira Code', monospace !important;
}

/* Custom legible retro headers */
h1, h2, h3, .retro-header {
    font-family: 'VT323', monospace !important;
    color: #ffffff !important; 
    text-shadow: 2px 2px 0px #ff007f !important; /* Magenta offset shadow */
    font-weight: normal !important;
    letter-spacing: 1px !important;
    margin-bottom: 20px !important;
}

h1 { font-size: 3rem !important; }
h2 { font-size: 2.2rem !important; }
h3 { font-size: 1.8rem !important; }

h4, .retro-subheader {
    font-family: 'VT323', monospace !important;
    color: #ffff00 !important; /* Yellow accent */
    font-size: 1.4rem !important;
    margin-top: 15px !important;
}

/* Flat retro blocky cards (slate background, cyan/magenta border, soft shadows) */
.retro-card {
    background-color: #0f1118 !important;
    border: 3px solid #00ffff !important; /* Neon Cyan Border for crisp contrast */
    box-shadow: 6px 6px 0px rgba(255, 0, 127, 0.15) !important; /* Cyber Pink shadow */
    padding: 24px;
    margin-bottom: 25px;
    border-radius: 0px !important;
}

/* Streamlit Tabs styled to look like old tab directories */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: #0b0c10 !important;
    padding: 6px;
    border: 3px solid #39ff14; /* Green terminal frame */
    border-radius: 0px !important;
}

.stTabs [data-baseweb="tab"] {
    height: 44px;
    background-color: #0f1118 !important;
    border-radius: 0px !important;
    color: #cbd5e1 !important;
    font-weight: 500 !important;
    font-family: 'Fira Code', monospace !important;
    font-size: 0.9rem !important;
    border: 1px solid #39ff14 !important;
    padding: 0px 18px !important;
    transition: all 0.1s ease !important;
}

.stTabs [data-baseweb="tab"]:hover {
    color: #000000 !important;
    background-color: #39ff14 !important;
}

.stTabs [aria-selected="true"] {
    background-color: #00ffff !important; /* Cyan active highlight */
    color: #000000 !important;
    border-color: #ffffff !important;
    font-weight: bold !important;
}

/* Retro arcade solid buttons */
.stButton>button {
    background-color: #ff007f !important;
    color: #ffffff !important;
    font-family: 'VT323', monospace !important;
    font-size: 1.4rem !important;
    border: 3px solid #ffffff !important;
    box-shadow: 4px 4px 0px #00ffff !important;
    border-radius: 0px !important;
    padding: 8px 24px !important;
    transition: all 0.1s ease !important;
}

.stButton>button:hover {
    background-color: #00ffff !important;
    color: #000000 !important;
    box-shadow: 2px 2px 0px #ff007f !important;
    transform: translate(2px, 2px);
}

/* Customize DataFrame tables to match the slate card color and Fira Code font */
[data-testid="stTable"] *, [data-testid="stDataFrame"] * {
    font-family: 'Fira Code', monospace !important;
    color: #f1f5f9 !important; /* Pure white/light grey for legibility */
    background-color: #0f1118 !important;
    font-size: 0.95rem !important;
}

/* Customize Selectbox and Inputs */
div[data-baseweb="select"] {
    border: 2px solid #00ffff !important;
    border-radius: 0px !important;
    background-color: #0f1118 !important;
    color: #f1f5f9 !important;
}

textarea {
    border: 2px solid #00ffff !important;
    border-radius: 0px !important;
    background-color: #0f1118 !important;
    color: #f1f5f9 !important;
}
</style>
""", unsafe_allow_html=True)


# CRT retro Plotly chart decorator with high readability
def style_retro_chart(fig, title_text=""):
    """
    INTERVIEW TALKING POINTS:
    - Sets transparent chart backgrounds and deep slate #0f1118 plotting areas.
    - Forces typography to use highly legible monospace 'Fira Code' fonts.
    - Applies crisp, white axes and bright arcade neon colors for high visibility.
    """
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#0f1118',
        font=dict(family='Fira Code, monospace', color='#cbd5e1', size=14),
        title=dict(
            text=f"[ {title_text.upper()} ]",
            font=dict(family='VT323, monospace', color='#ffff00', size=24),
            x=0.02
        ),
        margin=dict(l=60, r=40, t=80, b=60),
        xaxis=dict(
            gridcolor='#1e293b',
            zerolinecolor='#1e293b',
            tickfont=dict(color='#cbd5e1', size=12),
            title_font=dict(color='#00ffff', size=14)
        ),
        yaxis=dict(
            gridcolor='#1e293b',
            zerolinecolor='#1e293b',
            tickfont=dict(color='#cbd5e1', size=12),
            title_font=dict(color='#00ffff', size=14)
        ),
        legend=dict(
            font=dict(color='#e2e8f0', size=11),
            bgcolor='#0f1118',
            bordercolor='#00ffff',
            borderwidth=2
        )
    )
    return fig


# 2. Sidebar Import Options
st.sidebar.markdown('### [ LOAD CHAT DATABASE ]')
uploaded_file = st.sidebar.file_uploader("Upload exported .txt or .zip file:", type=["txt", "zip"])

if "df" not in st.session_state:
    st.session_state.df = None
if "source" not in st.session_state:
    st.session_state.source = None

# Parse uploaded file
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.zip'):
            with zipfile.ZipFile(uploaded_file) as z:
                txt_files = [f for f in z.namelist() if f.endswith('.txt')]
                if txt_files:
                    with z.open(txt_files[0]) as f:
                        file_content = io.TextIOWrapper(f, encoding='utf-8').read()
                else:
                    st.sidebar.error("No txt log inside zip!")
                    file_content = None
        else:
            file_content = io.TextIOWrapper(uploaded_file, encoding='utf-8').read()

        if file_content:
            st.session_state.df = preprocess(file_content)
            st.session_state.source = uploaded_file.name
            st.sidebar.success("LOG PARSE OK!")
    except Exception as e:
        st.sidebar.error(f"PARSE ERROR: {e}")

df = st.session_state.df

# 3. Welcome Screen
if df is None:
    st.markdown("""
    <div style="text-align: center; margin-top: 5vh; margin-bottom: 20px; border: 6px double #39ff14; padding: 30px; background-color: #12131a;">
        <h1 class="retro-header" style="margin: 0; font-size: 3.5rem; text-shadow: 4px 4px 0px #ff007f;">🕹️ WhatsFlow 👾</h1>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="max-width: 800px; margin: 40px auto;">
        <div class="retro-card">
            <h3 style="margin-top: 0; color: #ffff00; font-family: 'VT323', monospace; font-size: 1.4rem; letter-spacing: 1px;">[ UPLOAD CHAT LOG ]</h3>
            <p style="line-height: 1.8; color: #cbd5e1; font-size: 1.3rem; margin-bottom: 20px;">
                Securely analyze your WhatsApp chat. No data leaves your machine.
            </p>
            <div style="border-top: 4px dashed #39ff14; padding-top: 20px; margin-top: 20px;">
                <p style="margin-bottom: 12px; font-size: 1.2rem;">👉 <b>1.</b> Export your WhatsApp chat (without media) as a <b>.txt</b> file.</p>
                <p style="margin-bottom: 12px; font-size: 1.2rem;">👉 <b>2.</b> Drag and drop the file into the sidebar to start analysis.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    # 4. Filter configurations
    st.sidebar.markdown("---")
    st.sidebar.markdown("### [ CONFIG CONTROLS ]")
    
    # Member filter
    members = sorted(df[df['is_system'] == False]['sender'].unique().tolist())
    selected_member = st.sidebar.selectbox("Filter Sender:", ["ALL MEMBERS"] + members)
    
    # Custom stopwords filter
    custom_stopwords_input = st.sidebar.text_area("Stopwords to Ignore (comma separated):", placeholder="e.g. yeah, no")
    ignored_words = set()
    if custom_stopwords_input:
        ignored_words = {w.strip().lower() for w in custom_stopwords_input.split(',')}
        
    # Apply filters
    filtered_df = df.copy()
    if selected_member != "ALL MEMBERS":
        filtered_df = filtered_df[filtered_df['sender'] == selected_member]
        
    user_filtered_df = filtered_df[filtered_df['is_system'] == False]
    
    if user_filtered_df.empty:
        st.warning("👾 ZERO LOGS FOUND. TRY ADJUSTING SENDER FILTERS.")
    else:
        total_messages, total_members, total_media, total_links = get_kpis(filtered_df)
        
        # Retro header banner
        st.markdown(f"""
        <div style="border: 4px solid #39ff14; background-color: #12131a; padding: 15px; margin-bottom: 25px; text-align: center;">
            <h2 style="margin: 0; font-size: 2.5rem; color: #ffffff; font-family: 'VT323', monospace; text-shadow: 2px 2px 0px #ff007f; letter-spacing: 2px;">🎮 WhatsFlow Arcade Dashboard 🎮</h2>
            <p style="margin: 8px 0 0 0; font-family: 'Fira Code', monospace; color: #cbd5e1; font-size: 1.0rem;">Active Log: {st.session_state.source} | Cohort: {selected_member}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 8-Bit KPI layout
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="retro-card" style="text-align: center;">
                <h4 style="margin: 0; color: #ffff00; font-size: 1.3rem; font-family: 'VT323', monospace; letter-spacing: 1px;">[ TOTAL MSGS ]</h4>
                <div style="font-family: 'VT323', monospace; font-size: 3.5rem; color: #39ff14; margin-top: 10px; font-weight: bold; line-height: 1.1;">{total_messages}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="retro-card" style="text-align: center;">
                <h4 style="margin: 0; color: #ffff00; font-size: 1.3rem; font-family: 'VT323', monospace; letter-spacing: 1px;">[ ACTIVE SENDS ]</h4>
                <div style="font-family: 'VT323', monospace; font-size: 3.5rem; color: #39ff14; margin-top: 10px; font-weight: bold; line-height: 1.1;">{total_members}</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="retro-card" style="text-align: center;">
                <h4 style="margin: 0; color: #ffff00; font-size: 1.3rem; font-family: 'VT323', monospace; letter-spacing: 1px;">[ MEDIA LOGGED ]</h4>
                <div style="font-family: 'VT323', monospace; font-size: 3.5rem; color: #39ff14; margin-top: 10px; font-weight: bold; line-height: 1.1;">{total_media}</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="retro-card" style="text-align: center;">
                <h4 style="margin: 0; color: #ffff00; font-size: 1.3rem; font-family: 'VT323', monospace; letter-spacing: 1px;">[ LINKS LOGGED ]</h4>
                <div style="font-family: 'VT323', monospace; font-size: 3.5rem; color: #39ff14; margin-top: 10px; font-weight: bold; line-height: 1.1;">{total_links}</div>
            </div>
            """, unsafe_allow_html=True)
            
        # 5. Interactive Arcade Tabs
        tab_flow, tab_senders, tab_words, tab_assets = st.tabs([
            "🕹️ [FLOW TIMELINE]",
            "👾 [MEMBER STATS]",
            "📝 [WORDS & EMOJIS]",
            "💾 [SHARED LOGS]"
        ])
        
        # ==========================================
        # TAB 1: FLOW TIMELINE & HEATMAPS
        # ==========================================
        with tab_flow:
            st.markdown('<div class="retro-card">', unsafe_allow_html=True)
            st.markdown("### [ CHAT FREQUENCY TIMELINE ]")
            
            mode = st.radio("Select Resolution:", ["Monthly", "Daily"], horizontal=True)
            monthly_tl, daily_tl = get_timelines(filtered_df)
            
            if mode == "Monthly":
                fig = px.area(
                    monthly_tl,
                    x='month_year',
                    y='messages',
                    labels={'month_year': 'Month', 'messages': 'Messages'},
                    color_discrete_sequence=['#ff007f'] # Retro Pink
                )
                fig.update_traces(line=dict(width=4))
            else:
                fig = px.line(
                    daily_tl,
                    x='date_only',
                    y='messages',
                    labels={'date_only': 'Date', 'messages': 'Messages'},
                    color_discrete_sequence=['#39ff14'] # Retro Green
                )
                fig.update_traces(line=dict(width=3))
                
            st.plotly_chart(style_retro_chart(fig, f"{mode} Timeline"), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns([3, 2])
            
            with col1:
                st.markdown('<div class="retro-card" style="height: 100%;">', unsafe_allow_html=True)
                st.markdown("### [ CRT HEATMAP (WEEKDAY vs HOUR) ]")
                heatmap_data = get_weekday_hour_heatmap(filtered_df)
                
                # Plotly imshow colored like a retro plasma screen
                fig = px.imshow(
                    heatmap_data,
                    labels=dict(x="Hour of Day", y="Day of Week", color="Messages"),
                    x=heatmap_data.columns,
                    y=heatmap_data.index,
                    color_continuous_scale=[[0, '#000000'], [0.3, '#312e81'], [0.7, '#ff007f'], [1, '#ffff00']]
                )
                fig.update_xaxes(dtick=2)
                st.plotly_chart(style_retro_chart(fig, "24h Activity Load"), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            with col2:
                st.markdown('<div class="retro-card" style="height: 100%;">', unsafe_allow_html=True)
                st.markdown("### [ CONTRIBUTION SPLIT ]")
                active_users = get_active_users(filtered_df)
                
                # Retro blocky donut pie chart
                fig = px.pie(
                    active_users.head(5),
                    values='messages',
                    names='user',
                    hole=0.4,
                    color_discrete_sequence=['#39ff14', '#ff007f', '#00ffff', '#ffff00', '#a855f7']
                )
                fig.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#000000', width=3)))
                st.plotly_chart(style_retro_chart(fig, "Top 5 Senders"), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

        # ==========================================
        # TAB 2: MEMBER STATS & RESPONSE SPEED
        # ==========================================
        with tab_senders:
            st.markdown('<div class="retro-card">', unsafe_allow_html=True)
            st.markdown("### [ CHAT VOLUME LEADERBOARD ]")
            user_counts = get_active_users(filtered_df)
            
            fig = px.bar(
                user_counts,
                x='messages',
                y='user',
                orientation='h',
                labels={'messages': 'Messages Sent', 'user': 'Sender'},
                color_discrete_sequence=['#39ff14']
            )
            fig.update_layout(coloraxis_showscale=False)
            fig.update_yaxes(categoryorder='total ascending')
            st.plotly_chart(style_retro_chart(fig, "Messages Leaderboard"), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            col_l, col_r = st.columns(2)
            
            with col_l:
                st.markdown('<div class="retro-card" style="height: 100%;">', unsafe_allow_html=True)
                st.markdown("### [ RESPONSE LATENCY (SPEEDRUN) ]")
                st.markdown("<p style='font-size:1.1rem; color:#ffff00; margin-top: -10px;'>Average response delay in minutes per member when replying to a different sender.</p>", unsafe_allow_html=True)
                
                latency_df = calculate_reply_latency(filtered_df)
                if latency_df.empty:
                    st.info("👾 ZERO REPLIES DETECTED FOR TIMING DYNAMICS.")
                else:
                    fig = px.bar(
                        latency_df,
                        x='avg_reply_mins',
                        y='user',
                        orientation='h',
                        labels={'avg_reply_mins': 'Avg Delay (Mins)', 'user': 'User'},
                        color='avg_reply_mins',
                        color_continuous_scale=[[0, '#39ff14'], [1, '#ff007f']]  # Green (fast) to Pink (slow)
                    )
                    fig.update_layout(coloraxis_showscale=False)
                    fig.update_yaxes(categoryorder='total descending')
                    st.plotly_chart(style_retro_chart(fig, "Fastest Responders"), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            with col_r:
                st.markdown('<div class="retro-card" style="height: 100%;">', unsafe_allow_html=True)
                st.markdown("### [ VERBOSITY RATE ]")
                st.markdown("<p style='font-size:1.1rem; color:#ffff00; margin-top: -10px;'>Average word count sent per individual message.</p>", unsafe_allow_html=True)
                
                word_rates = []
                for u in user_counts['user']:
                    u_msgs = filtered_df[(filtered_df['sender'] == u) & (filtered_df['is_system'] == False)]
                    if len(u_msgs) > 0:
                        avg_w = u_msgs['message'].apply(lambda x: len(x.split())).mean()
                        word_rates.append({'user': u, 'avg_words': round(avg_w, 1)})
                
                word_rates_df = pd.DataFrame(word_rates)
                if not word_rates_df.empty:
                    fig = px.bar(
                        word_rates_df,
                        x='user',
                        y='avg_words',
                        labels={'user': 'User', 'avg_words': 'Avg Words'},
                        color_discrete_sequence=['#00ffff']
                    )
                    st.plotly_chart(style_retro_chart(fig, "Words Per Message"), use_container_width=True)
                else:
                    st.info("👾 ERROR GENERATING VERBOSITY GRAPH.")
                st.markdown('</div>', unsafe_allow_html=True)

        # ==========================================
        # TAB 3: WORDS & EMOJIS
        # ==========================================
        with tab_words:
            col_words, col_emoji = st.columns(2)
            
            with col_words:
                st.markdown('<div class="retro-card" style="height: 100%;">', unsafe_allow_html=True)
                st.markdown("### [ NEON WORD CLOUD ]")
                
                wc, words_rank = get_word_cloud_and_rankings(filtered_df, ignored_words)
                
                if wc is None or words_rank.empty:
                    st.info("👾 ZERO WORD ENTRIES COMPILED.")
                else:
                    # Render retro wordcloud
                    st.image(wc.to_array(), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            with col_emoji:
                st.markdown('<div class="retro-card" style="height: 100%;">', unsafe_allow_html=True)
                st.markdown("### [ EMOJI LEADERBOARD ]")
                
                em_df = get_emoji_analysis(filtered_df)
                if em_df.empty:
                    st.info("👾 ZERO EMOJIS FOUND IN CHAT STREAM.")
                else:
                    # Emoji blocky bar chart
                    fig = px.bar(
                        em_df.head(10),
                        x='count',
                        y='emoji',
                        orientation='h',
                        labels={'count': 'Occurrences', 'emoji': 'Emoji'},
                        color_discrete_sequence=['#ff007f']
                    )
                    fig.update_yaxes(categoryorder='total ascending')
                    st.plotly_chart(style_retro_chart(fig, "Emoji Count"), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

        # ==========================================
        # TAB 4: SHARED LOGS (LINKS & MEDIA)
        # ==========================================
        with tab_assets:
            col_m, col_l = st.columns(2)
            
            with col_m:
                st.markdown('<div class="retro-card" style="height: 100%;">', unsafe_allow_html=True)
                st.markdown("### [ MEDIA LOGS SHARE ]")
                
                media_markers = r'(?:<media omitted>|\[media omitted\]|image omitted|video omitted|document omitted|<media minimal>)'
                m_df = filtered_df[
                    (filtered_df['message'].str.lower().str.contains(media_markers, regex=True, na=False)) &
                    (filtered_df['is_system'] == False)
                ]
                
                if m_df.empty:
                    st.info("👾 ZERO MEDIA MARKERS IDENTIFIED.")
                else:
                    m_counts = m_df['sender'].value_counts().reset_index()
                    m_counts.columns = ['user', 'media_count']
                    
                    fig = px.pie(
                        m_counts,
                        values='media_count',
                        names='user',
                        hole=0.4,
                        color_discrete_sequence=['#39ff14', '#ff007f', '#00ffff']
                    )
                    fig.update_traces(marker=dict(line=dict(color='#000000', width=3)))
                    st.plotly_chart(style_retro_chart(fig, "Media Omission Share"), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            with col_l:
                st.markdown('<div class="retro-card" style="height: 100%;">', unsafe_allow_html=True)
                st.markdown("### [ WEB DOMAINS LOGGED ]")
                
                links_df, domain_counts = get_shared_links(filtered_df)
                if domain_counts.empty:
                    st.info("👾 ZERO SHARED LINKS SPOTTED.")
                else:
                    fig = px.bar(
                        domain_counts.head(10),
                        x='count',
                        y='domain',
                        orientation='h',
                        labels={'count': 'Times Shared', 'domain': 'Website'},
                        color_discrete_sequence=['#39ff14']
                    )
                    fig.update_yaxes(categoryorder='total ascending')
                    st.plotly_chart(style_retro_chart(fig, "Linked Domains"), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            st.markdown('<div class="retro-card">', unsafe_allow_html=True)
            st.markdown("### [ RAW LINKS DIRECTORY ]")
            
            if links_df.empty:
                st.info("👾 ZERO LINKS REGISTERED.")
            else:
                search_q = st.text_input("🔍 FILTER DATABASE BY KEYWORD:", placeholder="Search domains or senders...")
                
                display_links = links_df.copy()
                if search_q:
                    display_links = display_links[
                        display_links['url'].str.lower().str.contains(search_q.lower()) |
                        display_links['sender'].str.lower().str.contains(search_q.lower())
                    ]
                
                st.dataframe(
                    display_links[['date', 'sender', 'url']],
                    column_config={
                        "date": st.column_config.DatetimeColumn("Date Shared", format="D MMM YYYY, h:mm a"),
                        "sender": st.column_config.TextColumn("Shared By"),
                        "url": st.column_config.LinkColumn("Link URL")
                    },
                    use_container_width=True,
                    hide_index=True
                )
            st.markdown('</div>', unsafe_allow_html=True)

    # CRT Arcade footer branding
    st.markdown("""
    <div style="text-align: center; margin-top: 50px; padding: 25px; border-top: 4px dashed #39ff14;">
        <p style="color: #39ff14; font-family: 'VT323', monospace; font-size: 1.4rem; text-shadow: 2px 2px 0px #ff007f; letter-spacing: 2px;">
            === SYSTEM OK • READY TO ANALYZE ===
        </p>
    </div>
    """, unsafe_allow_html=True)
