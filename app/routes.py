from crypt import methods

from flask import render_template, request, send_file
from app import app
from app.utils import process_csv, create_map
import tempfile
import  pandas as pd
@app.route('/', methods=['GET', 'POST'])
def index():
    print("entrou na funçao index")
    return render_template('index.html')

@app.route('/uploads', methods=['POST'])
def upload_file():
    print("entrou na função upload_file")
    if 'file' not in request.files:
        return 'Nenhum arquivo enviado'

    file = request.files['file']

    if file.filename == '':
        return 'Nenhum arquivo selecionado'

    if file and file.filename.endswith('.csv'):
        print("Arquivo CSV identificado")
        try:
           df = process_csv(file)
           if df.empty:
               print("DataFrame está vazio após o processamento")
               return 'Não há pontos válidos para gerar mapa'

           if df is None or df.empty:
               return 'Não há pontos válidos para gerar mapa, routes'

           temp_map = create_map(df)
           return send_file(temp_map.name, as_attachment=True)
        except pd.errors.EmptyDataError:
            return 'O arquivo CSV está vazio', 400
        except Exception as e:
            print(f"Erro ao processar o arquivo: {e}")
            return 'Erro ao processar o arquivo CSV'

    return 'Tipo de arquivo não suportado'
