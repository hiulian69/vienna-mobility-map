"""Fetch, clean, and map Vienna public transit stops from the City of Vienna's open WFS API."""

import geopandas as gpd
import folium
import requests

WFS_URL = "https://data.wien.gv.at/daten/geo"
TYPE_NAME = "ogdwien:HALTESTELLEWLOGD"  # Haltestellen Wiener Linien (public transit stops)
VIENNA_CENTER = (48.2082, 16.3738)


def fetch_stops() -> gpd.GeoDataFrame:
    """Pull the Wiener Linien stop locations layer via WFS GetFeature, as GeoJSON."""
    params = {
        "service": "WFS",
        "version": "1.1.0",
        "request": "GetFeature",
        "typeName": TYPE_NAME,
        "srsName": "EPSG:4326",
        "outputFormat": "json",
    }
    response = requests.get(WFS_URL, params=params, timeout=30)
    response.raise_for_status()
    return gpd.GeoDataFrame.from_features(response.json()["features"], crs="EPSG:4326")


def clean_stops(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Drop empty geometries/duplicates and keep only the columns the map needs."""
    gdf = gdf[gdf.geometry.notna()].drop_duplicates(subset=["OBJECTID"])
    gdf = gdf.rename(columns={"BEZEICHNUNG": "stop_name", "WL_NUMMER": "line_number"})
    return gdf[["OBJECTID", "stop_name", "line_number", "geometry"]]


def build_map(gdf: gpd.GeoDataFrame) -> folium.Map:
    """Render stops as an interactive Folium map centered on Vienna."""
    m = folium.Map(location=VIENNA_CENTER, zoom_start=12, tiles="cartodbpositron")
    stops = folium.FeatureGroup(name="Public transit stops")
    for _, row in gdf.iterrows():
        folium.CircleMarker(
            location=(row.geometry.y, row.geometry.x),
            radius=3,
            color="#1f6feb",
            fill=True,
            fill_opacity=0.8,
            popup=folium.Popup(f"<b>{row.stop_name}</b><br>Line {row.line_number}", max_width=200),
        ).add_to(stops)
    stops.add_to(m)
    folium.LayerControl().add_to(m)
    return m


if __name__ == "__main__":
    stops_gdf = clean_stops(fetch_stops())
    print(f"Fetched {len(stops_gdf)} transit stops")
    mobility_map = build_map(stops_gdf)
    mobility_map.save("output/vienna_mobility_map.html")
    print("Saved output/vienna_mobility_map.html")
