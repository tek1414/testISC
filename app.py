# app.py
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

from Code_base_Ploty import (
    load_data, kpis,
    fig_ca_mensuel, fig_evo_ca_par_categorie, fig_ca_par_categorie, fig_marge_par_categorie,
    fig_pie_categorie, fig_bar_type_client, fig_map_villes,
    fig_top_rentables, fig_bottom_rentables,
    COL_DATE, COL_CAT, COL_TYPE, COL_CITY
)

# ========= Données =========
CSV_PATH = r"C:\Users\User\Desktop\test ISC paris\dataset_nettoye.csv"
df = load_data(CSV_PATH)

# valeurs pour filtres
min_date = df[COL_DATE].min()
max_date = df[COL_DATE].max()
villes   = sorted([v for v in df[COL_CITY].dropna().unique() if "total" not in str(v).lower()])
cats     = sorted(df[COL_CAT].dropna().unique())
types    = sorted(df[COL_TYPE].dropna().unique())

app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = "Dashboard Ventes"

# --- Filtres globaux ---
filters_bar = dbc.Card(
    dbc.CardBody([
        html.H4("Filtres", className="mb-3"),
        dbc.Row([
            dbc.Col([
                html.Small("Période"),
                dcc.DatePickerRange(
                    id="f-date",
                    min_date_allowed=min_date, max_date_allowed=max_date,
                    start_date=min_date, end_date=max_date, display_format="DD/MM/YYYY"
                )
            ], md=3),
            dbc.Col([
                html.Small("Villes"),
                dcc.Dropdown(villes, villes, id="f-villes", multi=True)
            ], md=3),
            dbc.Col([
                html.Small("Catégories"),
                dcc.Dropdown(cats, [], id="f-cats", multi=True, placeholder="Toutes")
            ], md=3),
            dbc.Col([
                html.Small("Type de client"),
                dcc.Dropdown(types, [], id="f-types", multi=True, placeholder="Tous")
            ], md=3),
        ], className="g-3"),
    ]),
    className="mb-3 rounded-4 shadow-sm"
)

# --- Onglet 1 : Vue générale ---
tab1 = dbc.Container([
    html.H3("Vue générale", className="mt-2"),
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("CA Total"), html.H3(id="kpi-ca")]), className="shadow-sm"), md=2),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("Marge brute"), html.H3(id="kpi-marge")]), className="shadow-sm"), md=2),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("Panier moyen"), html.H3(id="kpi-panier")]), className="shadow-sm"), md=2),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("Taux de marge"), html.H3(id="kpi-taux")]), className="shadow-sm"), md=2),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("Top Produit (CA)"), html.H5(id="kpi-top-prod")]), className="shadow-sm"), md=2),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("Top Client (CA)"), html.H5(id="kpi-top-client")]), className="shadow-sm"), md=2),
    ], className="gy-3"),
    html.Hr(),
    dbc.Card(dbc.CardBody([dcc.Graph(id="fig-ca-mensuel")]), className="shadow-sm"),
], fluid=True)

# --- Onglet 2 : Produits ---
tab2 = dbc.Container([
    html.H3("Produits", className="mt-2"),
    dbc.Card(dbc.CardBody([dcc.Graph(id="fig-evo-cat")]), className="shadow-sm"),
    html.Hr(),
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([dcc.Graph(id="fig-ca-cat")]), className="shadow-sm"), md=6),
        dbc.Col(dbc.Card(dbc.CardBody([dcc.Graph(id="fig-marge-cat")]), className="shadow-sm"), md=6),
    ], className="gy-3"),
    html.Hr(),
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([dcc.Graph(id="fig-top-prod")]), className="shadow-sm"), md=6),
        dbc.Col(dbc.Card(dbc.CardBody([dcc.Graph(id="fig-bottom-prod")]), className="shadow-sm"), md=6),
    ], className="gy-3"),
    html.Hr(),
    dbc.Card(dbc.CardBody([dcc.Graph(id="fig-top-prod-ca")]), className="shadow-sm"),   # <— NEW
], fluid=True)

# --- Onglet 3 : Clients & Régions ---
tab3 = dbc.Container([
    html.H3("Clients & Régions", className="mt-2"),
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([dcc.Graph(id="fig-type")]), className="shadow-sm"), md=6),
        dbc.Col(dbc.Card(dbc.CardBody([dcc.Graph(id="fig-map")]), className="shadow-sm"), md=6),
    ], className="gy-3"),
    html.Hr(),
    dbc.Card(dbc.CardBody([dcc.Graph(id="fig-top-client-ca")]), className="shadow-sm"),  # <— NEW
], fluid=True)

