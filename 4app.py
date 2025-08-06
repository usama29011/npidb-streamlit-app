import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

st.set_page_config(page_title="NPIDB Doctor Scraper", layout="centered")
st.title("NPIDB Doctor Profile Scraper")

# Dynamically fetch specialties from taxonomy page and clean them
@st.cache_data
def get_specialties():
    url = "https://npidb.org/taxonomy/"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    taxonomy_map = {}
    for a in soup.select("table tbody tr a"):
        name = a.text.strip()
        href = a.get("href")
        if "taxonomy" in href and "_" in href:
            slug = href.split("/")[-1].replace(".html", "")
            # Strip off category prefix if present
            if " - " in name:
                name = name.split(" - ")[-1].strip()
            taxonomy_map[name] = slug
    return taxonomy_map

specialties = get_specialties()

states = {
    "AL": "al", "AK": "ak", "AZ": "az", "AR": "ar", "CA": "ca", "CO": "co", "CT": "ct",
    "DE": "de", "FL": "fl", "GA": "ga", "HI": "hi", "ID": "id", "IL": "il", "IN": "in",
    "IA": "ia", "KS": "ks", "KY": "ky", "LA": "la", "ME": "me", "MD": "md", "MA": "ma",
    "MI": "mi", "MN": "mn", "MS": "ms", "MO": "mo", "MT": "mt", "NE": "ne", "NV": "nv",
    "NH": "nh", "NJ": "nj", "NM": "nm", "NY": "ny", "NC": "nc", "ND": "nd", "OH": "oh",
    "OK": "ok", "OR": "or", "PA": "pa", "RI": "ri", "SC": "sc", "SD": "sd", "TN": "tn",
    "TX": "tx", "UT": "ut", "VT": "vt", "VA": "va", "WA": "wa", "WV": "wv", "WI": "wi", "WY": "wy"
}

specialty_label = st.selectbox("Select provider specialty", sorted(specialties.keys()))
state_abbr = st.selectbox("Select state", list(states.keys()))

if st.button("Scrape"):
    st.info("Scraping in progress. Please wait...")

    slug = specialties[specialty_label]
    state_slug = states[state_abbr]
    base_url = f"https://npidb.org/doctors/{slug}_{state_slug}.html"

    scraped_data = []
    page = 1

    with st.spinner("Scraping profiles..."):
        while len(scraped_data) < 5000:
            url = base_url.replace(".html", f"/{page}.html")
            res = requests.get(url)
            if res.status_code != 200:
                st.warning(f"Failed to load page {page}")
                break

            soup = BeautifulSoup(res.text, "html.parser")
            rows = soup.select("table.tablesorter tbody tr")
            if not rows:
                break

            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 4:
                    continue

                profile_link = cols[1].find("a")
                if not profile_link:
                    continue

                profile_url = "https://npidb.org" + profile_link.get("href")

                # Visit individual profile page
                prof_res = requests.get(profile_url)
                if prof_res.status_code != 200:
                    continue

                prof_soup = BeautifulSoup(prof_res.text, "html.parser")

                # Get phone & fax from profile table
                phone = fax = ""
                for row2 in prof_soup.select("table.table tr"):
                    cells = row2.find_all("td")
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        if "Phone" in label:
                            phone = value
                        elif "Fax" in label:
                            fax = value

                scraped_data.append({
                    "NPI": cols[0].text.strip(),
                    "Provider Name": cols[1].text.strip(),
                    "Address": cols[2].text.strip(),
                    "Phone": phone,
                    "Fax": fax,
                    "State": state_abbr,
                    "Specialty": specialty_label
                })

                if len(scraped_data) >= 5000:
                    break

            page += 1
            time.sleep(1)

    if scraped_data:
        df = pd.DataFrame(scraped_data)
        st.success(f"Scraped {len(df)} records.")
        st.download_button("Download CSV", df.to_csv(index=False), file_name="npidb_profiles.csv", mime="text/csv")
    else:
        st.error("No data found.")
