import streamlit as st
import pandas as pd
import base64
from dbfread import DBF
import plotly.express as px

# ---------- Background Image Setup ----------
def get_base64_of_bin_file(bin_file_path):
    with open(bin_file_path, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

img_path = "mou.png"
img_base64 = get_base64_of_bin_file(img_path)

st.markdown(
    f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)),
                    url("data:image/png;base64,{img_base64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .main > div {{
        background-color: rgba(255, 255, 255, 0.85);
        padding: 2rem;
        border-radius: 1rem;
        box-shadow: 0px 0px 10px rgba(0,0,0,0.25);
    }}
    .block-container {{
        max-width: 95% !important;
        padding-left: 3rem;
        padding-right: 3rem;
    }}
    h1, p {{
        color: #111;
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
    ["Peaks", "Expeditions", "Top 10 Peaks (Combined)", "📊 Plotting"]
)

# ---------- Display Table ----------
if table_choice == "Peaks":
    st.subheader("🗻 Peaks Table")
    st.dataframe(df_peaks)

elif table_choice == "Expeditions":
    st.subheader("📋 Expeditions Table")
    st.dataframe(df_exped)

elif table_choice == "Top 10 Peaks (Combined)":
    st.subheader("🏔️ Top 10 Peaks by Expedition Count")
    with st.expander("ℹ️ Explanation of Expedition Variables"):
        st.markdown("""
         **🗂 Columns Explained**
        - `EXPID`: Unique expedition ID.
        - `PEAKID`: Code used to identify the mountain peak.
        - `PKNAME`: Name of the peak (e.g., Everest, Lhotse).
        - `HEIGHTM`: Elevation of the peak in meters.
        - `HIGHPOINT`: The highest altitude reached during the expedition.
        - `YEAR`: Year the expedition took place.
        - `SEASON`: Season of the expedition (Spring, Summer, Autumn, Winter).
        - `NATION`: Nationality of the expedition team.
        - `SPONSOR`: Whether the expedition had official sponsorship (True/False).
        - `SUCCESS1` to `SUCCESS4`: Climbing success codes.
        - `SMTDAYS`: Days taken to reach the summit.
        - `TOTDAYS`: Total duration of the expedition.
        - `TERMREASON`: Reason the expedition ended (e.g., Summit, Accident, Bad Weather).
        - `TOTMEMBERS`: Number of team members.
        - `MDEATHS`: Number of member deaths.
        - `O2USED`: Whether supplemental oxygen was used.
        - `CAMPS`: Number of camps above basecamp.
        """)
    st.dataframe(df_combined_top10)

elif table_choice == "📊 Plotting":
    st.subheader("Expedition Insights - Top 10 Peaks")
    
    # ---------- First Graph: Expeditions count ----------
    exp_counts = df_combined_top10['PKNAME'].value_counts().reset_index()
    exp_counts.columns = ['PeakName', 'ExpeditionCount']

    fig = px.bar(
        exp_counts,
        x='PeakName',
        y='ExpeditionCount',
        title='Number of Expeditions per Peak (Top 10)',
        labels={'PeakName': 'Peak', 'ExpeditionCount': 'Expeditions'},
        height=500
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)



    # ---------- Expeditions per Peak by Season (Horizontal Colored Stacked Bar with Correct Color Map) ----------
    st.markdown("### Expeditions per Peak by Season")

    # Count expeditions per Peak and Season
    exp_counts_season = df_combined_top10.groupby(['PKNAME', 'SEASON']).size().reset_index(name='ExpeditionCount')

    # Define color map for numeric SEASON
    season_colors = {
        0: 'black',
        1: '#2E8B57',
        2: 'blue',
        3: '#FF8C00',
        4: '#9370DB'
    }

    # Turn SEASON to string, because Plotly requires that for color_discrete_map
    exp_counts_season['SEASON'] = exp_counts_season['SEASON'].astype(str)

    # Update the color map keys to strings too
    season_colors = {str(k): v for k, v in season_colors.items()}

    fig2 = px.bar(
        exp_counts_season,
        x='ExpeditionCount',
        y='PKNAME',
        color='SEASON',
        color_discrete_map=season_colors,  # <- Custom colors applied
        orientation='h',
        title='Expeditions per Peak by Season (Top 10 Peaks)',
        labels={'PKNAME': 'Peak', 'ExpeditionCount': 'Expeditions', 'SEASON': 'Season'},
        height=700
    )

    fig2.update_layout(
        yaxis=dict(categoryorder='total ascending'),
        barmode='stack'
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
    yaxis_range=[5000, 10000]  # Start at 5000, no max limit (auto) 
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ---------- Fifth Graph: Sunburst of Members and Deaths per Peak ----------
    st.markdown("### Total Members and Deaths per Peak")

    # Prepare data: rectangular DataFrame
    peak_stats = df_combined_top10.groupby('PKNAME').agg({
        'TOTMEMBERS': 'sum',
        'MDEATHS': 'sum'
    }).reset_index()

    # Melt it into long format: "PeakName", "Type", "Value"
    sunburst_df = peak_stats.melt(
        id_vars='PKNAME',
        value_vars=['TOTMEMBERS', 'MDEATHS'],
        var_name='Type',
        value_name='Value'
    )

    # Build Sunburst
    fig5 = px.sunburst(
        sunburst_df,
        path=['PKNAME', 'Type'],  # hierarchy
        values='Value',
        title='Total Members and Deaths per Peak',
        height=700
    )

    st.plotly_chart(fig5, use_container_width=True)



        