app.layout = dbc.Container([
    html.H1("Tableau de bord des ventes", className="mt-3 mb-2 text-center"),
    filters_bar,
    dbc.Tabs([
        dbc.Tab(tab1, label="Vue générale"),
        dbc.Tab(tab2, label="Produits"),
        dbc.Tab(tab3, label="Clients & Régions"),
    ]),
], fluid=True)

# ========= Callback (filtres -> KPIs + graphiques) =========
@app.callback(
    Output("kpi-ca", "children"),
    Output("kpi-marge", "children"),
    Output("kpi-panier", "children"),
    Output("kpi-taux", "children"),
    Output("kpi-top-prod", "children"),
    Output("kpi-top-client", "children"),
    Output("fig-ca-mensuel", "figure"),
    Output("fig-evo-cat", "figure"),
    Output("fig-ca-cat", "figure"),
    Output("fig-marge-cat", "figure"),
    Output("fig-top-prod", "figure"),
    Output("fig-bottom-prod", "figure"),
    Output("fig-type", "figure"),
    Output("fig-map", "figure"),
    Output("fig-top-prod-ca", "figure"),     # NEW
    Output("fig-top-client-ca", "figure"),   # NEW
    Input("f-date", "start_date"),
    Input("f-date", "end_date"),
    Input("f-villes", "value"),
    Input("f-cats", "value"),
    Input("f-types", "value"),
)
def update_all(d1, d2, villes_sel, cats_sel, types_sel):
    # filtrage
    dff = df.copy()
    if d1 and d2:
        dff = dff[(dff[COL_DATE] >= pd.to_datetime(d1)) & (dff[COL_DATE] <= pd.to_datetime(d2))]
    if villes_sel:
        dff = dff[dff[COL_CITY].isin(villes_sel)]
    if cats_sel:
        dff = dff[dff[COL_CAT].isin(cats_sel)]
    if types_sel:
        dff = dff[dff[COL_TYPE].isin(types_sel)]

    # KPIs de base
    ca_total, marge_tot, panier, taux_marge = kpis(dff)
    kpi_ca     = f"{ca_total:,.0f} €".replace(",", " ")
    kpi_marge  = f"{marge_tot:,.0f} €".replace(",", " ")
    kpi_panier = f"{panier:,.0f} €".replace(",", " ")
    kpi_taux   = f"{taux_marge:.1%}"

    # KPIs top produit / top client par CA (noms)
    top_prod_s = dff.groupby("Nom du produit")["CA"].sum().sort_values(ascending=False)
    top_cli_s  = dff.groupby("Nom du client")["CA"].sum().sort_values(ascending=False)
    kpi_top_prod   = top_prod_s.index[0] if not top_prod_s.empty else "—"
    kpi_top_client = top_cli_s.index[0] if not top_cli_s.empty else "—"

    # Figures “de base”
    fig_ca   = fig_ca_mensuel(dff)
    fig_evo  = fig_evo_ca_par_categorie(dff)
    fig_cac  = fig_ca_par_categorie(dff)
    fig_marg = fig_marge_par_categorie(dff)
    fig_top  = fig_top_rentables(dff, n=5)
    fig_bot  = fig_bottom_rentables(dff, n=5)
    fig_type = fig_bar_type_client(dff)
    fig_map  = fig_map_villes(dff)

    # NEW — Classements Top par CA (barres)
    prod_ca = (dff.groupby("Nom du produit", as_index=False)["CA"]
                 .sum()
                 .sort_values("CA", ascending=False)
                 .head(10))
    fig_top_prod_ca = px.bar(prod_ca, x="Nom du produit", y="CA",
                             title="Top 10 produits par CA", text_auto=".2s")
    fig_top_prod_ca.update_layout(template="plotly_white", yaxis_tickformat=",", xaxis_tickangle=45)

    cli_ca = (dff.groupby("Nom du client", as_index=False)["CA"]
                .sum()
                .sort_values("CA", ascending=False)
                .head(10))
    fig_top_client_ca = px.bar(cli_ca, x="Nom du client", y="CA",
                               title="Top 10 clients par CA", text_auto=".2s")
    fig_top_client_ca.update_layout(template="plotly_white", yaxis_tickformat=",", xaxis_tickangle=45)

    return (kpi_ca, kpi_marge, kpi_panier, kpi_taux, kpi_top_prod, kpi_top_client,
            fig_ca, fig_evo, fig_cac, fig_marg, fig_top, fig_bot, fig_type, fig_map,
            fig_top_prod_ca, fig_top_client_ca)

# ========= Run =========
if __name__ == "__main__":
    app.run(debug=True)
