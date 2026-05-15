from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import re
import math
import time
from unidecode import unidecode
from datetime import datetime, timedelta
from urllib.parse import quote
import sys
import os

# Adiciona o diretório pai ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importa os dicionários dos arquivos separados
from dicionario_quimico import DICIONARIO_QUIMICO
from compostos_especiais import COMPOSTOS_ESPECIAIS, FORMULAS_GRANDES

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Cache em memória
class Cache:
    def __init__(self, timeout_seconds=3600):
        self.data = {}
        self.timeout = timedelta(seconds=timeout_seconds)
    
    def get(self, key):
        if key in self.data:
            item, timestamp = self.data[key]
            if datetime.now() - timestamp < self.timeout:
                return item
            del self.data[key]
        return None
    
    def set(self, key, value):
        self.data[key] = (value, datetime.now())

cache_store = Cache(timeout_seconds=3600)

# ============================================
# TRADUTOR QUÍMICO
# ============================================
class TradutorQuimico:
    @staticmethod
    def traduzir(nome):
        nome_lower = nome.lower().strip()
        nome_sem_acento = unidecode(nome_lower)
        
        if nome_lower in DICIONARIO_QUIMICO:
            return DICIONARIO_QUIMICO[nome_lower]
        
        if nome_sem_acento in DICIONARIO_QUIMICO:
            return DICIONARIO_QUIMICO[nome_sem_acento]
        
        palavras = nome_lower.split()
        palavras_traduzidas = []
        for palavra in palavras:
            if palavra in DICIONARIO_QUIMICO:
                palavras_traduzidas.append(DICIONARIO_QUIMICO[palavra])
            elif palavra not in ['de', 'da', 'do', 'das', 'dos', 'e', 'a', 'o', 'as', 'os']:
                palavras_traduzidas.append(palavra)
        
        if palavras_traduzidas:
            traducao = ' '.join(palavras_traduzidas)
            if traducao != nome_lower:
                return traducao
        
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                'client': 'gtx',
                'sl': 'pt',
                'tl': 'en',
                'dt': 't',
                'q': nome
            }
            response = requests.get(url, params=params, timeout=2)
            if response.status_code == 200:
                data = response.json()
                return data[0][0][0]
        except:
            pass
        
        return nome

# ============================================
# DETECTOR DE TIPO
# ============================================
class DetectorTipoBusca:
    @staticmethod
    def detectar_tipo(query):
        query = query.strip()
        
        if query.isdigit():
            return 'CID'
        elif query.upper() in FORMULAS_GRANDES:
            return 'FORMULA_GRANDE'
        elif re.match(r'^[A-Za-z][A-Za-z0-9]*$', query):
            if len(re.findall(r'\d+', query)) > 5:
                return 'FORMULA_GRANDE'
            return 'FORMULA_SIMPLES'
        elif re.search(r'[\(\)\[\]·]', query):
            return 'FORMULA_COMPLEXA'
        elif ' ' in query or len(query) > 3:
            return 'NOME_QUIMICO'
        else:
            return 'DESCONHECIDO'

