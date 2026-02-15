import requests
import json
import os
import sys
from pathlib import Path
import time

# --- CONFIGURATION ----
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = BASE_DIR / "Backend" / "Data" / "proteins.json"

# API UniProt
UNIPROT_API = "https://rest.uniprot.org/uniprotkb/search"

# CIBLE : LE PROTÉOME HUMAIN COMPLET (The Full Human Proteome)
QUERY = "proteome:UP000005640 AND reviewed:true"

def fetch_production_data():
    """
    Récupère l'intégralité du protéome humain (~20 350 protéines).
    Version corrigée avec gestion robuste de la pagination via response.links.
    """
    print(f"🚀 Démarrage du téléchargement 'Niveau Production'...")
    print(f"🎯 Cible : Protéome Humain Complet (UP000005640)")
    
    # Paramètres initiaux
    params = {
        "query": QUERY,
        "format": "json",
        "size": 500,
        "fields": "accession,id,protein_name,sequence,cc_function"
    }
    
    session = requests.Session()
    all_proteins = []
    batch_count = 0
    
    # URL de départ
    next_url = UNIPROT_API
    
    try:
        print("🌍 Connexion à UniProt...")
        
        while next_url:
            batch_count += 1
            
            # Pour la première requête, on utilise 'params'. 
            # Pour les suivantes, l'URL contient déjà les paramètres.
            if next_url == UNIPROT_API:
                response = session.get(next_url, params=params, timeout=45)
            else:
                response = session.get(next_url, timeout=45)
                
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            # Traitement du paquet
            for item in results:
                try:
                    name = item['proteinDescription']['recommendedName']['fullName']['value']
                    sequence = item['sequence']['value']
                    
                    function = "Fonction non cataloguée"
                    comments = item.get('comments', [])
                    for c in comments:
                        if c['commentType'] == 'FUNCTION':
                            function = c['texts'][0]['value']
                            break
                    
                    if len(function) > 300:
                        function = function[:300] + "..."

                    all_proteins.append({
                        "name": name,
                        "function": function,
                        "sequence": sequence,
                        "source": "UniProt Human Proteome"
                    })
                except KeyError:
                    continue
            
            print(f"   📦 Paquet {batch_count} traité. Total accumulé : {len(all_proteins)} protéines...")

            # --- CORRECTION MAJEURE ICI ---
            # Utilisation de la méthode native de `requests` pour trouver le lien "next"
            # Plus besoin de parsing manuel complexe qui cause des erreurs
            if 'next' in response.links:
                next_url = response.links['next']['url']
            else:
                next_url = None # Fin de la pagination
                
    except Exception as e:
        print(f"❌ Erreur critique : {e}")
        if len(all_proteins) > 0:
            print("⚠️ Sauvegarde d'urgence des données déjà récupérées...")
    
    # Sauvegarde Finale
    print(f"\n💾 Sauvegarde de {len(all_proteins)} séquences dans le fichier JSON...")
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_proteins, f, indent=4, ensure_ascii=False)
        
    print(f"✅ SUCCÈS : Données de production prêtes !")
    print(f"   📂 Emplacement : {OUTPUT_FILE}")

if __name__ == "__main__":
    fetch_production_data()