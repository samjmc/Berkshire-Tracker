import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

# Constants
CIK = "0001067983"
HEADERS = {"User-Agent": "Samuel McDonnell (samuel.mcdonnell@example.com)"}

def fetch_berkshire_filings():
    url = f"https://data.sec.gov/submissions/CIK{CIK}.json"
    res = requests.get(url, headers=HEADERS)
    data = res.json()
    recent = data['filings']['recent']
    filings = []
    for form, acc_num in zip(recent['form'], recent['accessionNumber']):
        if form == "13F-HR":
            acc_clean = acc_num.replace("-", "")
            detail_url = f"https://www.sec.gov/Archives/edgar/data/{CIK}/{acc_clean}/index.json"
            filings.append({"accession": acc_num, "url": detail_url, "accession_clean": acc_clean})
    return filings

def get_info_table_url(filing):
    try:
        index_url = filing['url']
        res = requests.get(index_url, headers=HEADERS)
        index_data = res.json()
        for file in index_data.get("directory", {}).get("item", []):
            name = file.get("name", "")
            if name.endswith(".xml"):
                file_url = f"https://www.sec.gov/Archives/edgar/data/{CIK}/{filing['accession_clean']}/{name}"
                try:
                    content = requests.get(file_url, headers=HEADERS).content
                    if b"<informationTable" in content:
                        return file_url
                except:
                    continue
        st.warning("⚠️ Could not find infotable XML on the filing detail page.")
        return None
    except Exception as e:
        st.error(f"Error loading filing detail JSON: {e}")
        return None

def parse_13f_xml(xml_url):
    try:
        response = requests.get(xml_url, headers=HEADERS)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        ns = {'ns': 'http://www.sec.gov/edgar/document/thirteenf/informationtable'}
        data = []
        for info in root.findall("ns:infoTable", ns):
            row = {
                "nameOfIssuer": info.findtext("ns:nameOfIssuer", default="", namespaces=ns),
                "cusip": info.findtext("ns:cusip", default="", namespaces=ns),
                "value ($)": int(info.findtext("ns:value", default="0", namespaces=ns)),
                "shares": int(info.find("ns:shrsOrPrnAmt/ns:sshPrnamt", ns).text or 0),
                "investmentDiscretion": info.findtext("ns:investmentDiscretion", default="", namespaces=ns),
                "votingAuthority (Sole)": int(info.find("ns:votingAuthority/ns:Sole", ns).text or 0)
            }
            data.append(row)
        return pd.DataFrame(data)
    except Exception as e:
        st.warning(f"⚠️ Error parsing XML: {e}")
        return pd.DataFrame()

@st.cache_data
def load_data():
    filings = fetch_berkshire_filings()
    if len(filings) < 2:
        st.error("❌ Not enough filings found to compare.")
        return None, None

    latest, previous = filings[0], filings[1]
    xml_url_1 = get_info_table_url(latest)
    xml_url_2 = get_info_table_url(previous)

    df_latest = parse_13f_xml(xml_url_1) if xml_url_1 else pd.DataFrame()
    df_previous = parse_13f_xml(xml_url_2) if xml_url_2 else pd.DataFrame()
    return df_latest, df_previous

def compare_holdings(df1, df2):
    merged = pd.merge(df1, df2, on="cusip", how="outer", suffixes=("_latest", "_previous"))
    merged["valueChange"] = merged["value ($)_latest"].fillna(0) - merged["value ($)_previous"].fillna(0)
    merged["shareChange"] = merged["shares_latest"].fillna(0) - merged["shares_previous"].fillna(0)

    merged["valuePctChange"] = (merged["valueChange"] / merged["value ($)_previous"].replace(0, pd.NA)) * 100
    merged["sharePctChange"] = (merged["shareChange"] / merged["shares_previous"].replace(0, pd.NA)) * 100

    def trend_icon(val):
        if pd.isna(val): return "➖"
        return "📈" if val > 0 else "📉" if val < 0 else "➖"

    merged["valueTrend"] = merged["valueChange"].apply(trend_icon)
    merged["shareTrend"] = merged["shareChange"].apply(trend_icon)

    return merged.sort_values("valueChange", ascending=False)

# --- Streamlit App ---
st.set_page_config(page_title="Berkshire Hathaway 13F Tracker", layout="wide")
st.title("📈 Berkshire Hathaway Holdings (13F Filing)")

df_latest, df_previous = load_data()

if df_latest is not None and not df_latest.empty:
    col1, col2 = st.columns(2)
    col1.metric("🧾 Stocks Tracked", len(df_latest))
    col2.metric("💼 Portfolio Value ($B)", f"{df_latest['value ($)'].sum() / 1e9:.2f}")

    N = st.slider("Top N holdings", 5, 50, 10)

    top = (
        df_latest.groupby(["cusip", "nameOfIssuer"], as_index=False)
        .agg({
            "value ($)": "sum",
            "shares": "sum",
            "investmentDiscretion": "first",
            "votingAuthority (Sole)": "sum"
        })
        .sort_values("value ($)", ascending=False)
        .head(N)
    )

    st.dataframe(top, use_container_width=True)
    st.download_button("📄 Export Top Holdings to CSV", top.to_csv(index=False), file_name="top_holdings.csv")

    st.markdown("---")
    st.subheader("🔁 Compare Most Recent 13F Filings")

    if df_previous is not None and not df_previous.empty:
        changes = compare_holdings(df_latest, df_previous)

        show_new_dropped = st.checkbox("📛 Show Only New / Dropped Positions", value=True)

        changes["is_new"] = changes["value ($)_previous"].isna()
        changes["is_dropped"] = changes["value ($)_latest"].isna()
        changes["valuePctChange"] = changes["valuePctChange"].fillna(-100)

        total_change = changes["valueChange"].sum()
        st.metric("hello", f"{total_change / 1e9:.2f}")

        filtered = changes.copy()
        if show_new_dropped:
            filtered = filtered[filtered["is_new"] | filtered["is_dropped"]]

        st.dataframe(
            filtered[
                [
                    'nameOfIssuer_latest', 'nameOfIssuer_previous', 'cusip',
                    'value ($)_latest', 'value ($)_previous', 'valueChange', 'valuePctChange', 'valueTrend',
                    'shares_latest', 'shares_previous', 'shareChange', 'sharePctChange', 'shareTrend'
                ]
            ],
            use_container_width=True
        )
    else:
        st.warning("⚠️ Could not load previous filing for comparison.")
else:
    st.error("❌ Could not load latest holdings data.")

st.caption("Data Source: SEC EDGAR")