# ============================================
# API PUBCHEM
# ============================================
class PubChemAPI:
    @staticmethod
    def buscar_por_formula(formula):
        formula = formula.strip()
        url_cid = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/fastformula/{quote(formula)}/cids/txt"
        
        try:
            response = requests.get(url_cid, timeout=8)
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                if lines and lines[0].isdigit():
                    cid = lines[0]
                    return PubChemAPI.buscar_por_cid(cid)
        except:
            pass
        return None
    
    @staticmethod
    def buscar_por_nome(nome):
        nome_traduzido = TradutorQuimico.traduzir(nome)
        
        variacoes = [
            nome_traduzido,
            nome_traduzido.lower(),
            nome_traduzido.capitalize(),
            nome_traduzido.replace(' ', ''),
        ]
        
        for variacao in set(variacoes):
            if len(variacao) < 2:
                continue
            
            try:
                url_cid = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{quote(variacao)}/cids/txt"
                response = requests.get(url_cid, timeout=8)
                if response.status_code == 200:
                    lines = response.text.strip().split('\n')
                    if lines and lines[0].isdigit():
                        cid = lines[0]
                        return PubChemAPI.buscar_por_cid(cid)
            except:
                continue
        
        return None
    
    @staticmethod
    def buscar_por_cid(cid):
        url_sdf = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF?record_type=3d"
        
        try:
            response = requests.get(url_sdf, headers={'Accept': 'chemical/x-mdl-sdfile'}, timeout=10)
            if response.status_code == 200:
                return PubChemAPI.parse_sdf(response.text)
        except:
            pass
        
        try:
            url_sdf_2d = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF"
            response = requests.get(url_sdf_2d, headers={'Accept': 'chemical/x-mdl-sdfile'}, timeout=10)
            if response.status_code == 200:
                return PubChemAPI.parse_sdf(response.text)
        except:
            pass
        
        return None
    
    @staticmethod
    def buscar_automatico(query):
        query = query.strip()
        
        cached = cache_store.get(query)
        if cached:
            return cached
        
        resultado = None
        
        query_lower = query.lower()
        if query_lower in COMPOSTOS_ESPECIAIS:
            dados = COMPOSTOS_ESPECIAIS[query_lower]
            resultado = PubChemAPI.buscar_por_cid(dados['cid'])
            if resultado:
                cache_store.set(query, resultado)
                return resultado
        
        resultado = PubChemAPI.buscar_por_nome(query)
        if resultado:
            cache_store.set(query, resultado)
            return resultado
        
        resultado = PubChemAPI.buscar_por_formula(query)
        if resultado:
            cache_store.set(query, resultado)
            return resultado
        
        return None
    
    @staticmethod
    def parse_sdf(sdf_text):
        lines = sdf_text.strip().split('\n')
        if len(lines) < 4:
            return None
        
        atom_count, bond_count, start_line = 0, 0, 0
        
        for i in range(min(100, len(lines))):
            line = lines[i]
            if len(line) >= 6 and line[0:3].strip().isdigit():
                try:
                    atom_count = int(line[0:3].strip())
                    bond_count = int(line[3:6].strip())
                    start_line = i + 1
                    break
                except:
                    continue
        
        if atom_count == 0 or atom_count > 5000:
            return None
        
        while start_line < len(lines) and len(lines[start_line].strip()) < 5:
            start_line += 1
        
        atoms = []
        for i in range(start_line, min(start_line + atom_count, len(lines))):
            line = lines[i]
            if len(line) >= 34:
                try:
                    x = float(line[0:10].strip())
                    y = float(line[10:20].strip())
                    z = float(line[20:30].strip())
                    element = line[31:34].strip()
                    element_match = re.match(r'([A-Z][a-z]?)', element)
                    if element_match:
                        element = element_match.group(1)
                    if element and element[0].isalpha():
                        atoms.append({'element': element, 'x': x, 'y': y, 'z': z})
                except:
                    continue
        
        if len(atoms) == 0:
            return None
        
        bonds = []
        bond_start = start_line + atom_count
        for i in range(bond_start, min(bond_start + bond_count, len(lines))):
            line = lines[i]
            if len(line) >= 9:
                try:
                    a1 = int(line[0:3].strip()) - 1
                    a2 = int(line[3:6].strip()) - 1
                    bond_type = int(line[6:9].strip())
                    if 0 <= a1 < len(atoms) and 0 <= a2 < len(atoms):
                        bonds.append({'atom1': a1, 'atom2': a2, 'type': bond_type})
                except:
                    continue
        
        if len(bonds) == 0 and len(atoms) > 1:
            bonds = PubChemAPI.auto_bonds(atoms)
        
        return {
            'atoms': atoms,
            'bonds': bonds,
            'atom_count': len(atoms),
            'bond_count': len(bonds)
        }
    
    @staticmethod
    def auto_bonds(atoms):
        bonds = []
        for i in range(len(atoms)):
            for j in range(i + 1, len(atoms)):
                dx = atoms[i]['x'] - atoms[j]['x']
                dy = atoms[i]['y'] - atoms[j]['y']
                dz = atoms[i]['z'] - atoms[j]['z']
                dist = math.sqrt(dx*dx + dy*dy + dz*dz)
                if dist < 2.0:
                    bonds.append({'atom1': i, 'atom2': j, 'type': 1})
        return bonds

# ============================================
# ROTAS DA API
# ============================================

# ROTA PRINCIPAL - SERVE O HTML
@app.route('/')
def serve_index():
    return send_from_directory(os.path.dirname(__file__), 'index.html')

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({'status': 'ok', 'message': 'API Química na Vercel!'})

@app.route('/api/molecule/<path:query>', methods=['GET'])
def get_molecule(query):
    start_time = time.time()
    resultado = PubChemAPI.buscar_automatico(query)
    elapsed = time.time() - start_time
    
    if resultado:
        return jsonify({
            'success': True,
            'meta': {
                'query_original': query,
                'tempo_busca': f"{elapsed:.2f}s",
                'fonte': 'PubChem API + Dicionário PT'
            },
            'data': resultado
        })
    else:
        return jsonify({
            'success': False,
            'error': f'Não foi possível encontrar: "{query}"'
        }), 404

@app.route('/api/traduzir/<path:texto>', methods=['GET'])
def test_traducao(texto):
    traduzido = TradutorQuimico.traduzir(texto)
    return jsonify({'original': texto, 'traduzido': traduzido})

@app.route('/api/compostos', methods=['GET'])
def listar_compostos_especiais():
    return jsonify({
        'total': len(COMPOSTOS_ESPECIAIS),
        'compostos': list(COMPOSTOS_ESPECIAIS.keys())
    })

@app.route('/api/cid/<int:cid>', methods=['GET'])
def get_by_cid(cid):
    resultado = PubChemAPI.buscar_por_cid(cid)
    if resultado:
        return jsonify({'success': True, 'data': resultado})
    return jsonify({'success': False, 'error': f'CID {cid} não encontrado'}), 404

# Handler para Vercel
app = app

if __name__ == '__main__':
    app.run(debug=True)