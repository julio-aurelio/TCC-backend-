from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
import math
import time
from unidecode import unidecode

app = Flask(__name__)
CORS(app)

# Cache em memória
cache = {}
from datetime import datetime, timedelta

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


class TradutorAutomatico:
    """Tradutor automático português -> inglês para química"""
    
    # Dicionário de fallback para casos comuns (mais rápido que API)
    FALLBACK = {
        "amonia": "ammonia", "amônia": "ammonia",
        "agua": "water", "água": "water",
        "metano": "methane", "etano": "ethane", "propano": "propane",
        "butano": "butane", "pentano": "pentane", "hexano": "hexane",
        "heptano": "heptane", "octano": "octane", "nonano": "nonane", "decano": "decane",
        "metanol": "methanol", "etanol": "ethanol", "propanol": "propanol", "butanol": "butanol",
        "benzeno": "benzene", "tolueno": "toluene", "fenol": "phenol",
        "sacarose": "sucrose", "glicose": "glucose", "frutose": "fructose",
        "acetona": "acetone", "acido": "acid", "ácido": "acid",
        "acido acetico": "acetic acid", "ácido acético": "acetic acid",
        "acido sulfurico": "sulfuric acid", "ácido sulfúrico": "sulfuric acid",
        "acido cloridrico": "hydrochloric acid", "ácido clorídrico": "hydrochloric acid",
        "acido nitrico": "nitric acid", "ácido nítrico": "nitric acid",
        "acido fosforico": "phosphoric acid", "ácido fosfórico": "phosphoric acid",
        "hidroxido de sodio": "sodium hydroxide", "hidróxido de sódio": "sodium hydroxide",
        "cloreto de sodio": "sodium chloride", "cloreto de sódio": "sodium chloride",
        "carbonato de calcio": "calcium carbonate", "carbonato de cálcio": "calcium carbonate",
        "bicarbonato de sodio": "sodium bicarbonate", "bicarbonato de sódio": "sodium bicarbonate",
        "peroxido de hidrogenio": "hydrogen peroxide", "peróxido de hidrogênio": "hydrogen peroxide",
    }
    
    @staticmethod
    def traduzir(texto):
        """Traduz texto do português para inglês"""
        texto = texto.lower().strip()
        texto_sem_acento = unidecode(texto)
        
        # Verifica fallback primeiro (mais rápido)
        if texto in TradutorAutomatico.FALLBACK:
            return TradutorAutomatico.FALLBACK[texto]
        if texto_sem_acento in TradutorAutomatico.FALLBACK:
            return TradutorAutomatico.FALLBACK[texto_sem_acento]
        
        # Tenta API do Google Translate (gratuita)
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                'client': 'gtx',
                'sl': 'pt',
                'tl': 'en',
                'dt': 't',
                'q': texto
            }
            response = requests.get(url, params=params, timeout=3)
            if response.status_code == 200:
                data = response.json()
                traduzido = data[0][0][0]
                if traduzido and len(traduzido) > 0:
                    print(f"🌐 Google Translate: {texto} -> {traduzido}")
                    return traduzido
        except Exception as e:
            print(f"⚠️ Erro no Google Translate: {e}")
        
        # Se tudo falhar, retorna o texto original
        return texto


class PubChemAPI:
    """API PubChem com tradução automática"""
    
    @staticmethod
    def buscar_por_formula(formula):
        formula_limpa = re.sub(r'[^A-Za-z0-9]', '', formula).upper()
        url_cid = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/fastformula/{formula_limpa}/cids/txt"
        
        try:
            response = requests.get(url_cid, timeout=5)
            if response.status_code == 200:
                cid = response.text.strip().split('\n')[0]
                if cid.isdigit():
                    print(f"✅ CID encontrado: {cid}")
                    return PubChemAPI.buscar_sdf_por_cid(cid)
        except:
            pass
        return None
    
    @staticmethod
    def buscar_por_nome(nome):
        # TRADUZ AUTOMATICAMENTE
        nome_traduzido = TradutorAutomatico.traduzir(nome)
        
        if nome_traduzido != nome:
            print(f"🔄 Traduzido: {nome} -> {nome_traduzido}")
        
        url_cid = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{nome_traduzido}/cids/txt"
        
        try:
            response = requests.get(url_cid, timeout=5)
            if response.status_code == 200:
                cid = response.text.strip().split('\n')[0]
                if cid.isdigit():
                    print(f"✅ CID encontrado: {cid}")
                    return PubChemAPI.buscar_sdf_por_cid(cid)
        except:
            pass
        return None
    
    @staticmethod
    def buscar_por_smiles(smiles):
        url_cid = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/{smiles}/cids/txt"
        
        try:
            response = requests.get(url_cid, timeout=5)
            if response.status_code == 200:
                cid = response.text.strip().split('\n')[0]
                if cid.isdigit():
                    print(f"✅ CID encontrado: {cid}")
                    return PubChemAPI.buscar_sdf_por_cid(cid)
        except:
            pass
        return None
    
    @staticmethod
    def buscar_sdf_por_cid(cid):
        url_sdf = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF?record_type=3d"
        
        try:
            response = requests.get(url_sdf, headers={'Accept': 'chemical/x-mdl-sdfile'}, timeout=10)
            if response.status_code == 200:
                return PubChemAPI.parse_sdf(response.text)
        except:
            pass
        return None
    
    @staticmethod
    def buscar_automatico(query):
        query = query.strip()
        
        # Verifica cache
        cached = cache_store.get(query)
        if cached:
            print(f"⚡ Cache hit: {query}")
            return cached
        
        print(f"\n🔍 Buscando: {query}")
        
        # Tenta como FÓRMULA
        if re.search(r'[A-Z]\d+', query.upper()):
            resultado = PubChemAPI.buscar_por_formula(query)
            if resultado:
                cache_store.set(query, resultado)
                return resultado
        
        # Tenta como NOME (com tradução automática)
        resultado = PubChemAPI.buscar_por_nome(query)
        if resultado:
            cache_store.set(query, resultado)
            return resultado
        
        # Tenta como SMILES
        if re.search(r'[a-z]', query):
            resultado = PubChemAPI.buscar_por_smiles(query)
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
        for i in range(min(50, len(lines))):
            line = lines[i]
            if len(line) >= 10 and line[0:3].strip().isdigit():
                try:
                    atom_count = int(line[0:3].strip())
                    bond_count = int(line[3:6].strip())
                    start_line = i + 1
                    break
                except:
                    pass
        
        if atom_count == 0:
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
                    element = re.sub(r'[0-9]', '', element)[:1]
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


@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({'status': 'ok', 'message': 'API com tradutor automático!'})

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
                'fonte': 'PubChem API'
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
    """Endpoint para testar a tradução"""
    traduzido = TradutorAutomatico.traduzir(texto)
    return jsonify({'original': texto, 'traduzido': traduzido})


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🧪 API COM TRADUTOR AUTOMÁTICO")
    print("="*60)
    print("\n✅ TRADUÇÕES AUTOMÁTICAS:")
    print("   amonia -> ammonia")
    print("   amônia -> ammonia")
    print("   água -> water")
    print("   octano -> octane")
    print("\n🚀 Servidor: http://localhost:5000")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)