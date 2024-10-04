import streamlit as st
import pandas as pd
import geopandas as gpd
from streamlit_folium import st_folium
import folium
from branca.colormap import LinearColormap

# Load CSV data with comma as decimal separator
df = pd.read_csv('data copy.csv', encoding='latin1', sep=';', decimal=',')

# Clean data: Convert '2022' to numeric and 'Codigo municipio' to string
df['2022'] = pd.to_numeric(df['2022'].str.replace(',', '.'), errors='coerce')
df['Codigo municipio'] = df['Codigo municipio'].astype(str).apply(lambda x: '0' + x if len(x) == 4 else x)

# Load GeoJSON file of municipalities in Euskadi
gdf = gpd.read_file('euskadi.geojson')

# Ensure 'ud_kodea' is a string
gdf['ud_kodea'] = gdf['ud_kodea'].astype(str).str.strip()

# Check for common codes between CSV and GeoJSON
common_codes = set(df['Codigo municipio']).intersection(set(gdf['ud_kodea']))

if len(common_codes) == 0:
    st.error("No common codes between 'Codigo municipio' and 'ud_kodea'. Check the formats.")
else:
    # Merge data with GeoJSON using 'ud_kodea'
    gdf = gdf.merge(df, left_on='ud_kodea', right_on='Codigo municipio', how='left')

    # Define function to create the map
    def create_map(gdf):
        # Create base map centered on Euskadi
        m = folium.Map(location=[42.9, -2.5], zoom_start=8)

        # Check if there are valid data for colormap
        if gdf['2022'].notna().any():
            # Create a colormap from green to yellow to red
            colormap = LinearColormap(
                colors=['green', 'yellow', 'red'],
                vmin=gdf['2022'].min(),
                vmax=gdf['2022'].max()
            )
            colormap.caption = 'Potencia Fotovoltaica (kW por 10,000 habitantes)'

            # Add choropleth layer using the same color scheme
            choropleth = folium.Choropleth(
                geo_data=gdf,
                name='Potencia Fotovoltaica',
                data=gdf,
                columns=['ud_kodea', '2022'],
                key_on='feature.properties.ud_kodea',
                fill_color='YlOrRd',
                fill_opacity=0.7,
                line_opacity=0.2,
                legend_name='Potencia Fotovoltaica (kW por 10,000 habitantes)',
                highlight=True
            ).add_to(m)

            # Replace existing legend with custom colormap
            choropleth.geojson.add_child(colormap)

            # Add hover functionality
            folium.GeoJson(
                gdf,
                name='Labels',
                style_function=lambda x: {'fillColor': 'transparent', 'color': 'transparent'},
                tooltip=folium.features.GeoJsonTooltip(
                    fields=['Municipio', '2022'],
                    aliases=['Municipio:', 'Potencia Fotovoltaica:'],
                    localize=True
                )
            ).add_to(m)
        else:
            st.warning("No valid data in the column '2022' to display on the map.")

        return m

    # Remove rows without data in '2022' and where '2022' != 0
    gdf_clean = gdf.dropna(subset=['2022'])
    gdf_clean = gdf_clean[gdf_clean['2022'] != 0]

    # Create the map
    m = create_map(gdf_clean)

    # Title and description in Streamlit
    st.title('Potencia Fotovoltaica en Municipios de Euskadi')
    st.write('Mapa que muestra la potencia fotovoltaica instalada (kW por 10,000 habitantes) en 2022')

    # Display the map in Streamlit using st_folium
    st_folium(m, width=700, height=500)

    # Write the number of code combinations with data from 2022
    st.write(f"Número de combinaciones de códigos con datos de 2022: {len(common_codes)}")