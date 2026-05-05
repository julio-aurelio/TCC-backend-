from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
import math
import time
from unidecode import unidecode
from datetime import datetime, timedelta
import json

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

class DetectorTipoBusca:
    """Detecta inteligentemente o tipo de busca (fórmula simples, complexa, nome, etc)"""
    
    @staticmethod
    def é_formula_simples(query):
        """Detecta fórmulas simples como C8H18, H2O, CO2, NaCl"""
        # Padrão: letra maiúscula seguida de número opcional, repetido
        # Aceita apenas C, H, O, N, etc + números
        padrao_simples = r'^[A-Z][a-z]?\d*([A-Z][a-z]?\d*)*$'
        
        if re.match(padrao_simples, query):
            # Verifica se tem apenas elementos comuns
            elementos_comuns = ['C', 'H', 'O', 'N', 'S', 'P', 'F', 'Cl', 'Br', 'I', 'Na', 'Mg', 'Ca', 'K', 'Fe', 'Cu', 'Zn']
            elementos_encontrados = re.findall(r'[A-Z][a-z]?', query)
            
            # Se todos os elementos são comuns, é fórmula simples
            for elem in elementos_encontrados:
                if elem not in elementos_comuns and len(elem) == 1:
                    if elem not in ['C', 'H', 'O', 'N', 'S', 'P', 'F', 'Cl', 'Br', 'I']:
                        return False
            return True
        return False
    
    @staticmethod
    def é_formula_complexa(query):
        """Detecta fórmulas complexas: com parênteses, hidratação, íons"""
        padrões_complexos = [
            r'[\(\)]',           # Parênteses
            r'[·.*]H2O',         # Hidratação
            r'[²³⁺⁻]',           # Íons
            r'[A-Z][a-z]?\[',    # Colchetes
        ]
        
        for padrao in padrões_complexos:
            if re.search(padrao, query):
                return True
        return False
    
    @staticmethod
    def é_nome_quimico(query):
        """Detecta se é um nome químico (tem espaços e palavras comuns)"""
        palavras_comuns = ['acido', 'ácido', 'hidroxido', 'hidróxido', 'cloreto', 'sulfato', 
                          'nitrato', 'carbonato', 'fosfato', 'metano', 'etano', 'butano', 
                          'benzeno', 'tolueno', 'agua', 'água', 'amonia', 'amônia']
        
        query_lower = query.lower()
        
        # Tem espaços ou palavras comuns
        if ' ' in query:
            return True
        
        for palavra in palavras_comuns:
            if palavra in query_lower:
                return True
        
        return False
    
    @staticmethod
    def detectar_tipo(query):
        """Retorna o tipo de busca"""
        if DetectorTipoBusca.é_formula_simples(query):
            return 'FORMULA_SIMPLES'
        elif DetectorTipoBusca.é_formula_complexa(query):
            return 'FORMULA_COMPLEXA'
        elif DetectorTipoBusca.é_nome_quimico(query):
            return 'NOME_QUIMICO'
        else:
            return 'DESCONHECIDO'


