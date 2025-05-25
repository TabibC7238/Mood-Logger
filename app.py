import streamlit as st
from streamlit_autorefresh import st_autorefresh
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import plotly.express as px
from datetime import datetime, date

# ---- GOOGLE SHEETS AUTH ----
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_CREDS"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("Mood Logger").sheet1

# ---- STREAMLIT UI ----
st.title("🧠 Mood of the Queue")
st_autorefresh(interval=10000, key="datarefresh")  # Auto-refresh every 10 seconds

# ---- MOOD LOGGER ----
st.subheader("Log a Mood")
mood = st.selectbox("How does the queue feel?", ["😊", "😠", "😕", "🎉"])
note = st.text_input("Optional note")
submit = st.button("Submit")

if submit:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([timestamp, mood, note])
    st.success("Mood logged successfully!")

# ---- DATA VISUALIZATION ----
data = pd.DataFrame(sheet.get_all_records())

if not data.empty:
    data["timestamp"] = pd.to_datetime(data["timestamp"])
    data["Mood"] = data["mood"]  # Make sure mood column is named consistently

    # Consistent mood color scheme
    emoji_colors = {
        "😠": "#8B0000",   # Dark Red
        "😕": "#e74c3c",   # Red
        "😊": "#3498db",   # Blue
        "🎉": "#0000FF"    # Dark Blue
    }

    # ---- DATE FILTER ----
    st.subheader("📅 Select Date to Explore Mood Trends")
    selected_date = st.date_input("Choose a date", value=date.today())
    filtered = data[data["timestamp"].dt.date == selected_date]

    if not filtered.empty:
        # ---- DAILY MOOD COUNTS ----
        mood_counts = filtered["Mood"].value_counts().reset_index()
        mood_counts.columns = ["Mood", "Count"]

        st.subheader("📊 Mood Counts")
        fig1 = px.bar(
            mood_counts,
            x="Mood",
            y="Count",
            color="Mood",
            color_discrete_map=emoji_colors,
            title=f"Mood Count for {selected_date}"
        )
        st.plotly_chart(fig1)

        # ---- MOOD BY HOUR ----
        st.subheader("🕒 Mood Distribution by Hour")
        filtered["hour"] = filtered["timestamp"].dt.hour
        mood_by_hour = filtered.groupby(["hour", "Mood"]).size().reset_index(name="Count")
        fig2 = px.bar(
            mood_by_hour,
            x="hour",
            y="Count",
            color="Mood",
            color_discrete_map=emoji_colors,
            barmode="group",
            title=f"Moods by Hour for {selected_date}"
        )
        st.plotly_chart(fig2)

        # ---- RAW DATA TABLE ----
        st.subheader("🧾 Raw Mood Entries")
        st.dataframe(filtered[["timestamp", "Mood", "note"]].sort_values(by="timestamp"))

    else:
        st.info("No moods logged on this date.")
else:
    st.warning("No data found in the sheet.")
