# analytics.py
import pandas as pd
import plotly.express as px


COL_DATE  = "Date de commande"
COL_CA    = "Montant de la vente"
COL_MARGE = "Marge"
COL_CAT   = "Catégorie de produit"
COL_TYPE  = "Type de client"
COL_PROD  = "Nom du produit"
COL_CITY  = "Région de vente"
COL_CMDID = "ID de commande"
CITY_COORDS = {
    "Bordeaux": (44.8378, -0.5792),
    "Lille": (50.6292, 3.0573),
    "Lyon": (45.7640, 4.8357),
    "Marseille": (43.2965, 5.3698),
    "Paris": (48.8566, 2.3522),
}

# 1) Nettoyage
def prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoie le DataFrame brut et prépare les colonnes utiles."""
    df = df.copy()
    # conversions nombre decimales
    num_cols = [COL_CA, COL_MARGE, "Prix unitaire", "Coût de revient"]
    for col in num_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(",", ".", regex=False)
            df[col] = pd.to_numeric(df[col], errors="coerce")
    # dates
    if COL_DATE in df.columns:
        try:
            df[COL_DATE] = pd.to_datetime(df[COL_DATE], format="%Y-%m-%d %H:%M:%S", errors="raise")
        except Exception:
            df[COL_DATE] = pd.to_datetime(df[COL_DATE], errors="coerce")

    # CA & Marge safe
    if COL_CA in df.columns:
        df["CA"] = pd.to_numeric(df[COL_CA], errors="coerce").fillna(0)
    else:
        raise ValueError(f"Colonne manquante : {COL_CA}")

    if COL_MARGE in df.columns:
        df["Marge"] = pd.to_numeric(df[COL_MARGE], errors="coerce").fillna(0)
    else:
        # si la marge n'existe pas, on la met à 0 pour ne pas planter les graphes
        df["Marge"] = 0.0

    return df

def load_data(csv_path: str) -> pd.DataFrame:
    """Charge un CSV brut puis applique prepare_df."""
    raw = pd.read_csv(csv_path)
    return prepare_df(raw)


# 2) KPIs
def kpis(dff: pd.DataFrame, col_cmd: str = COL_CMDID):
    nb_cmd = dff[col_cmd].nunique() if col_cmd in dff.columns else 0
    ca_total = float(dff["CA"].sum())
    marge_tot = float(dff["Marge"].sum())
    panier = (ca_total / nb_cmd) if nb_cmd > 0 else 0.0
    taux_marge = (marge_tot / ca_total) if ca_total > 0 else 0.0
    return ca_total, marge_tot, panier, taux_marge

# 3) Figures Plotly
def fig_ca_mensuel(dff: pd.DataFrame, col_date: str = COL_DATE):
    if dff.empty or dff[col_date].isna().all():
        return px.line(pd.DataFrame({col_date: [], "CA": []}), x=col_date, y="CA",
                       title="Évolution du chiffre d'affaires (mensuel)")
    ca_m = (dff.set_index(col_date).resample("ME")["CA"].sum().reset_index())
    fig = px.line(ca_m, x=col_date, y="CA", title="Évolution du chiffre d'affaires (mensuel)")
    fig.update_layout(template="plotly_white", yaxis_tickformat=",", xaxis_tickformat="%d/%m/%Y")
    return fig

def fig_pie_categorie(dff: pd.DataFrame, col_cat: str = COL_CAT):
    ca_cat = dff.groupby(col_cat, as_index=False)["CA"].sum()
    fig = px.pie(ca_cat, names=col_cat, values="CA",
                 title="Répartition du CA par catégorie", hole=0.4)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(template="plotly_white")
    return fig

def fig_bar_type_client(dff: pd.DataFrame, col_type: str = COL_TYPE):
    ca_type = dff.groupby(col_type, as_index=False)["CA"].sum()
    fig = px.bar(ca_type, x=col_type, y="CA",
                 title="Chiffre d'affaires par type de client", text_auto=".2s")
    fig.update_layout(template="plotly_white", yaxis_tickformat=",")
    return fig

def fig_map_villes(dff: pd.DataFrame, col_city: str = COL_CITY):
    city = dff.groupby(col_city, as_index=False)["CA"].sum()
    city = city[~city[col_city].str.contains("Total", case=False, na=False)].copy()
    city["lat"] = city[col_city].map(lambda v: CITY_COORDS.get(v, (None, None))[0])
    city["lon"] = city[col_city].map(lambda v: CITY_COORDS.get(v, (None, None))[1])
    city = city.dropna(subset=["lat", "lon"])
    fig = px.scatter_map(
        city, lat="lat", lon="lon", size="CA", color="CA",
        hover_name=col_city, size_max=30, zoom=4,
        center=dict(lat=46.5, lon=2.0),
        map_style="open-street-map",
        title="CA par région de vente (carte)"
    )
    return fig

def fig_evo_ca_par_categorie(dff: pd.DataFrame, col_date: str = COL_DATE, col_cat: str = COL_CAT):
    if dff.empty or dff[col_date].isna().all():
        return px.line(pd.DataFrame({col_date: [], col_cat: [], "CA": []}), x=col_date, y="CA", color=col_cat,
                       title="Évolution du CA par catégorie (mensuel)")
    evo_cat = (dff.set_index(col_date)
                 .groupby(col_cat)["CA"]
                 .resample("ME").sum()
                 .reset_index())
    fig = px.line(evo_cat, x=col_date, y="CA", color=col_cat,
                  title="Évolution du CA par catégorie (mensuel)")
    fig.update_layout(template="plotly_white", yaxis_tickformat=",", xaxis_tickformat="%d/%m/%Y")
    return fig

def fig_ca_par_categorie(dff: pd.DataFrame, col_cat: str = COL_CAT):
    ca_cat = dff.groupby(col_cat, as_index=False)["CA"].sum().sort_values("CA", ascending=False)
    fig = px.bar(ca_cat, x=col_cat, y="CA", title="CA par catégorie")
    fig.update_layout(template="plotly_white", yaxis_tickformat=",", xaxis_tickangle=45)
    return fig

def fig_marge_par_categorie(dff: pd.DataFrame, col_cat: str = COL_CAT):
    marge_cat = dff.groupby(col_cat, as_index=False)["Marge"].sum().sort_values("Marge", ascending=False)
    fig = px.bar(marge_cat, x=col_cat, y="Marge", title="Marge nette par catégorie")
    fig.update_layout(template="plotly_white", yaxis_tickformat=",", xaxis_tickangle=45)
    return fig

def fig_top_rentables(dff: pd.DataFrame, col_prod: str = COL_PROD, n: int = 5):
    prod = dff.groupby(col_prod, as_index=False)[["CA", "Marge"]].sum()
    prod = prod[prod["CA"] > 0].copy()
    prod["Rentabilité"] = prod["Marge"] / prod["CA"]
    view = prod.sort_values("Rentabilité", ascending=False).head(n)
    fig = px.bar(view, x=col_prod, y="Rentabilité",
                 title=f"Top {n} produits (rentabilité)", text_auto=".1%")
    fig.update_layout(template="plotly_white", xaxis_tickangle=45)
    return fig

def fig_bottom_rentables(dff: pd.DataFrame, col_prod: str = COL_PROD, n: int = 5):
    prod = dff.groupby(col_prod, as_index=False)[["CA", "Marge"]].sum()
    prod = prod[prod["CA"] > 0].copy()
    prod["Rentabilité"] = prod["Marge"] / prod["CA"]
    view = prod.sort_values("Rentabilité", ascending=True).head(n)
    fig = px.bar(view, x=col_prod, y="Rentabilité",
                 title=f"Bottom {n} produits (rentabilité)", text_auto=".1%")
    fig.update_layout(template="plotly_white", xaxis_tickangle=45)
    return fig
