import streamlit as st
import pandas as pd
import base64
from dbfread import DBF
import plotly.express as px
import plotly.graph_objects as go

# ---------- Background Image Setup ----------
def get_base64_of_bin_file(bin_file_path):
    with open(bin_file_path, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

img_path = "mou.png"
img_base64 = get_base64_of_bin_file(img_path)

# ---------- Dark Mode Styling ----------
st.markdown(
    f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.8)),
                    url("data:image/png;base64,{img_base64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .main > div {{
        background-color: rgba(40, 40, 40, 0.75);
        padding: 2rem;
        border-radius: 1rem;
        box-shadow: 0px 0px 10px rgba(255,255,255,0.15);
    }}
    .block-container {{
        max-width: 95% !important;
        padding-left: 3rem;
        padding-right: 3rem;
    }}
    h1, h2, h3, h4, h5, h6, p, li, span {{
        color: #f5f5f5;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- App Title ----------
st.title("Himalayan Database Viewer")
st.markdown("Explore peaks, expeditions, and filtered insights from the Himalayan Database.")

# ---------- Load DBF Files ----------
@st.cache_data
def load_df(path):
    return pd.DataFrame(DBF(path, load=True, encoding='latin1'))

# File paths
peaks_path = "peaks.dbf"
exped_path = "exped.dbf"

# Load data
df_peaks = load_df(peaks_path)
df_exped = load_df(exped_path)

# ---------- Combine Data ----------
peaks_cols = ['PEAKID', 'PKNAME', 'HEIGHTM']
df_peaks_subset = df_peaks[peaks_cols]

exped_cols = [
    'EXPID', 'PEAKID', 'YEAR', 'SEASON', 'NATION', 'SPONSOR',
    'SUCCESS1', 'SUCCESS2', 'SUCCESS3', 'SUCCESS4',
    'SMTDAYS', 'TOTDAYS', 'TERMREASON', 'HIGHPOINT',
    'TOTMEMBERS', 'MDEATHS', 'O2USED', 'CAMPS'
]
df_exped_subset = df_exped[exped_cols]

# Merge
df_combined = pd.merge(df_exped_subset, df_peaks_subset, on='PEAKID', how='left')

# Reorder columns
ordered_columns = [
    'EXPID', 'PEAKID', 'PKNAME', 'HEIGHTM', 'HIGHPOINT',
    'YEAR', 'SEASON', 'NATION', 'SPONSOR',
    'SUCCESS1', 'SUCCESS2', 'SUCCESS3', 'SUCCESS4',
    'SMTDAYS', 'TOTDAYS', 'TERMREASON',
    'TOTMEMBERS', 'MDEATHS', 'O2USED', 'CAMPS'
]
df_combined = df_combined[ordered_columns]

# ---------- Filter for Top 10 Peaks ----------
top_peaks = df_combined['PEAKID'].value_counts().head(10).index.tolist()
df_combined_top10 = df_combined[df_combined['PEAKID'].isin(top_peaks)].copy()

# Convert SPONSOR to boolean: True if non-empty
df_combined_top10['SPONSOR'] = df_combined_top10['SPONSOR'].apply(lambda x: bool(str(x).strip()))

# ---------- Sidebar Table Selector ----------
table_choice = st.sidebar.selectbox(
    "📁 Navigation Menu",
    ["Expeditions", "Peaks","Top 10 Peaks (Combined)", "📊 Plotting"]
)

# ---------- Display Table ----------
if table_choice == "Expeditions":
    st.subheader("📋 Expeditions Table")
    st.dataframe(df_exped)

elif table_choice == "Peaks":
    st.subheader("🗻 Peaks Table")
    st.dataframe(df_peaks)

elif table_choice == "Top 10 Peaks (Combined)":
    st.subheader("🏔️ Top 10 Peaks by Expedition Count")
    st.dataframe(df_combined_top10)

elif table_choice == "📊 Plotting":
    st.subheader("Expedition Insights - Top 10 Peaks")

    # ---------- First Graph: Expeditions, Total Members, Avg Members ----------
    exp_counts = df_combined_top10.groupby('PKNAME').agg({
        'EXPID': 'count',
        'TOTMEMBERS': 'sum'
    }).reset_index()
    
    exp_counts.columns = ['PeakName', 'ExpeditionCount', 'TotalMembers']
    exp_counts['AvgMembersPerExpedition'] = exp_counts['TotalMembers'] / exp_counts['ExpeditionCount']
    
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=exp_counts['PeakName'],
        y=exp_counts['ExpeditionCount'],
        name='Expeditions',
        yaxis='y1'
    ))

    fig.add_trace(go.Bar(
        x=exp_counts['PeakName'],
        y=exp_counts['TotalMembers'],
        name='Total Members',
        yaxis='y1'
    ))

    fig.add_trace(go.Scatter(
        x=exp_counts['PeakName'],
        y=exp_counts['AvgMembersPerExpedition'],
        name='Avg Members per Expedition',
        mode='lines+markers',
        yaxis='y2'
    ))

    fig.update_layout(
        title='Expeditions, Total Members, and Average Team Size per Peak',
        xaxis=dict(title='Peak Name', tickangle=-45),
        yaxis=dict(title='Count (Expeditions / Total Members)', side='left'),
        yaxis2=dict(title='Average Members per Expedition', overlaying='y', side='right'),
        barmode='group',
        height=600,
        legend=dict(x=0.5, y=1.1, orientation='h', xanchor='center'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='white'
    )

    st.plotly_chart(fig, use_container_width=True)

    # ---------- Expeditions per Peak by Season ----------
    st.markdown("### Expeditions per Peak by Season")

    exp_counts_season = df_combined_top10.groupby(['PKNAME', 'SEASON']).size().reset_index(name='ExpeditionCount')
    season_colors = {
        '0': 'black',
        '1': '#2E8B57',
        '2': 'blue',
        '3': '#FF8C00',
        '4': '#9370DB'
    }
    exp_counts_season['SEASON'] = exp_counts_season['SEASON'].astype(str)

    fig2 = px.bar(
        exp_counts_season,
        x='ExpeditionCount',
        y='PKNAME',
        color='SEASON',
        color_discrete_map=season_colors,
        orientation='h',
        title='Expeditions per Peak by Season (Top 10 Peaks)',
        labels={'PKNAME': 'Peak', 'ExpeditionCount': 'Expeditions', 'SEASON': 'Season'},
        height=700
    )

    fig2.update_layout(
        yaxis=dict(categoryorder='total ascending'),
        barmode='stack',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='white'
    )

    st.plotly_chart(fig2, use_container_width=True)

    # ---------- Third Graph: Average HIGHPOINT vs HEIGHTM ----------
    st.markdown("### Average Highpoint per Peak vs Official Height")
    avg_highpoint = df_combined_top10.groupby(['PKNAME', 'HEIGHTM'])['HIGHPOINT'].mean().reset_index()
    avg_highpoint.columns = ['PeakName', 'Height_m', 'Avg_Highpoint_m']

    fig3 = px.bar(
        avg_highpoint,
        x='PeakName',
        y='Avg_Highpoint_m',
        title='Average Highpoint Reached vs Official Peak Height',
        labels={'Avg_Highpoint_m': 'Average Highpoint (m)', 'PeakName': 'Peak'},
        height=500
    )

    fig3.add_scatter(
        x=avg_highpoint['PeakName'],
        y=avg_highpoint['Height_m'],
        mode='lines+markers',
        name='Official Peak Height (m)',
        line=dict(dash='dash')
    )

    fig3.update_layout(
        xaxis_tickangle=-45,
        yaxis_range=[5000, 10000],
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='white'
    )

    st.plotly_chart(fig3, use_container_width=True)

    # ---------- Sunburst Chart: Total Members and Deaths ----------
    st.markdown("### Total Members and Deaths per Peak")

    peak_stats = df_combined_top10.groupby('PKNAME').agg({
        'TOTMEMBERS': 'sum',
        'MDEATHS': 'sum'
    }).reset_index()

    sunburst_df = peak_stats.melt(
        id_vars='PKNAME',
        value_vars=['TOTMEMBERS', 'MDEATHS'],
        var_name='Type',
        value_name='Value'
    )

    fig5 = px.sunburst(
        sunburst_df,
        path=['PKNAME', 'Type'],
        values='Value',
        title='Total Members and Deaths per Peak',
        height=700
    )

    fig5.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='white'
    )

    st.plotly_chart(fig5, use_container_width=True)
