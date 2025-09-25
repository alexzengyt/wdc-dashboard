import pandas as pd
from dash import Dash, html, dcc, dash_table, Input, Output
import plotly.express as px
from pathlib import Path
DATA_PATH = Path(__file__).parent / "data" / "competition.csv"
df = pd.read_csv(DATA_PATH)

# If your CSV already has a "Status" column (long format), normalize it.
# Otherwise (wide format with competitor columns), melt to long format.
if "Status" in df.columns and "Competitor" in df.columns:
    df["Status"] = df["Status"].str.lower().str.strip()
else:
    # Wide -> Long: Feature stays, competitors become rows
    df = df.melt(id_vars=["Feature"], var_name="Competitor", value_name="Notes")

    # Heuristic mapping from Notes -> Status for coloring
    def to_status(text: str) -> str:
        t = (str(text) or "").lower()
        if t in ("na", "n/a", "n⁄a"):
            return "na"
        if "need to request" in t:
            return "no"
        if "primarily" in t or "missing" in t or "lacks" in t or "for users who can read" in t:
            return "partial"
        return "yes"
    df["Status"] = df["Notes"].map(to_status)

STATUS_COLOR = {"yes": "#22c55e", "partial": "#f59e0b", "no": "#ef4444", "na": "#9ca3af"}

app = Dash(__name__, title="Competition Dashboard", suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div(
    style={"maxWidth": "1100px", "margin": "24px auto", "fontFamily": "system-ui,-apple-system,Segoe UI,Roboto"},
    children=[
        html.H2("Competition Analysis Dashboard"),
        html.Div(
            style={"display": "grid", "gridTemplateColumns": '1fr 1fr 1fr', "gap": "12px", "marginBottom": "12px"},
            children=[
                dcc.Dropdown(
                    id="competitor-filter",
                    options=[{"label": c, "value": c} for c in sorted(df["Competitor"].unique())],
                    value=sorted(df["Competitor"].unique()),
                    multi=True,
                    placeholder="Filter competitors",
                ),
                dcc.Dropdown(
                    id="feature-filter",
                    options=[{"label": f, "value": f} for f in sorted(df["Feature"].unique())],
                    value=sorted(df["Feature"].unique()),
                    multi=True,
                    placeholder="Filter features",
                ),
                dcc.RadioItems(
                    id="view-mode",
                    options=[{"label": "Table", "value": "table"}, {"label": "Heatmap", "value": "heatmap"}],
                    value="table",
                    inline=True,
                ),
            ],
        ),
        html.Div(id="main-view"),
        html.Hr(),
        html.Small("Tip: switch to Heatmap for a quick overview; use filters to focus on a subset.")
    ],
)

@app.callback(
    Output("main-view", "children"),
    Input("competitor-filter", "value"),
    Input("feature-filter", "value"),
    Input("view-mode", "value"),
)
def render_view(competitors, features, mode):
    if not competitors or not features:
        return html.Div("Please select at least one competitor and one feature.")

    dff = df[df["Competitor"].isin(competitors) & df["Feature"].isin(features)].copy()

    if mode == "table":
        wide = dff.pivot_table(index="Feature", columns="Competitor", values="Status", aggfunc="first")
        wide = wide.reindex(sorted(features), axis=0).reindex(sorted(competitors), axis=1)
        columns = [{"name": "Feature", "id": "Feature"}] + [{"name": c, "id": c} for c in wide.columns]
        data = [{"Feature": idx, **row.dropna().to_dict()} for idx, row in wide.iterrows()]

        style_conditional = []
        for comp in wide.columns:
            for status, color in STATUS_COLOR.items():
                style_conditional.append({
                    "if": {"filter_query": f'{{{comp}}} = "{status}"', "column_id": comp},
                    "backgroundColor": color, "color": "white",
                })

        return dash_table.DataTable(
            columns=columns,
            data=data,
            style_table={"overflowX": "auto"},
            style_header={"backgroundColor": "#111827", "color": "white", "fontWeight": 600},
            style_cell={"textAlign": "center", "minWidth": 120, "padding": "6px"},
            style_data_conditional=style_conditional,
            page_size=50,
            sort_action="native",
            filter_action="native",
        )

    score_map = {"yes": 3, "partial": 2, "no": 1, "na": 0}
    dff["score"] = dff["Status"].map(score_map).fillna(0)
    heat = dff.pivot_table(index="Feature", columns="Competitor", values="score", aggfunc="first")
    heat = heat.reindex(sorted(features), axis=0).reindex(sorted(competitors), axis=1)

    fig = px.imshow(
        heat,
        color_continuous_scale=["#9ca3af", "#ef4444", "#f59e0b", "#22c55e"],
        aspect="auto",
        labels=dict(color="Score"),
    )
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=600)
    fig.update_xaxes(side="top")
    return dcc.Graph(figure=fig)

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8050))
    app.run_server(host="0.0.0.0", port=port, debug=True)
