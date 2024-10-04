import streamlit as st
import pandas as pd
import geopandas as gpd
from streamlit_folium import st_folium
import folium
from branca.colormap import LinearColormap

# Load CSV data with comma as decimal separator
df = pd.read_csv('data copy.csv', encoding='latin1', sep=';', decimal=',')


# Convert '2022' to numeric handling thousands and decimal separators
df['2022'] = pd.to_numeric(df['2022'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce')

# Convert 'Codigo municipio' to string and clean spaces, adding '0' if it has 4 characters
df['Codigo municipio'] = df['Codigo municipio'].astype(str).apply(lambda x: '0' + x if len(x) == 4 else x)


# Load GeoJSON file of municipalities in Euskadi
gdf = gpd.read_file('euskadi.geojson')

# Ensure 'ud_kodea' is a string
gdf['ud_kodea'] = gdf['ud_kodea'].astype(str).str.strip()

# Check for common codes between CSV and GeoJSON
common_codes = set(df['Codigo municipio']).intersection(set(gdf['ud_kodea'].astype(str)))

if len(common_codes) == 0:
    st.error("No hay códigos comunes entre 'Codigo municipio' y 'ud_kodea'. Revisa los formatos de los códigos.")
else:
    # Merge data with GeoJSON using 'ud_kodea'
    gdf = gdf.merge(df, left_on='ud_kodea', right_on='Codigo municipio', how='left')

    # Definir la función para crear el mapa
    def create_map(gdf):
        # Crear mapa base centrado en Euskadi
        m = folium.Map(location=[42.9, -2.5], zoom_start=8)

        # Verificar si hay datos válidos para crear el colormap
        if gdf['2022'].notna().any():

            # Añadir capa choropleth
            choropleth = folium.Choropleth(
                geo_data=gdf,
                name='Potencia Fotovoltaica',
                data=gdf,
                columns=['ud_kodea', '2022'],
                key_on='feature.properties.ud_kodea',
                fill_color='RdYlGn',
                fill_opacity=0.7,
                line_opacity=0.2,
                legend_name='Potencia Fotovoltaica (kW por 10,000 habitantes)'
            ).add_to(m)


            # Añadir funcionalidad de hover
            folium.GeoJson(
                gdf,
                name='Etiquetas',
                style_function=lambda x: {'fillColor': 'transparent', 'color': 'transparent'},
                tooltip=folium.features.GeoJsonTooltip(
                    fields=['Municipio', '2022'],
                    aliases=['Municipio:', 'Potencia Fotovoltaica:'],
                    localize=True
                )
            ).add_to(m)
        else:
            st.warning("No hay datos válidos en la columna '2022' para mostrar en el mapa.")

        return m

    # Remove rows without data in '2022' and where '2022' != 0
    gdf_clean = gdf.dropna(subset=['2022'])
    
    # Create the map
    m = create_map(gdf_clean)

    # Title and description in Streamlit
    st.title('Potencia Fotovoltaica en Municipios de Euskadi')
    st.write('Mapa que muestra la potencia fotovoltaica instalada (kW por 10,000 habitantes) en 2022')

    # Display the map in Streamlit using st_folium
    st_folium(m, width=700, height=500)