import streamlit as st
import pandas as pd
import geopandas as gpd
from streamlit_folium import st_folium
import folium
from branca.colormap import LinearColormap

# Cargar datos CSV con coma como separador decimal
df = pd.read_csv('data copy.csv', encoding='latin1', sep=';', decimal=',')

# # Debug: Imprimir las primeras filas de los datos CSV
# st.write("Primeras filas de los datos CSV:")
# st.write(df.head())

# Limpiar los datos
# df = df[df['Codigo municipio'].notna()]  # Eliminar filas sin código de municipio
# df['2022'] = pd.to_numeric(df['2022'], errors='coerce')  # Convertir a numérico
df['2022'] = pd.to_numeric(df['2022'].str.replace(',', '.'), errors='coerce')

# Convertir 'Codigo municipio' a string y limpiar espacios
# df['Codigo municipio'] = df['Codigo municipio'].astype(str).str.strip()
df['Codigo municipio'] = df['Codigo municipio'].astype(str).apply(lambda x: '0' + x if len(x) == 4 else x)

# # Debug: Verificar valores perdidos en CSV
# st.write(df['Codigo municipio'])
# st.write("Valores perdidos en CSV:")
# st.write(df.isnull())

# Cargar archivo GeoJSON de municipios de Euskadi
gdf = gpd.read_file('euskadi.geojson')

# # Debug: Imprimir las primeras filas de los datos GeoJSON
# st.write("Primeras filas de los datos GeoJSON:")
# st.write(gdf.head())

# Asegurar que 'ud_kodea' es de tipo string y limpiar si es necesario
gdf['ud_kodea'] = gdf['ud_kodea'].astype(str).str.strip()

# # Debug: Verificar valores perdidos en GeoJSON
# st.write("Valores perdidos en GeoJSON:")
# st.write(gdf.isnull().sum())

# Verificar si 'ud_kod' en GeoJSON puede coincidir con 'Codigo municipio' en CSV
common_codes = set(df['Codigo municipio']).intersection(set(gdf['ud_kodea'].astype(str)))

# # Comentado: Mostrar número de códigos comunes
# st.write(f"Número de códigos comunes para la unión: {len(common_codes)}")

if len(common_codes) == 0:
    st.error("No hay códigos comunes entre 'Codigo municipio' y 'ud_kodea'. Revisa los formatos de los códigos.")
else:
    # Unir datos con GeoJSON usando 'ud_kodea' si es el campo correcto
    gdf = gdf.merge(df, left_on='ud_kodea', right_on='Codigo municipio', how='left')

    # # Debug: Verificar la forma de los datos fusionados
    # st.write("Forma de los datos fusionados:", gdf.shape)

    # # Debug: Verificar valores perdidos después de la unión
    # st.write("Valores perdidos después de la unión:")
    # st.write(gdf.isnull().sum())

    # # Muestra una muestra de los datos fusionados
    # st.write("Muestra de los datos fusionados:")
    # st.write(gdf[['ud_kodea', 'Municipio', '2022']].head())

    # Definir la función para crear el mapa
    def create_map(gdf):
        # Crear mapa base centrado en Euskadi
        m = folium.Map(location=[42.9, -2.5], zoom_start=8)

        # # Debug: Verificar valores mínimos y máximos para el colormap
        # st.write("Valores mínimos y máximos para 2022:")
        # st.write(gdf['2022'].min(), gdf['2022'].max())

        # Verificar si hay datos válidos para crear el colormap
        if gdf['2022'].notna().any():
            # Crear un mapa de colores de verde a amarillo a rojo
            colormap = LinearColormap(
                colors=['green', 'yellow', 'red'],  # Orden cambiado para verde a rojo
                vmin=gdf['2022'].min(),
                vmax=gdf['2022'].max()
            )
            colormap.caption = 'Potencia Fotovoltaica (kW por 10,000 habitantes)'

            # Añadir capa choropleth usando el mismo esquema de colores
            choropleth = folium.Choropleth(
                geo_data=gdf,
                name='Potencia Fotovoltaica',
                data=gdf,
                columns=['ud_kodea', '2022'],
                key_on='feature.properties.ud_kodea',
                fill_color='YlOrRd',  # Cambiar si es necesario para sincronizar con colormap
                fill_opacity=0.7,
                line_opacity=0.2,
                legend_name='Potencia Fotovoltaica (kW por 10,000 habitantes)',
                highlight=True
            ).add_to(m)

            # Reemplazar la leyenda existente con la colormap personalizada
            choropleth.geojson.add_child(colormap)

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

    # Eliminar filas sin datos en '2022' y con '2022' != 0
    gdf_clean = gdf.dropna(subset=['2022'])
    gdf_clean = gdf_clean[gdf_clean['2022'] != 0]

    # Crear el mapa
    m = create_map(gdf_clean)

    # Título y descripción en Streamlit
    st.title('Potencia Fotovoltaica en Municipios de Euskadi')
    st.write('Mapa que muestra la potencia fotovoltaica instalada (kW por 10,000 habitantes) en 2022')

    # Mostrar el mapa en Streamlit usando st_folium
    st_folium(m, width=700, height=500)

    # # Debug: Verificar datos finales (excluyendo 'geometry')
    # st.write("Datos finales después de la limpieza (excluyendo 'geometry'):")
    # st.write(gdf_clean.drop(columns=['geometry']).shape)
    # st.write("Valores perdidos finales:")
    # st.write(gdf_clean.drop(columns=['geometry']).isnull().sum())

    # Escribir el número de combinaciones de códigos con datos de 2022
    st.write(f"Número de combinaciones de códigos con datos de 2022: {len(common_codes)}")