class NormalizadorFormula:
    """Normaliza fórmulas químicas - APENAS para fórmulas complexas"""
    
    @staticmethod
    def normalizar_formula_simples(formula):
        """Preserva fórmula simples exatamente como está"""
        # Apenas garante que C vem antes de H
        if 'C' in formula and 'H' in formula:
            # Extrai números
            match_c = re.search(r'C(\d*)', formula)
            match_h = re.search(r'H(\d*)', formula)
            
            if match_c and match_h:
                c_num = match_c.group(1) if match_c.group(1) else '1'
                h_num = match_h.group(1) if match_h.group(1) else '1'
                
                # Pega o resto da fórmula
                resto = re.sub(r'[CH]\d*', '', formula)
                
                # Reconstrói com C primeiro, depois H
                return f"C{c_num}H{h_num}{resto}"
        
        return formula
    
    @staticmethod
    def normalizar_formula_complexa(formula):
        """Normaliza fórmulas complexas (com parênteses, hidratação, etc)"""
        original = formula
        print(f"🔧 Normalizando fórmula complexa: {formula}")
        
        # Remove cargas iônicas
        formula = re.sub(r'[²³⁺⁻]', '', formula)
        
        # Remove hidratação
        formula = re.sub(r'[·.*](\d*)H2O', '', formula)
        formula = re.sub(r'[·.*](\d*)H₂O', '', formula)
        
        # Expande parênteses simples
        padrao = r'\(([^()]+)\)(\d+)'
        while re.search(padrao, formula):
            def expandir(match):
                grupo = match.group(1)
                indice = int(match.group(2))
                resultado = ""
                elementos = re.findall(r'([A-Z][a-z]?)(\d*)', grupo)
                for elem, num in elementos:
                    if num:
                        resultado += elem * (int(num) * indice)
                    else:
                        resultado += elem * indice
                return resultado
            formula = re.sub(padrao, expandir, formula)
        
        # Remove traços orgânicos
        formula = re.sub(r'[-=→]', '', formula)
        formula = re.sub(r'\s+', '', formula)
        
        print(f"   ↳ {original} -> {formula}")
        return formula
    
    @staticmethod
    def normalizar_completo(query, tipo):
        """Normaliza baseado no tipo detectado"""
        if tipo == 'FORMULA_SIMPLES':
            return NormalizadorFormula.normalizar_formula_simples(query)
        elif tipo == 'FORMULA_COMPLEXA':
            return NormalizadorFormula.normalizar_formula_complexa(query)
        else:
            return query


class TradutorAutomatico:
    """Tradutor automático português -> inglês para química"""
    
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
        "sulfato": "sulfate", "nitrato": "nitrate", "carbonato": "carbonate",
        "fosfato": "phosphate", "amonio": "ammonium", "amônio": "ammonium",
        "hidroxido": "hydroxide", "hidróxido": "hydroxide",
    }
    
    @staticmethod
    def traduzir(texto):
        texto = texto.lower().strip()
        texto_sem_acento = unidecode(texto)
        
        if texto in TradutorAutomatico.FALLBACK:
            return TradutorAutomatico.FALLBACK[texto]
        if texto_sem_acento in TradutorAutomatico.FALLBACK:
            return TradutorAutomatico.FALLBACK[texto_sem_acento]
        
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
                if traduzido:
                    return traduzido
        except Exception as e:
            print(f"⚠️ Erro no Google Translate: {e}")
        
        return texto


