"""
Hämtar nyckeltal från Kolada API för alla 290 kommuner och sparar som CSV.
Kör från projektets rotmapp:  python src/fetch_data.py
"""
import time
import requests
import pandas as pd

BASE_URL = "https://api.kolada.se/v3"
YEAR = 2024  # senaste året där alla nyckeltal har data för alla kommuner

# Nyckeltalen vi vill ha: Kolada-ID -> kort kolumnnamn
KPIS = {
    # Befolkning
    "N01951": "folkmangd",                  # Invånare totalt, antal
    "N02937": "befolkningstathet",          # Invånare per km²
    "N01958": "befolkningsforandring_5ar",  # Befolkningsförändring senaste 5 år, %
    "N01994": "andel_0_19",                 # Invånare 0-19 år, andel (%)
    "N01960": "andel_65plus",               # Invånare 65+, andel (%)
    "N02101": "inrikes_flyttnetto",         # Inrikes flyttnetto, andel (%)
    "N00954": "tatortsgrad",                # Tätortsgrad
    "N02279": "utpendling",                 # Utpendling, andel (%)
    "N01950": "utrikes_fodda",              # Utrikes födda 20-64 år, andel (%)
    # Ekonomi
    "N00906": "medianinkomst",              # Förvärvsinkomst 20-64 år (median), kr
    "N00900": "skattesats",                 # Skattesats totalt (%)
    "N07956": "andel_hyresratter",          # Hyresrätter, andel (%)
    # Utbildning
    "N01982": "eftergymnasial_utb",         # 25-64 år med eftergymnasial utb, andel (%)
    "N15428": "gymnasiebehorighet",         # Åk 9 behöriga till yrkesprogram, andel (%)
    # Arbetsmarknad
    "N02267": "sysselsattningsgrad",        # Sysselsättningsgrad 20-64 år, (%)
    "N01720": "arbetsloshet",               # Arbetslösa eller i åtgärd 16-64 år, andel (%)
    # Hälsa och samhälle
    "N00957": "ohalsotal",                  # Ohälsotal, dagar
    "N05401": "valdeltagande",              # Valdeltagande kommunalval, andel (%)
}


def hamta_kommuner():
    """Hämtar listan över alla kommuner (id + namn)."""
    svar = requests.get(f"{BASE_URL}/municipality", params={"type": "K", "per_page": 500})
    svar.raise_for_status()  # stoppar med ett tydligt fel om anropet misslyckas
    df = pd.DataFrame(svar.json()["values"])
    return df[["id", "title"]].rename(columns={"id": "kommun_id", "title": "kommun"})


def hamta_nyckeltal(kpi_id, kolumnnamn):
    """Hämtar ett nyckeltal för alla kommuner (och riket/regioner) ett år."""
    url = f"{BASE_URL}/data/kpi/{kpi_id}/year/{YEAR}"
    svar = requests.get(url, params={"per_page": 5000})
    svar.raise_for_status()

    rader = []
    for rad in svar.json()["values"]:
        for v in rad["values"]:
            if v["gender"] == "T":  # totalt, inte uppdelat på kön
                rader.append({"kommun_id": rad["municipality"], kolumnnamn: v["value"]})
    return pd.DataFrame(rader)


def main():
    df = hamta_kommuner()
    print(f"Hämtade {len(df)} kommuner")

    # Hämta ett nyckeltal i taget och koppla på det som en ny kolumn
    for kpi_id, kolumnnamn in KPIS.items():
        print(f"Hämtar {kpi_id} ({kolumnnamn}) ...")
        df_kpi = hamta_nyckeltal(kpi_id, kolumnnamn)
        df = df.merge(df_kpi, on="kommun_id", how="left")
        time.sleep(0.3)  # liten paus för att inte belasta API:et

    df.to_csv(f"data/raw/kolada_{YEAR}.csv", index=False)
    print(f"\nSparade data/raw/kolada_{YEAR}.csv med form {df.shape}")
    print("\nSaknade värden per kolumn:")
    print(df.isna().sum())


if __name__ == "__main__":
    main()