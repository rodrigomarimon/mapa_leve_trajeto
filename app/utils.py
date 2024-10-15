import pandas as pd
import folium
from folium.plugins import HeatMap
import tempfile
import re
from datetime import timedelta
import os

def clean_coordinate(value):
    match = re.search(r'-?\d+,\d+', value)
    if match:
        return float(match.group().replace(',', '.'))
    return None

def create_google_maps_link(lat, lon):
    return f"https://www.google.com/maps?q={lat},{lon}"

def process_csv(file):

    df = pd.read_csv(file)
    print(f"DataFrame lido com {len(df)} linhas")
    if 'HR Evento' in df.columns:
        print("IDENTIFICADO ARQUIVO MOVIDA")
        df['HR Evento'] = pd.to_datetime(df['HR Evento'], format='%d/%m/%Y %H:%M')
        df['Data'] = df['HR Evento'].dt.strftime('%d/%m/%Y')
        df['Hora'] = df['HR Evento'].dt.strftime('%H:%M:%S')
        df['DataHora'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'], format='%d/%m/%Y %H:%M:%S', dayfirst=True)
        df[['Latitude', 'Longitude']] = df['Lat/Long'].str.split(',', expand=True)
        df['Latitude'] = df['Latitude'].str.replace(',', '.').astype(float)
        df['Longitude'] = df['Longitude'].str.replace(',', '.').astype(float)
        df = df[['Placa', 'Data', 'Hora', 'Velocidade', 'Latitude', 'Longitude', 'DataHora']]
        df['DateTime'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'], dayfirst=True)
        df = df.sort_values('DateTime')




    # elif 'Ignição' in df.columns:
    #     print("IDENTIFICADO ARQUIVO UNIDAS")
    #
    #     # Funções de validação
    #     def validate_date(date_str):
    #         try:
    #             return pd.to_datetime(date_str, format='%d/%m/%Y').strftime('%d/%m/%Y')
    #         except:
    #             return np.nan
    #
    #     def validate_time(time_str):
    #         try:
    #             return pd.to_datetime(time_str, format='%H:%M:%S').strftime('%H:%M:%S')
    #         except:
    #             return np.nan
    #
    #     def validate_coordinate(coord_str):
    #         try:
    #             return float(str(coord_str).replace(',', '.'))
    #         except:
    #             return np.nan
    #
    #     def validate_speed(speed_str):
    #         try:
    #             return float(speed_str)
    #         except:
    #             return np.nan
    #
    #     # Mapeamento de nomes de colunas esperados para nomes reais no DataFrame
    #     column_mapping = {
    #         'Data': next((col for col in df.columns if 'Data' in col), None),
    #         'GPS': next((col for col in df.columns if 'GPS' in col), None),
    #         'Km/h': next((col for col in df.columns if 'Km/h' in col or 'Velocidade' in col), None),
    #         'Latitude': next((col for col in df.columns if 'Latitude' in col), None),
    #         'Longitude': next((col for col in df.columns if 'Longitude' in col), None),
    #     }
    #
    #     print("Mapeamento de colunas:", column_mapping)  # Diagnóstico: imprimir o mapeamento
    #
    #     # Processar colunas
    #     for expected_name, actual_name in column_mapping.items():
    #         if actual_name:
    #             if expected_name == 'Data':
    #                 df[expected_name] = df[actual_name].apply(validate_date)
    #             elif expected_name == 'GPS':
    #                 df['Hora'] = df[actual_name].apply(validate_time)
    #             elif expected_name == 'Km/h':
    #                 df['Velocidade'] = df[actual_name].apply(validate_speed)
    #             else:
    #                 df[expected_name] = df[actual_name].apply(validate_coordinate)
    #         else:
    #             print(f"Coluna '{expected_name}' não encontrada")
    #             if expected_name == 'Data':
    #                 df['Data'] = df.index.astype(str)
    #             elif expected_name == 'GPS':
    #                 df['Hora'] = '00:00:00'
    #             elif expected_name == 'Km/h':
    #                 df['Velocidade'] = 0
    #             else:
    #                 df[expected_name] = 0
    #
    #     # Remover linhas com valores inválidos
    #     df = df.dropna(subset=['Data', 'Hora', 'Velocidade', 'Latitude', 'Longitude'])
    #
    #     # Criar coluna DateTime
    #     df['DateTime'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
    #     df = df.dropna(subset=['DateTime'])
    #
    #     # Selecionar e ordenar as colunas
    #     df = df[['Data', 'Hora', 'Velocidade', 'Latitude', 'Longitude', 'DateTime']]
    #     df = df.sort_values('DateTime')

    else:
        print('IDENTIFICADO ARQUIVO LOCALIZA')
        print(df.head())
        df['Latitude'] = df['Latitude'].apply(clean_coordinate)
        df['Longitude'] = df['Longitude'].apply(clean_coordinate)

        df = df.dropna(subset=['Latitude', 'Longitude'])
        # print(df.columns)
        df['DateTime'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'])

        df = df.sort_values('DateTime')
        # print(df.columns)

    if df.empty:
        return 'Não há pontos válidos para gerar o mapa(utils).'

    return df

    # Criando o mapa base
def create_map(df):
    print("entrou na função create_map")
    mapa = folium.Map(location=[df['Latitude'].mean(), df['Longitude'].mean()], zoom_start=12)

    # Adicionando diferentes camadas de mapa com atribuições corretas
    # folium.TileLayer('openstreetmap', name='OpenStreetMap').add_to(mapa)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google Maps Hybrid',
        name='Google Maps (Hybrid)'
    ).add_to(mapa)

    # Adicionando o mapa de calor para pontos com velocidade zero
    pontos_calor = df[df['Velocidade'] == 0][['Latitude', 'Longitude']].values.tolist()
    heat_map = HeatMap(pontos_calor, name='Mapa de Calor')
    heat_map.add_to(mapa)

    # Criando uma camada para o trajeto
    trajeto_layer = folium.FeatureGroup(name='Trajeto')

    # camada marcadores
    marcadores_layer = folium.FeatureGroup(name='Marcadores')

    # Adicionando marcadores e linha do trajeto
    coordenadas = []
    ultimo_tempo = df.iloc[0]['DateTime'] - timedelta(minutes=1.5)
    for _, row in df.iterrows():
        coordenadas.append([row['Latitude'], row['Longitude']])
        if row['DateTime'] - ultimo_tempo >= timedelta(minutes=1.5):
            google_maps_link = create_google_maps_link(row['Latitude'], row['Longitude'])
            popup_html = f"""
                Placa: {row['Placa']}<br>
                Data/Hora: {row['DateTime']}<br>
                Velocidade: {row['Velocidade']} km/h<br>
                <a href="{google_maps_link}" target="_blank">Abrir no Google Maps</a>
            """
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=folium.Popup(popup_html, max_width=300),
                # icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(marcadores_layer)
            ultimo_tempo = row['DateTime']

    # Adicionando a linha do trajeto
    folium.PolyLine(coordenadas, color="red", weight=2.5, opacity=1).add_to(trajeto_layer)

    # Adicionando a camada de trajeto ao mapa
    trajeto_layer.add_to(mapa)
    marcadores_layer.add_to(mapa)

    # Adicionando o controle de camadas
    folium.LayerControl().add_to(mapa)

    temp_map = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
    mapa.save(temp_map.name)

    # os.unlink(df.name)

    return temp_map

    # return 'Tipo de arquivo não suportado'