class PubChemAPI:
    """API PubChem com detecção inteligente de tipo"""
    
    @staticmethod
    def buscar_por_formula(formula, tipo):
        """Busca por fórmula química"""
        
        if tipo == 'FORMULA_SIMPLES':
            # Para fórmulas simples, busca direto sem normalização
            formulas_para_testar = [formula, formula.upper()]
        else:
            # Para fórmulas complexas, normaliza primeiro
            formula_normalizada = NormalizadorFormula.normalizar_completo(formula, tipo)
            formulas_para_testar = [formula_normalizada, formula_normalizada.upper()]
        
        for var in formulas_para_testar:
            if len(var) < 2:
                continue
                
            url_cid = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/fastformula/{var}/cids/txt"
            
            try:
                response = requests.get(url_cid, timeout=5)
                if response.status_code == 200:
                    cid = response.text.strip().split('\n')[0]
                    if cid and cid.isdigit():
                        print(f"✅ CID encontrado via fórmula: {cid} (variação: {var})")
                        resultado = PubChemAPI.buscar_sdf_por_cid(cid)
                        if resultado:
                            return resultado
            except:
                continue
        
        return None
    
    @staticmethod
    def buscar_por_nome(nome):
        nome_traduzido = TradutorAutomatico.traduzir(nome)
        
        if nome_traduzido != nome:
            print(f"🔄 Traduzido: {nome} -> {nome_traduzido}")
        
        estrategias = [
            nome_traduzido,
            nome_traduzido.replace(" ", ""),
            nome_traduzido.split()[0]
        ]
        
        for estrategia in set(estrategias):
            if len(estrategia) < 2:
                continue
                
            url_cid = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{estrategia}/cids/txt"
            
            try:
                response = requests.get(url_cid, timeout=5)
                if response.status_code == 200:
                    cid = response.text.strip().split('\n')[0]
                    if cid and cid.isdigit():
                        print(f"✅ CID encontrado via nome: {cid}")
                        resultado = PubChemAPI.buscar_sdf_por_cid(cid)
                        if resultado:
                            return resultado
            except:
                continue
        
        return None
    
    @staticmethod
    def buscar_por_smiles(smiles):
        url_cid = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/{smiles}/cids/txt"
        
        try:
            response = requests.get(url_cid, timeout=5)
            if response.status_code == 200:
                cid = response.text.strip().split('\n')[0]
                if cid and cid.isdigit():
                    print(f"✅ CID encontrado via SMILES: {cid}")
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
        
        # Tenta 2D como fallback
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
        
        # Verifica cache
        cached = cache_store.get(query)
        if cached:
            print(f"⚡ Cache hit: {query}")
            return cached
        
        print(f"\n🔍 Buscando: {query}")
        
        # DETECTA O TIPO DE BUSCA
        tipo = DetectorTipoBusca.detectar_tipo(query)
        print(f"📊 Tipo detectado: {tipo}")
        
        resultado = None
        
        # ESTRATÉGIA 1: Busca por fórmula (se parecer com fórmula)
        if tipo in ['FORMULA_SIMPLES', 'FORMULA_COMPLEXA']:
            print("📝 Buscando como fórmula química...")
            resultado = PubChemAPI.buscar_por_formula(query, tipo)
            if resultado:
                cache_store.set(query, resultado)
                return resultado
        
        # ESTRATÉGIA 2: Busca por nome
        print("📝 Buscando como nome químico...")
        resultado = PubChemAPI.buscar_por_nome(query)
        if resultado:
            cache_store.set(query, resultado)
            return resultado
        
        # ESTRATÉGIA 3: Busca por SMILES
        if not re.search(r'\s', query):
            print("📝 Buscando como SMILES...")
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
        
        # Encontra linha de counts
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
        
        if atom_count == 0:
            return None
        
        # Pula linhas em branco
        while start_line < len(lines) and len(lines[start_line].strip()) < 5:
            start_line += 1
        
        # Lê átomos
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
        
        # Lê ligações
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
    return jsonify({'status': 'ok', 'message': 'API Química com Detecção Inteligente!'})

@app.route('/api/molecule/<path:query>', methods=['GET'])
def get_molecule(query):
    start_time = time.time()
    
    # Detecta tipo antes de buscar
    tipo = DetectorTipoBusca.detectar_tipo(query)
    
    resultado = PubChemAPI.buscar_automatico(query)
    elapsed = time.time() - start_time
    
    if resultado:
        return jsonify({
            'success': True,
            'meta': {
                'query_original': query,
                'tipo_detectado': tipo,
                'tempo_busca': f"{elapsed:.2f}s",
                'fonte': 'PubChem API Inteligente'
            },
            'data': resultado
        })
    else:
        return jsonify({
            'success': False,
            'error': f'Não foi possível encontrar: "{query}"',
            'tipo_detectado': tipo,
            'dicas': [
                'Para fórmulas: use C8H18, H2O, NaCl',
                'Para nomes: use "água", "metano", "benzeno"',
                'Para SMILES: use CC(=O)O para ácido acético'
            ]
        }), 404

@app.route('/api/detectartipo/<path:query>', methods=['GET'])
def detectar_tipo(query):
    """Endpoint para testar a detecção de tipo"""
    tipo = DetectorTipoBusca.detectar_tipo(query)
    return jsonify({
        'query': query,
        'tipo_detectado': tipo,
        'explicacao': {
            'FORMULA_SIMPLES': 'Fórmula química simples (C8H18, H2O)',
            'FORMULA_COMPLEXA': 'Fórmula com parênteses/hidratação/íons',
            'NOME_QUIMICO': 'Nome químico em português/inglês',
            'DESCONHECIDO': 'Tipo não identificado'
        }[tipo]
    })

@app.route('/api/traduzir/<path:texto>', methods=['GET'])
def test_traducao(texto):
    traduzido = TradutorAutomatico.traduzir(texto)
    return jsonify({'original': texto, 'traduzido': traduzido})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)