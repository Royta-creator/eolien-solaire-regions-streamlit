"""Quatre graphiques Plotly avec unités et informations au survol."""
import plotly.express as px
import plotly.graph_objects as go

BLUE = "#17617B"
ORANGE = "#BE6A16"


def finish(fig, height=390):
    fig.update_layout(
        template="plotly_white", height=height,
        font=dict(family="Arial, sans-serif", size=14, color="#23313C"),
        margin=dict(l=25, r=25, t=30, b=25),
        paper_bgcolor="white", plot_bgcolor="white",
        legend=dict(orientation="h", y=1.12, title_text=""),
    )
    return fig


def trend(data, metric, unit):
    fig = px.line(data, x="year", y=metric, markers=True,
                  labels={"year": "Année", metric: unit})
    fig.update_traces(line_color=BLUE, line_width=3, marker_size=8,
                      hovertemplate="%{x:.0f}<br>%{y:.2f} " + unit + "<extra></extra>")
    fig.update_xaxes(dtick=1)
    fig.update_yaxes(rangemode="tozero")
    return finish(fig)


def ranking(data, metric, unit):
    ordered = data.sort_values(metric)
    fig = px.bar(ordered, x=metric, y="region", orientation="h",
                 labels={metric: unit, "region": "Région"})
    fig.update_traces(marker_color=BLUE,
                      hovertemplate="%{y}<br>%{x:.2f} " + unit + "<extra></extra>")
    fig.update_yaxes(title="", categoryorder="array", categoryarray=ordered.region.tolist())
    return finish(fig, max(340, 31 * len(data) + 80))


def region_map(data, geo, metric, unit):
    # Le fond blanc évite toute dépendance à un serveur de tuiles ou jeton externe.
    fig = go.Figure(go.Choroplethmap(
        geojson=geo, featureidkey="properties.code", locations=data.code,
        z=data[metric], text=data.region, colorscale="Blues", zmin=0,
        marker_line_width=1, marker_line_color="#7B8B95",
        colorbar=dict(title=dict(text=unit), thickness=14),
        hovertemplate="%{text}<br>%{z:.2f} " + unit + "<extra></extra>",
    ))
    fig.update_layout(map=dict(style="white-bg", center=dict(lat=46.5, lon=2.5), zoom=4.35))
    return finish(fig, 500)


def production_mix(data, columns):
    labels = {"wind_gwh": "Éolien", "solar_gwh": "Solaire"}
    colors = {"wind_gwh": BLUE, "solar_gwh": ORANGE}
    fig = go.Figure()
    for column in columns:
        fig.add_bar(x=data.year, y=data[column] / 1000, name=labels[column],
                    marker_color=colors[column],
                    hovertemplate="%{x:.0f}<br>%{y:.2f} TWh<extra>" + labels[column] + "</extra>")
    fig.update_layout(barmode="stack", xaxis_title="Année", yaxis_title="Production (TWh)")
    fig.update_xaxes(dtick=1)
    return finish(fig)
