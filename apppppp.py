import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

st.set_page_config(page_title="NPIDB Scraper", layout="centered")

st.title("NPIDB Doctor/Physician Scraper")

# These are human-readable labels with mapped taxonomy URLs (examples only)
provider_types = {
    "Internal Medicine": "internal_medicine_207r00000x",
    "Family Medicine": "family_medicine_207q00000x",
    "Pediatrics": "pediatrics_208000000x",
    "Dentist": "dentist_122300000x",
    "Chiropractor": "chiropractor_111n00000x"
}

states = {
    "AL": "al", "AK": "ak", "AZ": "az", "AR": "ar", "CA": "ca", "CO": "co", "CT": "ct",
    "DE": "de", "FL": "fl", "GA": "ga", "HI": "hi", "ID": "id", "IL": "il", "IN": "in",
    "IA": "ia", "KS": "ks", "KY": "ky", "LA": "la", "ME": "me", "MD": "md", "MA": "ma",
    "MI": "mi", "MN": "mn", "MS": "ms", "MO": "mo", "MT": "mt", "NE": "ne", "NV": "nv",
    "NH": "nh", "NJ": "nj", "NM": "nm", "NY": "ny", "NC": "nc", "ND": "nd", "OH": "oh",
    "OK": "ok", "OR": "or", "PA": "pa", "RI": "ri", "SC": "sc", "SD": "sd", "TN": "tn",
    "TX": "tx", "UT": "ut", "VT": "vt", "VA": "va", "WA": "wa", "WV": "wv", "WI": "wi", "WY": "wy"
}

taxonomy_label = st.selectbox("Select provider type (specialty)", list(provider_types.keys()))
state_abbr = st.selectbox("Select state", list(states.keys()))
start_button = st.button("Scrape")

if start_button:
    st.info("Starting scraping process. Please wait...")

    specialty_slug = provider_types[taxonomy_label]
    state_slug = states[state_abbr]
    base_url = f"https://npidb.org/doctors/{specialty_slug}_{state_slug}.html"

    scraped_data = []
    page = 1

    with st.spinner("Scraping records..."):
        while len(scraped_data) < 5000:
            url = base_url.replace(".html", f"/{page}.html")
            res = requests.get(url)
            if res.status_code != 200:
                st.warning(f"No more pages found or error on page {page}.")
                break

            soup = BeautifulSoup(res.text, "html.parser")
            rows = soup.select("table.tablesorter tbody tr")

            if not rows:
                break

            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 5:
                    continue
                scraped_data.append({
                    "NPI": cols[0].text.strip(),
                    "Provider Name": cols[1].text.strip(),
                    "Specialty": taxonomy_label,
                    "Address": cols[2].text.strip(),
                    "Phone": cols[3].text.strip(),
                    "State": state_abbr
                })
                if len(scraped_data) >= 5000:
                    break

            page += 1
            time.sleep(1)

    if scraped_data:
        df = pd.DataFrame(scraped_data)
        st.success(f"Scraped {len(df)} records.")
        st.download_button("Download CSV", df.to_csv(index=False), file_name="npidb_scraped.csv", mime="text/csv")
    else:
        st.error("No data found.")
