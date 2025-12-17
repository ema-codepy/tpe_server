import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Configuração do Banco
uri = os.getenv('DATABASE_URL')
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class RegistroOcorrencia(db.Model):
    __tablename__ = 'registros'
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), default='Pendente')
    tv = db.Column(db.String(50), nullable=False)
    zona = db.Column(db.String(50), nullable=False)
    placa = db.Column(db.String(20), nullable=False)
    motivo = db.Column(db.String(100), nullable=False)
    data_inicio = db.Column(db.DateTime, default=datetime.utcnow)
    data_fim = db.Column(db.DateTime, nullable=True)
    duracao = db.Column(db.String(20), nullable=True) # Nova coluna no Python

@app.route('/api/registros', methods=['POST'])
def criar_registro():
    data = request.json
    try:
        d_ini = datetime.utcnow()
        if data.get('data_inicio'):
            try:
                d_ini = datetime.strptime(data.get('data_inicio'), "%Y-%m-%d %H:%M:%S")
            except:
                pass

        novo = RegistroOcorrencia(
            tv=data.get('tv'),
            zona=data.get('zona'),
            placa=data.get('placa_veiculo'),
            motivo=data.get('motivo'),
            status=data.get('status', 'Pendente'),
            data_inicio=d_ini,
            duracao="" # Começa vazio
        )
        db.session.add(novo)
        db.session.commit()
        return jsonify({"message": "Criado", "id": novo.id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/registros/<int:id_registro>', methods=['PUT'])
def atualizar_registro(id_registro):
    data = request.json
    registro = RegistroOcorrencia.query.get(id_registro)
    
    if not registro:
        return jsonify({"error": "Nao encontrado"}), 404

    try:
        # 1. Atualiza dados básicos
        if 'tv' in data: registro.tv = data['tv']
        if 'zona' in data: registro.zona = data['zona']
        if 'placa_veiculo' in data: registro.placa = data['placa_veiculo']
        if 'motivo' in data: registro.motivo = data['motivo']
        if 'status' in data: registro.status = data['status']
        
        # 2. Se vier data fim, atualiza
        if data.get('data_fim'):
            try:
                registro.data_fim = datetime.strptime(data.get('data_fim'), "%Y-%m-%d %H:%M:%S")
            except:
                pass
        
        # 3. Lógica de Status e Cálculo
        if registro.status == 'Pendente':
            registro.data_fim = None
            registro.duracao = ""
        
        elif registro.status == 'Concluído' and registro.data_inicio and registro.data_fim:
            # CALCULA A DURAÇÃO E SALVA NO BANCO
            diferenca = registro.data_fim - registro.data_inicio
            segundos = int(diferenca.total_seconds())
            horas = segundos // 3600
            minutos = (segundos % 3600) // 60
            registro.duracao = f"{horas}h {minutos}m"

        db.session.commit()
        return jsonify({"message": "Atualizado"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/registros', methods=['GET'])
def listar_registros():
    status_filtro = request.args.get('status')
    try:
        query = RegistroOcorrencia.query
        if status_filtro:
            query = query.filter_by(status=status_filtro)
        
        registros = query.order_by(RegistroOcorrencia.id.desc()).all()
        
        resultado = []
        for r in registros:
            # Formata datas para string
            d_ini = r.data_inicio.strftime("%Y-%m-%d %H:%M:%S") if r.data_inicio else ""
            d_fim = r.data_fim.strftime("%Y-%m-%d %H:%M:%S") if r.data_fim else ""
            
            resultado.append({
                "id": r.id,
                "status": r.status,
                "tv": r.tv,
                "zona": r.zona,
                "placa_veiculo": r.placa,
                "motivo": r.motivo,
                "data_inicio": d_ini,
                "data_fim": d_fim,
                "duracao": r.duracao # Pega direto do banco agora
            })
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return "Servidor TPE V5 (Com Duração no Banco)"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=10000)