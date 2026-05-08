"""
Compostos especiais que têm CID fixo na PubChem
(são moléculas grandes ou complexas que não são encontradas facilmente por nome)
"""

COMPOSTOS_ESPECIAIS = {
    # ============================================
    # PROTEÍNAS
    # ============================================
    'hemoglobina': {
        'cid': '9774494',
        'nome': 'Hemoglobina',
        'formula': 'C3032H4816O872N780S8Fe4',
        'tipo': 'proteina',
        'descricao': 'Proteína responsável pelo transporte de oxigênio no sangue'
    },
    'hemoglobin': {
        'cid': '9774494',
        'nome': 'Hemoglobin',
        'formula': 'C3032H4816O872N780S8Fe4',
        'tipo': 'protein',
        'descricao': 'Protein responsible for oxygen transport in blood'
    },
    'insulina': {
        'cid': '16137410',
        'nome': 'Insulina',
        'formula': 'C257H383N65O77S6',
        'tipo': 'hormonio',
        'descricao': 'Hormônio que regula o metabolismo da glicose'
    },
    'insulin': {
        'cid': '16137410',
        'nome': 'Insulin',
        'formula': 'C257H383N65O77S6',
        'tipo': 'hormone',
        'descricao': 'Hormone that regulates glucose metabolism'
    },
    'albumina': {
        'cid': '16137409',
        'nome': 'Albumina',
        'formula': 'C2936H4624N786O889S41',
        'tipo': 'proteina',
        'descricao': 'Proteína mais abundante no plasma sanguíneo'
    },
    'albumin': {
        'cid': '16137409',
        'nome': 'Albumin',
        'formula': 'C2936H4624N786O889S41',
        'tipo': 'protein',
        'descricao': 'Most abundant protein in blood plasma'
    },
    'mioglobina': {
        'cid': '16077965',
        'nome': 'Mioglobina',
        'formula': 'C768H1212N210O218S2Fe',
        'tipo': 'proteina',
        'descricao': 'Proteína que armazena oxigênio nos músculos'
    },
    'myoglobin': {
        'cid': '16077965',
        'nome': 'Myoglobin',
        'formula': 'C768H1212N210O218S2Fe',
        'tipo': 'protein',
        'descricao': 'Oxygen-storage protein in muscles'
    },
    
    # ============================================
    # FÁRMACOS COMPLEXOS
    # ============================================
    'vincristina': {
        'cid': '5978',
        'nome': 'Vincristina',
        'formula': 'C46H56N4O10',
        'tipo': 'farmaco',
        'descricao': 'Agente quimioterápico'
    },
    'vincristine': {
        'cid': '5978',
        'nome': 'Vincristine',
        'formula': 'C46H56N4O10',
        'tipo': 'drug',
        'descricao': 'Chemotherapy agent'
    },
    'vancomicina': {
        'cid': '6099',
        'nome': 'Vancomicina',
        'formula': 'C66H75Cl2N9O24',
        'tipo': 'antibiotico',
        'descricao': 'Antibiótico potente para infecções graves'
    },
    'vancomycin': {
        'cid': '6099',
        'nome': 'Vancomycin',
        'formula': 'C66H75Cl2N9O24',
        'tipo': 'antibiotic',
        'descricao': 'Potent antibiotic for serious infections'
    },
    'ciclosporina': {
        'cid': '5284373',
        'nome': 'Ciclosporina',
        'formula': 'C62H111N11O12',
        'tipo': 'imunossupressor',
        'descricao': 'Imunossupressor usado em transplantes'
    },
    'cyclosporine': {
        'cid': '5284373',
        'nome': 'Cyclosporine',
        'formula': 'C62H111N11O12',
        'tipo': 'immunosuppressant',
        'descricao': 'Immunosuppressant used in transplants'
    },
    
    # ============================================
    # VITAMINAS (com estruturas complexas)
    # ============================================
    'vitamina b12': {
        'cid': '70678557',
        'nome': 'Vitamina B12',
        'formula': 'C63H88CoN14O14P',
        'tipo': 'vitamina',
        'descricao': 'Essencial para a formação do sangue e sistema nervoso'
    },
    'cobalamina': {
        'cid': '70678557',
        'nome': 'Cobalamina',
        'formula': 'C63H88CoN14O14P',
        'tipo': 'vitamina',
        'descricao': 'Essencial para a formação do sangue e sistema nervoso'
    },
    
    # ============================================
    # ÁCIDOS NUCLEICOS (ADICIONADO)
    # ============================================
    'dna': {
        'cid': '44135672',
        'nome': 'DNA (Deoxyribonucleic acid)',
        'tipo': 'acido_nucleico',
        'descricao': 'Ácido desoxirribonucleico - material genético'
    },
    'acido desoxirribonucleico': {
        'cid': '44135672',
        'nome': 'DNA (Ácido desoxirribonucleico)',
        'tipo': 'acido_nucleico',
        'descricao': 'Material genético'
    },
    'ácido desoxirribonucleico': {
        'cid': '44135672',
        'nome': 'DNA (Ácido desoxirribonucleico)',
        'tipo': 'acido_nucleico',
        'descricao': 'Material genético'
    },
    'rna': {
        'cid': '439153',
        'nome': 'RNA (Ribonucleic acid)',
        'tipo': 'acido_nucleico',
        'descricao': 'Ácido ribonucleico'
    },
    'acido ribonucleico': {
        'cid': '439153',
        'nome': 'RNA (Ácido ribonucleico)',
        'tipo': 'acido_nucleico',
        'descricao': 'Ácido ribonucleico'
    },
    'ácido ribonucleico': {
        'cid': '439153',
        'nome': 'RNA (Ácido ribonucleico)',
        'tipo': 'acido_nucleico',
        'descricao': 'Ácido ribonucleico'
    },
    
    # ============================================
    # NUCLEOTÍDEOS (ADICIONADO)
    # ============================================
    'atp': {
        'cid': '5957',
        'nome': 'ATP (Adenosine triphosphate)',
        'tipo': 'nucleotideo',
        'descricao': 'Adenosina trifosfato - principal moeda energética da célula'
    },
    'adp': {
        'cid': '6022',
        'nome': 'ADP (Adenosine diphosphate)',
        'tipo': 'nucleotideo',
        'descricao': 'Adenosina difosfato'
    },
    'amp': {
        'cid': '6083',
        'nome': 'AMP (Adenosine monophosphate)',
        'tipo': 'nucleotideo',
        'descricao': 'Adenosina monofosfato'
    },
    'camp': {
        'cid': '123631',
        'nome': 'cAMP (Cyclic AMP)',
        'tipo': 'nucleotideo',
        'descricao': 'AMP cíclico - segundo mensageiro'
    },
    'gtp': {
        'cid': '6830',
        'nome': 'GTP (Guanosine triphosphate)',
        'tipo': 'nucleotideo',
        'descricao': 'Guanosina trifosfato'
    },
    'gdp': {
        'cid': '8977',
        'nome': 'GDP (Guanosine diphosphate)',
        'tipo': 'nucleotideo',
        'descricao': 'Guanosina difosfato'
    },
    'nadh': {
        'cid': '439153',
        'nome': 'NADH',
        'tipo': 'coenzima',
        'descricao': 'Nicotinamida adenina dinucleotídeo reduzido'
    },
    'nadph': {
        'cid': '439153',
        'nome': 'NADPH',
        'tipo': 'coenzima',
        'descricao': 'Nicotinamida adenina dinucleotídeo fosfato reduzido'
    },
    
    # ============================================
    # ENZIMAS
    # ============================================
    'catalase': {
        'cid': '154221104',
        'nome': 'Catalase',
        'tipo': 'enzima',
        'descricao': 'Enzima que decompõe peróxido de hidrogênio'
    },
    'lisozima': {
        'cid': '16139975',
        'nome': 'Lisozima',
        'tipo': 'enzima',
        'descricao': 'Enzima antibacteriana presente em lágrimas e saliva'
    },
    
    # ============================================
    # TOXINAS
    # ============================================
    'botulinum': {
        'cid': '5484910',
        'nome': 'Toxina Botulínica',
        'tipo': 'toxina',
        'descricao': 'Toxina produzida pela bactéria Clostridium botulinum'
    },
    'ricina': {
        'cid': '118984579',
        'nome': 'Ricina',
        'tipo': 'toxina',
        'descricao': 'Toxina da semente da mamona'
    },
    
    # ============================================
    # AÇÚCARES E CARBOIDRATOS COMPLEXOS
    # ============================================
    'heparina': {
        'cid': '772',
        'nome': 'Heparina',
        'tipo': 'anticoagulante',
        'descricao': 'Anticoagulante natural'
    },
    'hialuronico': {
        'cid': '3080588',
        'nome': 'Ácido Hialurônico',
        'tipo': 'polissacarideo',
        'descricao': 'Componente importante do tecido conjuntivo'
    },
    'hialurônico': {
        'cid': '3080588',
        'nome': 'Ácido Hialurônico',
        'tipo': 'polissacarideo',
        'descricao': 'Componente importante do tecido conjuntivo'
    },
}

# Mapeamento de fórmulas grandes para CID
FORMULAS_GRANDES = {
    'C3032H4816O872N780S8Fe4': '9774494',  # Hemoglobina
    'C257H383N65O77S6': '16137410',        # Insulina
    'C2936H4624N786O889S41': '16137409',   # Albumina
    'C768H1212N210O218S2Fe': '16077965',   # Mioglobina
    'C63H88CoN14O14P': '70678557',         # Vitamina B12
    'C62H111N11O12': '5284373',            # Ciclosporina
}