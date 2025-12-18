# 🤖 FlaskBuddy - Système de contrôle complet pour robot Buddy

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-orange.svg)](https://modelcontextprotocol.io/)

> **Guide complet étape par étape pour créer un système de contrôle intelligent du robot Buddy via Flask API et Model Context Protocol (MCP)**

Ce guide vous permettra de recréer **intégralement** le projet FlaskBuddy, y compris le serveur MCP, l'API Flask, et toutes les fonctionnalités de contrôle et de suivi autonome.

---

## 📋 Table des matières

1. [Introduction & Architecture](#-introduction--architecture)
2. [Prérequis & Installation](#-prérequis--installation)
3. [Création du projet de zéro](#-création-du-projet-de-zéro)
   - [Structure des fichiers](#étape-1--structure-des-fichiers)
   - [Dependencies (requirements.txt)](#étape-2--dependencies-requirementstxt)
   - [API Flask (api.py)](#étape-3--api-flask-apipy)
   - [Fonctions Buddy (buddy_functions.py)](#étape-4--fonctions-buddy-buddy_functionspy)
   - [Serveur MCP (mcp_server.py)](#étape-5--serveur-mcp-mcp_serverpy)
4. [Configuration](#-configuration)
5. [Déploiement & Tests](#-déploiement--tests)
6. [Utilisation avancée](#-utilisation-avancée)
7. [Troubleshooting](#-troubleshooting)

---

## 🎯 Introduction & Architecture

### Qu'est-ce que FlaskBuddy ?

FlaskBuddy est un système complet permettant de contrôler le robot Buddy via **deux interfaces** :
1. **Claude Desktop** (via Model Context Protocol - MCP)
2. **CLI en ligne de commande** (pour tests et débogage)

### Architecture complète

```
┌────────────────────────────────────────────────────────────────┐
│                      Claude Desktop                            │
│                   (Interface utilisateur)                      │
│  - Permet de parler à Claude en langage naturel                │
│  - Claude utilise les tools MCP pour contrôler Buddy           │
└───────────────────────┬────────────────────────────────────────┘
                        │
                        │ Communication stdio (entrée/sortie standard)
                        │ JSON-RPC 2.0 via MCP Protocol
                        │
┌───────────────────────▼────────────────────────────────────────┐
│             MCP Server (mcp_server.py)                         │
│  Rôle: Interface entre Claude et le système Buddy             │
│  ────────────────────────────────────────────────────────      │
│  - Expose 9 "tools" à Claude Desktop                           │
│  - Convertit les requêtes Claude en opérations Buddy          │
│  - Utilise stdio pour communication (pas HTTP)                 │
│  - Fonctionne en mode serveur standalone                       │
│  ────────────────────────────────────────────────────────      │
│  Tools exposés:                                                │
│    1. move_buddy      - Déplacement (avant/arrière)            │
│    2. rotate_buddy    - Rotation (gauche/droite)               │
│    3. speak           - Synthèse vocale                        │
│    4. move_head       - Mouvement de tête                      │
│    5. set_mood        - Expression faciale                     │
│    6. take_picture    - Capture photo                          │
│    7. multi_action    - Actions multiples simultanées          │
└────────────────────────┬───────────────────────────────────────┘
                        │
                        │ Shared Memory (Python)
                        │ operation_queue (deque)
                        │ latest_image (dict)
                        │ queue_lock (threading.Lock)
                        │
┌───────────────────────▼────────────────────────────────────────┐
│           Buddy Functions (buddy_functions.py)                 │
│  Rôle: Implémentation de la logique métier                    │
│  ────────────────────────────────────────────────────────      │
│  - Implémente les 7 fonctions outils                           │
│  - Crée les opérations au format API REST                      │
│  - Gère la queue partagée avec Flask                           │
│  - Logs détaillés pour debugging                               │
│  ────────────────────────────────────────────────────────      │
│  Fonctions principales:                                        │
│    - move_buddy()     -> MoveOperation                         │
│    - rotate_buddy()   -> RotateOperation                       │
│    - speak()          -> TalkOperation                         │
│    - multi_action()   -> MultiOperation                        │
└───────────────────────┬────────────────────────────────────────┘
                        │
                        │ Append operations to queue
                        │ Thread-safe avec queue_lock
                        │
┌───────────────────────▼────────────────────────────────────────┐
│                 Flask API (api.py)                             │
│  Rôle: Serveur HTTP REST pour Buddy                           │
│  ────────────────────────────────────────────────────────      │
│  Port: 5000                                                    │
│  Host: 0.0.0.0 (accessible sur le réseau local)                │
│  ────────────────────────────────────────────────────────      │
│  Endpoints:                                                    │
│    GET  /operation      - Polling par Buddy                    │
│    POST /upload_image   - Réception photos caméra              │
│  ────────────────────────────────────────────────────────      │
│  Features:                                                     │
│    - Queue d'opérations partagée avec MCP                      │
│    - Redimensionnement images 800x600                          │
│    - Mode CLI pour tests (--cli flag)                          │
└───────────────────────┬────────────────────────────────────────┘
                        │
                        │ HTTP REST API
                        │ GET /operation (polling toutes les X secondes)
                        │ POST /upload_image (quand photo capturée)
                        │
┌───────────────────────▼────────────────────────────────────────┐
│                      Robot Buddy                               │
│  Comportement côté robot:                                      │
│  ────────────────────────────────────────────────────────      │
│  1. Polling: GET /operation toutes les 2 secondes              │
│  2. Si operation != null:                                      │
│     - Parse l'opération (MoveOperation, etc.)                  │
│     - Exécute l'action (moteurs, parole, etc.)                 │
│  3. Périodiquement: capture photo caméra                       │
│     - POST /upload_image avec base64                           │
└────────────────────────────────────────────────────────────────┘
```

### Flow de communication détaillé

```
SCÉNARIO: Claude dit "Buddy, avance de 1 mètre"

1. Claude Desktop (UI)
   └─> Analyse la demande en langage naturel
   └─> Identifie qu'il faut utiliser le tool "move_buddy"
   
2. Claude Desktop → MCP Server (stdio)
   └─> Envoie requête JSON-RPC:
       {
         "jsonrpc": "2.0",
         "method": "tools/call",
         "params": {
           "name": "move_buddy",
           "arguments": {"speed": 100, "distance": 1.0}
         }
       }

3. MCP Server (mcp_server.py)
   └─> Reçoit la requête via stdio
   └─> Appelle TOOL_HANDLERS["move_buddy"](speed=100, distance=1.0)
   
4. buddy_functions.py - move_buddy()
   └─> Valide les paramètres (speed = abs(speed))
   └─> Crée l'opération:
       {
         "type": "MoveOperation",
         "speed": 100,
         "distance": 1.0
       }
   └─> Ajoute à operation_queue (thread-safe avec queue_lock)
   └─> Retourne réponse à MCP Server
   
5. MCP Server → Claude Desktop
   └─> Envoie réponse JSON-RPC:
       {
         "jsonrpc": "2.0",
         "result": [
           {"type": "text", "text": "Queued move forward at speed 100 for 1.0m"}
         ]
       }
   
6. Claude Desktop (UI)
   └─> Affiche à l'utilisateur: "✓ Commande envoyée à Buddy"
   
7. Robot Buddy (polling)
   └─> GET http://localhost:5000/operation
   └─> Reçoit: {"status": "success", "operation": {"type": "MoveOperation", ...}}
   └─> Exécute le mouvement: moteurs à vitesse 100, distance 1.0m
   └─> GET http://localhost:5000/operation (continue polling)
```

---

## 🔧 Prérequis & Installation

### Prérequis système

**Obligatoire** :
- **Python 3.8+** (testé avec Python 3.10 et 3.11)
- **pip** (gestionnaire de packages Python)
- **Claude Desktop** (version avec support MCP)
- **Robot Buddy** connecté au réseau local
- **Windows, macOS, ou Linux** (instructions adaptées à chaque OS)

**Optionnel** :
- **Git** (pour cloner le repository)
- **Visual Studio Code** ou autre IDE
- **Postman** ou **curl** (pour tester l'API)

### Installation Python

#### Windows
```powershell
# Télécharger depuis python.org
# Ou via Windows Store
winget install Python.Python.3.11

# Vérifier installation
python --version
pip --version
```

#### macOS
```bash
# Via Homebrew
brew install python@3.11

# Vérifier
python3 --version
pip3 --version
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3.11 python3-pip python3-venv

# Vérifier
python3 --version
pip3 --version
```

### Installation Claude Desktop

1. Télécharger Claude Desktop depuis [claude.ai](https://claude.ai/download)
2. Installer l'application
3. Se connecter avec son compte Anthropic
4. **Important** : Vérifier que la version supporte MCP (version récente)

---

## 🏗️ Création du projet de zéro

### Étape 1 : Structure des fichiers

Créer la structure de dossiers suivante :

```
flaskBuddy/
├── api.py                      # Serveur Flask API
├── mcp_server.py               # Serveur MCP pour Claude Desktop
├── buddy_functions.py          # Implémentation des outils
├── requirements.txt            # Dépendances Python
├── claude_desktop_config.json  # Configuration MCP (exemple)
├── README.md                   # Cette documentation
├── Todo.md                     # Tâches de développement (optionnel)
└── .gitignore                  # Fichiers à ignorer par Git
```

Créer les fichiers :

```bash
# Créer le dossier du projet
mkdir flaskBuddy
cd flaskBuddy

# Créer les fichiers vides
touch api.py mcp_server.py buddy_functions.py requirements.txt .gitignore README.md
```

---

### Étape 2 : Dependencies (requirements.txt)

Créer le fichier `requirements.txt` avec le contenu exact suivant :

```txt
# Flask - Serveur web pour API REST
flask>=3.0.0

# MCP - Model Context Protocol pour Claude Desktop
mcp>=1.0.0

# Pillow - Traitement d'images (redimensionnement photos)
pillow>=10.0.0

# Standard library (déjà inclus mais mentionné pour référence)
# - collections (deque pour queue)
# - threading (Lock pour thread-safety)
# - asyncio (pour MCP server)
# - base64 (encodage images)
# - datetime (timestamps)
```

**Installer les dépendances** :

```bash
# Créer un environnement virtuel (FORTEMENT RECOMMANDÉ)
python -m venv .venv

# Activer l'environnement
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Windows CMD:
.\.venv\Scripts\activate.bat
# macOS/Linux:
source .venv/bin/activate

# Installer les packages
pip install -r requirements.txt

# Vérifier l'installation
pip list
```

---

### Étape 3 : API Flask (api.py)

Créer le fichier `api.py` **complet** avec tout le code suivant :

```python
"""
Flask API Server pour Buddy Robot
Expose les endpoints HTTP pour communication avec le robot.
"""

from flask import Flask, jsonify, request
from collections import deque
from datetime import datetime
import threading
import sys
import logging
import base64
import os
from io import BytesIO
from PIL import Image

# Créer l'application Flask
app = Flask(__name__)

# Configuration
LATEST_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "latest_image.png")
IMAGE_SIZE = (800, 600)  # Taille cible pour les images

# Logger vers stderr (stdout réservé pour MCP)
app.logger.addHandler(logging.StreamHandler(sys.stderr))
log = lambda msg: print(msg, file=sys.stderr)

# ═══════════════════════════════════════════════════════════════
# SHARED STATE - Partagé entre Flask et MCP Server
# ═══════════════════════════════════════════════════════════════
# Cette queue est LA source unique de vérité pour les opérations
operation_queue = deque()
latest_image = {"base64": None, "timestamp": None}
queue_lock = threading.Lock()  # Prévient les race conditions


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS HTTP
# ═══════════════════════════════════════════════════════════════

@app.route("/")
def home():
    """Page d'accueil simple."""
    return jsonify({
        "service": "Buddy Robot API",
        "version": "2.0",
        "endpoints": {
            "GET /operation": "Récupérer la prochaine opération (polling)",
            "POST /upload_image": "Upload photo caméra (base64)"
        }
    })


@app.route("/operation", methods=['GET'])
def operation():
    """
    Endpoint polled par Buddy pour récupérer les commandes.
    
    Returns:
        JSON avec l'opération à exécuter ou null si queue vide
    """
    # Log état de la queue (debugging)
    queue_id = id(operation_queue)
    queue_size = len(operation_queue)
    log(f"[/operation] GET - Queue size: {queue_size} (ID: {queue_id})")
    
    # Récupérer opération si disponible
    if operation_queue:
        with queue_lock:
            op = operation_queue.popleft()
        log(f"[/operation] Returning: {op}")
        return jsonify({"status": "success", "operation": op}), 200
    
    # Queue vide
    log(f"[/operation] Queue empty - returning null")
    return jsonify({"status": "success", "operation": None}), 200


@app.route("/upload_image", methods=['POST'])
def upload_image():
    """
    Reçoit une photo de la caméra de Buddy.
    
    Expected JSON payload:
        {"image_base64": "iVBORw0KGgoAAAANS..."}
    
    Returns:
        JSON confirmation
    """
    data = request.get_json()
    
    # Validation
    if not data or 'image_base64' not in data:
        log("[/upload_image] ERROR - Missing image_base64 parameter")
        return jsonify({
            "error": "MissingParameter",
            "message": "Le paramètre 'image_base64' est requis"
        }), 400
    
    image_base64 = data['image_base64']
    
    # Sauvegarder image (redimensionnée à 800x600)
    try:
        # Décoder base64
        image_bytes = base64.b64decode(image_base64)
        
        # Ouvrir avec Pillow
        img = Image.open(BytesIO(image_bytes))
        
        # Redimensionner (optimisation)
        img = img.resize(IMAGE_SIZE, Image.Resampling.LANCZOS)
        
        # Sauvegarder (remplace l'ancienne image)
        img.save(LATEST_IMAGE_PATH, 'PNG')
        
        # Mettre à jour timestamp
        with queue_lock:
            latest_image["timestamp"] = datetime.now().isoformat()
        
        log(f"[/upload_image] Image saved successfully ({len(image_bytes)} bytes)")
        
    except Exception as e:
        log(f"[/upload_image] ERROR saving image: {e}")
        return jsonify({
            "error": "ImageProcessingError",
            "message": str(e)
        }), 500
    
    return jsonify({
        "status": "success",
        "message": "Image reçue et sauvegardée"
    }), 200


# ═══════════════════════════════════════════════════════════════
# MODE CLI - Pour tests sans MCP
# ═══════════════════════════════════════════════════════════════

def run_cli():
    """Interface CLI interactive pour contrôler Buddy."""
    import json
    from buddy_functions import build_operation, LATEST_IMAGE_PATH
    
    print("╔════════════════════════════════════════╗")
    print("║     Buddy CLI - Mode Interactif       ║")
    print("╚════════════════════════════════════════╝")
    print("Tapez 'help' pour la liste des commandes")
    print("Tapez 'quit' pour quitter\n")
    
    while True:
        try:
            user_input = input("buddy> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Au revoir!")
            break
        
        if not user_input:
            continue
        
        parts = user_input.split()
        cmd = parts[0].lower()
        args = parts[1:]
        
        # === Commandes système ===
        if cmd in ("quit", "exit", "q"):
            print("👋 Au revoir!")
            break
        
        elif cmd == "help":
            print("""
╔═══════════════════════════════════════════════════════════════╗
║                    COMMANDES DISPONIBLES                      ║
╠═══════════════════════════════════════════════════════════════╣
║ MOUVEMENT                                                     ║
║   move <speed> <distance>    Déplacer (+ avant, - arrière)    ║
║   rotate <speed> <angle>     Tourner (+ droite, - gauche)     ║
║                                                               ║
║ COMMUNICATION                                                 ║
║   speak <message>            Parler (guillemets optionnels)   ║
║   speak <message> <volume>   Parler avec volume (100-500)     ║
║                                                               ║
║ INTERACTIONS                                                  ║
║   head <yes|no>              Hocher (yes) ou secouer (no)     ║
║   mood <emotion>             Changer humeur                   ║
║                              (happy/sad/angry/surprised/...)  ║
║                                                               ║
║ SYSTÈME                                                       ║
║   picture                    Info dernière photo              ║
║   queue                      Voir queue d'opérations          ║
║   help                       Afficher cette aide              ║
║   quit                       Quitter le CLI                   ║
╚═══════════════════════════════════════════════════════════════╝
""")
        
        # === Commandes Buddy ===
        elif cmd == "move":
            if len(args) < 2:
                print("❌ Usage: move <speed> <distance>")
                print("   Exemple: move 100 1.5")
                continue
            try:
                op = build_operation("move_buddy", 
                                    speed=float(args[0]), 
                                    distance=float(args[1]))
                with queue_lock:
                    operation_queue.append(op)
                print(f"✓ Queued: {json.dumps(op)}")
            except ValueError:
                print("❌ Erreur: speed et distance doivent être des nombres")
        
        elif cmd == "rotate":
            if len(args) < 2:
                print("❌ Usage: rotate <speed> <angle>")
                print("   Exemple: rotate 50 90")
                continue
            try:
                op = build_operation("rotate_buddy",
                                    speed=float(args[0]),
                                    angle=float(args[1]))
                with queue_lock:
                    operation_queue.append(op)
                print(f"✓ Queued: {json.dumps(op)}")
            except ValueError:
                print("❌ Erreur: speed et angle doivent être des nombres")
        
        elif cmd == "speak":
            if len(args) < 1:
                print("❌ Usage: speak <message> [volume]")
                print("   Exemple: speak Bonjour 300")
                continue
            # Parser volume si présent
            volume = 300
            message_parts = args
            if len(args) > 1 and args[-1].isdigit():
                volume = int(args[-1])
                message_parts = args[:-1]
            message = " ".join(message_parts)
            op = build_operation("speak", message=message, volume=volume)
            with queue_lock:
                operation_queue.append(op)
            print(f"✓ Queued: {json.dumps(op)}")
        
        elif cmd == "head":
            if len(args) < 1 or args[0].lower() not in ("yes", "no"):
                print("❌ Usage: head <yes|no>")
                continue
            op = build_operation("move_head", axis=args[0].lower())
            with queue_lock:
                operation_queue.append(op)
            print(f"✓ Queued: {json.dumps(op)}")
        
        elif cmd == "mood":
            valid = ["happy", "sad", "angry", "surprised", "neutral", 
                    "afraid", "disgusted", "contempt"]
            if len(args) < 1 or args[0].lower() not in valid:
                print(f"❌ Usage: mood <{' | '.join(valid)}>")
                continue
            op = build_operation("set_mood", mood=args[0].lower())
            with queue_lock:
                operation_queue.append(op)
            print(f"✓ Queued: {json.dumps(op)}")
        
        elif cmd == "picture":
            if os.path.exists(LATEST_IMAGE_PATH):
                size = os.path.getsize(LATEST_IMAGE_PATH)
                mtime = os.path.getmtime(LATEST_IMAGE_PATH)
                print(f"📸 Image: {LATEST_IMAGE_PATH}")
                print(f"   Taille: {size:,} bytes")
                print(f"   Modifiée: {datetime.fromtimestamp(mtime)}")
            else:
                print("❌ Aucune image disponible")
        
        elif cmd == "queue":
            with queue_lock:
                if operation_queue:
                    print(f"📋 Queue ({len(operation_queue)} opération(s)):")
                    for i, op in enumerate(operation_queue, 1):
                        print(f"   {i}. {json.dumps(op)}")
                else:
                    print("📋 Queue vide")
        
        else:
            print(f"❌ Commande inconnue: '{cmd}'")
            print("   Tapez 'help' pour voir les commandes disponibles")


# ═══════════════════════════════════════════════════════════════
# POINT D'ENTRÉE PRINCIPAL
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse
    
    # Parser les arguments
    parser = argparse.ArgumentParser(
        description="Buddy Flask API Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes disponibles:
  Mode Normal (défaut) - Flask + MCP Server
    python api.py
  
  Mode CLI - Flask + Interface interactive (sans MCP)
    python api.py --cli
        """
    )
    parser.add_argument("--cli", action="store_true",
                       help="Lancer en mode CLI (Flask only, pas de MCP)")
    
    args = parser.parse_args()
    
    if args.cli:
        # ═══ MODE CLI ═══
        print("\n🚀 Démarrage en mode CLI...")
        
        # Supprimer logs Flask (pour garder CLI propre)
        werkzeug_log = logging.getLogger('werkzeug')
        werkzeug_log.setLevel(logging.ERROR)
        
        # Démarrer Flask en arrière-plan
        flask_thread = threading.Thread(
            target=lambda: app.run(host='0.0.0.0', port=5000, 
                                  debug=False, threaded=True),
            daemon=True
        )
        flask_thread.start()
        print("✓ Flask server started on http://0.0.0.0:5000\n")
        
        # Lancer CLI interactif
        run_cli()
    
    else:
        # ═══ MODE NORMAL (Flask + MCP) ═══
        import asyncio
        from buddy_functions import init_shared_state
        from mcp_server import run_server
        
        print("\n🚀 Démarrage en mode MCP...")
        
        # Initialiser shared state pour buddy_functions
        init_shared_state(operation_queue, latest_image, queue_lock)
        log("✓ Shared state initialized")
        
        # Supprimer logs Flask (perturbent MCP sur stdout)
        werkzeug_log = logging.getLogger('werkzeug')
        werkzeug_log.setLevel(logging.ERROR)
        
        # Démarrer Flask en arrière-plan
        flask_thread = threading.Thread(
            target=lambda: app.run(host='0.0.0.0', port=5000,
                                  debug=False, threaded=True),
            daemon=True
        )
        flask_thread.start()
        log("✓ Flask server started on http://0.0.0.0:5000")
        
        # Démarrer MCP server (bloquant - thread principal)
        log("✓ Starting MCP server on stdio...")
        asyncio.run(run_server())
```

**Points clés du code** :
- ✅ Deux endpoints: `/operation` et `/upload_image`
- ✅ Queue partagée thread-safe avec `queue_lock`
- ✅ Support de deux modes: Normal (MCP) et CLI
- ✅ Logs vers stderr (ne perturbent pas MCP)
- ✅ Redimensionnement automatique des images

---

### Étape 4 : Fonctions Buddy (buddy_functions.py)

Créer `buddy_functions.py` **complet** :

```python
"""
Implémentations des outils pour contrôler Buddy.
Chaque fonction crée une opération qui sera envoyée à l'API REST.
"""

import json
import sys
import os
import base64
from mcp.types import TextContent, ImageContent

# ═══════════════════════════════════════════════════════════════
# SHARED STATE - Initialisé par api.py
# ═══════════════════════════════════════════════════════════════
operation_queue = None
latest_image = None
queue_lock = None

# Path vers l'image la plus récente
LATEST_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "latest_image.png")


# ═══════════════════════════════════════════════════════════════
# UTILITAIRES
# ═══════════════════════════════════════════════════════════════

def log(msg):
    """Log vers stderr (stdout réservé pour MCP)."""
    print(f"[buddy_functions] {msg}", file=sys.stderr)


def init_shared_state(queue, image, lock):
    """
    Initialise l'état partagé avec Flask.
    Appelé par api.py au démarrage.
    
    Args:
        queue: deque() - File d'opérations partagée
        image: dict - Dernière image et timestamp
        lock: threading.Lock - Verrou thread-safe
    """
    global operation_queue, latest_image, queue_lock
    operation_queue = queue
    latest_image = image
    queue_lock = lock
    log("Shared state initialized successfully")


def queue_operation(operation: dict, message: str):
    """
    Ajoute une opération à la queue (thread-safe).
    
    Args:
        operation: dict - Opération au format API REST
        message: str - Message de confirmation
    
    Returns:
        list[TextContent] - Réponse MCP
    """
    with queue_lock:
        operation_queue.append(operation)
        size = len(operation_queue)
        qid = id(operation_queue)
    
    # Log détaillé pour debugging
    log(f"Queued: {json.dumps(operation)}")
    log(f"Queue size: {size} (ID: {qid})")
    
    # Réponse avec JSON formaté
    return [TextContent(
        type="text",
        text=f"{message}\n\n```json\n{json.dumps(operation, indent=2)}\n```"
    )]


# ═══════════════════════════════════════════════════════════════
# TOOLS - Implémentations
# ═══════════════════════════════════════════════════════════════

def move_buddy(speed: float, distance: float):
    """
    Déplace Buddy en avant ou en arrière.
    
    RÈGLES CRITIQUES:
    - speed: DOIT être positive (direction = signe de distance)
    - distance: positive = avant, négative = arrière
    
    Args:
        speed: Vitesse (0-500, recommandé 50-200)
        distance: Distance en mètres (+ ou -)
    
    Returns:
        MCP response
    """
    # Force speed positive (règle critique)
    speed = abs(speed)
    
    operation = {
        "type": "MoveOperation",
        "speed": speed,
        "distance": distance
    }
    
    # Direction basée sur signe de distance
    direction = "forward" if distance > 0 else "backward"
    
    return queue_operation(
        operation,
        f"Queued move {direction} at speed {speed} for {abs(distance)}m"
    )


def rotate_buddy(speed: float, angle: float):
    """
    Fait tourner Buddy.
    
    RÈGLES CRITIQUES:
    - speed: DOIT être positive
    - angle: positif = droite, négatif = gauche
    
    Args:
        speed: Vitesse rotation (0-500, recommandé 30-100)
        angle: Angle en degrés (+ ou -)
    
    Returns:
        MCP response
    """
    # Force speed positive
    speed = abs(speed)
    
    operation = {
        "type": "RotateOperation",
        "speed": speed,
        "angle": angle
    }
    
    # Direction basée sur signe d'angle
    direction = "right" if angle > 0 else "left"
    
    return queue_operation(
        operation,
        f"Queued rotation {direction} at speed {speed} for {abs(angle)}°"
    )


def speak(message: str, volume: int = 300):
    """
    Fait parler Buddy.
    
    Args:
        message: Texte à prononcer
        volume: Volume 100-500 (défaut: 300)
    
    Returns:
        MCP response
    """
    operation = {
        "type": "TalkOperation",
        "message": message,
        "volume": volume
    }
    
    return queue_operation(
        operation,
        f"Queued speech: '{message}' at volume {volume}"
    )


def move_head(axis: str, speed: float = 40.0, angle: float = 20.0):
    """
    Fait hocher ou secouer la tête de Buddy.
    
    Args:
        axis: "yes" (hocher) ou "no" (secouer)
        speed: Vitesse (défaut: 40.0)
        angle: Angle (défaut: 20.0)
    
    Returns:
        MCP response
    """
    # Convertir en format API
    axis_value = "Yes" if axis.lower() == "yes" else "No"
    
    operation = {
        "type": "HeadOperation",
        "speed": speed,
        "angle": angle,
        "axis": axis_value
    }
    
    action = "nod" if axis_value == "Yes" else "shake"
    
    return queue_operation(
        operation,
        f"Queued head {action} at speed {speed} with angle {angle}"
    )


def set_mood(mood: str):
    """
    Change l'expression faciale de Buddy.
    
    Args:
        mood: Expression (happy, sad, angry, surprised, neutral, 
                         afraid, disgusted, contempt)
    
    Returns:
        MCP response
    """
    operation = {
        "type": "MoodOperation",
        "mood": mood.upper()
    }
    
    return queue_operation(
        operation,
        f"Queued mood change to {mood.upper()}"
    )


def take_picture():
    """
    Retourne la dernière photo de la caméra de Buddy.
    
    Returns:
        MCP response avec image base64
    """
    if not os.path.exists(LATEST_IMAGE_PATH):
        return [TextContent(
            type="text",
            text="No image available. Buddy hasn't sent any image yet."
        )]
    
    try:
        # Lire le fichier image
        with open(LATEST_IMAGE_PATH, 'rb') as f:
            image_bytes = f.read()
        
        # Encoder en base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Récupérer timestamp (thread-safe)
        with queue_lock:
            timestamp = latest_image.get("timestamp", "unknown")
        
        # Retourner texte + image
        return [
            TextContent(
                type="text",
                text=f"Image captured at {timestamp}"
            ),
            ImageContent(
                type="image",
                data=image_base64,
                mimeType="image/png"
            )
        ]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error reading image: {e}"
        )]


def multi_action(actions: list):
    """
    Exécute plusieurs actions SIMULTANÉMENT.
    
    RÈGLE CRITIQUE: Ne JAMAIS combiner move et rotate !
    
    Args:
        actions: Liste de dicts avec type + paramètres
                 Exemple: [
                     {"type": "move", "speed": 100, "distance": 1},
                     {"type": "talk", "message": "J'arrive!"}
                 ]
    
    Returns:
        MCP response
    """
    operations = []
    descriptions = []
    
    for action in actions:
        action_type = action.get("type")
        
        if action_type == "move":
            speed = abs(action.get("speed", 100))
            distance = action.get("distance", 0)
            operations.append({
                "type": "MoveOperation",
                "speed": speed,
                "distance": distance
            })
            direction = "forward" if distance > 0 else "backward"
            descriptions.append(f"move {direction} {abs(distance)}m")
        
        elif action_type == "rotate":
            speed = abs(action.get("speed", 50))
            angle = action.get("angle", 0)
            operations.append({
                "type": "RotateOperation",
                "speed": speed,
                "angle": angle
            })
            direction = "right" if angle > 0 else "left"
            descriptions.append(f"rotate {direction} {abs(angle)}°")
        
        elif action_type == "talk":
            message = action.get("message", "")
            volume = action.get("volume", 300)
            operations.append({
                "type": "TalkOperation",
                "message": message,
                "volume": volume
            })
            descriptions.append(f"say '{message}'")
        
        elif action_type == "head":
            axis = action.get("axis", "yes")
            axis_value = "Yes" if axis.lower() == "yes" else "No"
            speed = action.get("speed", 40.0)
            angle = action.get("angle", 20.0)
            operations.append({
                "type": "HeadOperation",
                "speed": speed,
                "angle": angle,
                "axis": axis_value
            })
            head_action = "nod" if axis_value == "Yes" else "shake"
            descriptions.append(f"{head_action} head")
        
        elif action_type == "mood":
            mood = action.get("mood", "NEUTRAL")
            operations.append({
                "type": "MoodOperation",
                "mood": mood.upper()
            })
            descriptions.append(f"set mood to {mood}")
    
    # Créer MultiOperation
    multi_operation = {
        "type": "MultiOperation",
        "operations": operations
    }
    
    # Message descriptif
    description = " + ".join(descriptions)
    message = f"Queued multi-action: {description} ({len(operations)} ops)"
    
    return queue_operation(multi_operation, message)


# ═══════════════════════════════════════════════════════════════
# TOOL HANDLERS - Dispatch dictionary
# ═══════════════════════════════════════════════════════════════


TOOL_HANDLERS = {
    "move_buddy": move_buddy,
    "rotate_buddy": rotate_buddy,
    "speak": speak,
    "move_head": move_head,
    "set_mood": set_mood,
    "take_picture": take_picture,
    "multi_action": multi_action,
}


# ═══════════════════════════════════════════════════════════════
# CLI SUPPORT - Utilisé par api.py en mode --cli
# ═══════════════════════════════════════════════════════════════

def build_operation(name: str, **kwargs) -\> dict:
    """
    Construit une opération pour la queue (mode CLI).
    
    Args:
        name: Nom du tool
        **kwargs: Paramètres du tool
    
    Returns:
        dict - Opération au format API REST
    """
    if name == "move_buddy":
        return {
            "type": "MoveOperation",
            "speed": kwargs["speed"],
            "distance": kwargs["distance"]
        }
    
    elif name == "rotate_buddy":
        return {
            "type": "RotateOperation",
            "speed": kwargs["speed"],
            "angle": kwargs["angle"]
        }
    
    elif name == "speak":
        return {
            "type": "TalkOperation",
            "message": kwargs["message"],
            "volume": kwargs.get("volume", 300)
        }
    
    elif name == "move_head":
        axis_value = "Yes" if kwargs["axis"].lower() == "yes" else "No"
        return {
            "type": "HeadOperation",
            "speed": kwargs.get("speed", 40.0),
            "angle": kwargs.get("angle", 20.0),
            "axis": axis_value
        }
    
    elif name == "set_mood":
        return {
            "type": "MoodOperation",
            "mood": kwargs["mood"].upper()
        }
    
    else:
        return None
```

**Fonctionnalités clés** :
- ✅ 8 tools implémentés
- ✅ Validation automatique (speed > 0)
- ✅ Thread-safe avec queue_lock
- ✅ Logs détaillés
- ✅ Support CLI via build_operation()

---

### Étape 5 : Serveur MCP (mcp_server.py)

Créer le fichier `mcp_server.py` avec le code **complet** suivant :

```python
"""
MCP Server pour Buddy Robot Control

Ce serveur expose les fonctionnalités de contrôle de Buddy
à Claude Desktop via le protocole MCP (Model Context Protocol).

Transport: stdio (stdin/stdout)
Communication: JSON-RPC 2.0
"""

import asyncio
import sys
import threading
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import des fonctions Buddy
from buddy_functions import (
    init_shared_state,
    move_buddy,
    rotate_buddy,
    speak,
    move_head,
    set_mood,
    take_picture,
    multi_action,
    TOOL_HANDLERS
)


def log(msg):
    """Log vers stderr (stdout réservé pour MCP JSON-RPC)."""
    print(f"[MCP Server] {msg}", file=sys.stderr)


# ═══════════════════════════════════════════════════════════════
# CRÉATION DU SERVEUR MCP
# ═══════════════════════════════════════════════════════════════

app = Server("buddy-mcp-server")


# ═══════════════════════════════════════════════════════════════
# LISTE DES TOOLS - Découverte par Claude
# ═══════════════════════════════════════════════════════════════

@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    Liste tous les tools disponibles pour Claude Desktop.
    Appelé automatiquement au démarrage de la connexion MCP.
    
    Returns:
        Liste des tools avec descriptions et schémas
    """
    log("Claude Desktop requested tool list")
    
    return [
        # ═══════════════════════════════════════════════════════
        # TOOL 1: move_buddy
        # ═══════════════════════════════════════════════════════
        Tool(
            name="move_buddy",
            description=(
                "Move Buddy forward or backward. "
                "IMPORTANT: Speed must always be POSITIVE. "
                "Direction is controlled by distance sign (+ forward, - backward). "
                "Example: move_buddy(speed=100, distance=-0.5) moves backward."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "number",
                        "description": (
                            "Movement speed - MUST be positive (recommended: 50-200). "
                            "Direction is NOT determined by speed."
                        ),
                        "minimum": 0,
                        "maximum": 500
                    },
                    "distance": {
                        "type": "number",
                        "description": (
                            "Distance to move in meters. "
                            "POSITIVE = forward, NEGATIVE = backward. "
                            "Example: 0.5 moves forward, -0.5 moves backward."
                        ),
                    }
                },
                "required": ["speed", "distance"]
            }
        ),
        
        # ═══════════════════════════════════════════════════════
        # TOOL 2: rotate_buddy
        # ═══════════════════════════════════════════════════════
        Tool(
            name="rotate_buddy",
            description=(
                "Rotate Buddy left or right. "
                "IMPORTANT: Speed must always be POSITIVE. "
                "Direction is controlled by angle sign (+ right, - left). "
                "Example: rotate_buddy(speed=50, angle=-90) rotates left."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "number",
                        "description": (
                            "Rotation speed - MUST be positive (recommended: 50-200). "
                            "Direction is NOT determined by speed."
                        ),
                        "minimum": 0,
                        "maximum": 500
                    },
                    "angle": {
                        "type": "number",
                        "description": (
                            "Angle to rotate in degrees. "
                            "POSITIVE = turn right, NEGATIVE = turn left. "
                            "Example: 90 turns right, -90 turns left."
                        ),
                    }
                },
                "required": ["speed", "angle"]
            }
        ),
        
        # ═══════════════════════════════════════════════════════
        # TOOL 3: speak
        # ═══════════════════════════════════════════════════════
        Tool(
            name="speak",
            description=(
                "Make Buddy say something out loud. "
                "Use this for standalone speech. "
                "If you want Buddy to talk WHILE doing something else "
                "(moving, rotating), use multi_action instead."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The text that Buddy should speak"
                    },
                    "volume": {
                        "type": "integer",
                        "description": "Volume level (100-500, default: 300)",
                        "minimum": 100,
                        "maximum": 500,
                        "default": 300
                    }
                },
                "required": ["message"]
            }
        ),
        
        # ═══════════════════════════════════════════════════════
        # TOOL 4: move_head
        # ═══════════════════════════════════════════════════════
        Tool(
            name="move_head",
            description=(
                "Make Buddy nod (yes) or shake (no) his head. "
                "Use 'yes' for agreement/approval or 'no' for disagreement/disapproval. "
                "Can be combined with other actions using multi_action "
                "(e.g., nod while saying 'Yes!')"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "axis": {
                        "type": "string",
                        "description": "Head movement type",
                        "enum": ["yes", "no"]
                    },
                    "speed": {
                        "type": "number",
                        "description": "Movement speed (default: 40.0)",
                        "minimum": 0,
                        "maximum": 100,
                        "default": 40.0
                    },
                    "angle": {
                        "type": "number",
                        "description": "Movement angle (default: 20.0)",
                        "minimum": 0,
                        "maximum": 90,
                        "default": 20.0
                    }
                },
                "required": ["axis"]
            }
        ),
        
        # ═══════════════════════════════════════════════════════
        # TOOL 5: set_mood
        # ═══════════════════════════════════════════════════════
        Tool(
            name="set_mood",
            description=(
                "Change Buddy's facial expression/mood displayed on the screen. "
                "Use this to convey emotions visually. "
                "Can be combined with speech and gestures using multi_action "
                "for more expressive interactions (e.g., smile while saying 'Hello!')"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "mood": {
                        "type": "string",
                        "description": "The mood/expression to display",
                        "enum": [
                            "happy", "sad", "angry", "surprised",
                            "neutral", "afraid", "disgusted", "contempt"
                        ]
                    }
                },
                "required": ["mood"]
            }
        ),
        
        # ═══════════════════════════════════════════════════════
        # TOOL 6: take_picture
        # ═══════════════════════════════════════════════════════
        Tool(
            name="take_picture",
            description=(
                "Capture and return the latest image from Buddy's camera. "
                "Returns the image with timestamp. "
                "Use this to see what Buddy sees, analyze the environment, "
                "or track a person."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        
        # ═══════════════════════════════════════════════════════
        # TOOL 7: multi_action (ADVANCED)
        # ═══════════════════════════════════════════════════════
        Tool(
            name="multi_action",
            description=(
                "Execute multiple actions SIMULTANEOUSLY. "
                "This makes Buddy more fluid and natural by doing several things at once. "
                "Examples: move while talking, rotate while speaking, "
                "greet someone (talk + nod + smile). "
                "Use this instead of calling individual tools sequentially "
                "when you want Buddy to multitask. "
                "CRITICAL: NEVER combine 'move' and 'rotate' together!"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "actions": {
                        "type": "array",
                        "description": (
                            "List of actions to execute simultaneously. "
                            "Each action has a 'type' and its specific parameters."
                        ),
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "description": (
                                        "Type of action: "
                                        "'move' (move forward/backward), "
                                        "'rotate' (turn left/right), "
                                        "'talk' (speak), "
                                        "'head' (nod/shake), "
                                        "'mood' (facial expression)"
                                    ),
                                    "enum": ["move", "rotate", "talk", "head", "mood"]
                                },
                                "speed": {
                                    "type": "number",
                                    "description": "Speed parameter (for move/rotate/head actions). Must be positive."
                                },
                                "distance": {
                                    "type": "number",
                                    "description": "Distance in meters (for move action). Positive = forward, negative = backward."
                                },
                                "angle": {
                                    "type": "number",
                                    "description": "Angle in degrees (for rotate/head actions). Positive = right/yes, negative = left/no."
                                },
                                "message": {
                                    "type": "string",
                                    "description": "Text to speak (for talk action)"
                                },
                                "volume": {
                                    "type": "integer",
                                    "description": "Volume level 100-500 (for talk action, default: 300)"
                                },
                                "axis": {
                                    "type": "string",
                                    "description": "Head movement type (for head action): 'yes' = nod, 'no' = shake",
                                    "enum": ["yes", "no"]
                                },
                                "mood": {
                                    "type": "string",
                                    "description": "Facial expression (for mood action)",
                                    "enum": [
                                        "happy", "sad", "angry", "surprised",
                                        "neutral", "afraid", "disgusted", "contempt"
                                    ]
                                }
                            },
                            "required": ["type"]
                        },
                        "minItems": 1
                    }
                },
                "required": ["actions"]
            }
        )
    ]


# ═══════════════════════════════════════════════════════════════
# CALL TOOL - Exécution des tools
# ═══════════════════════════════════════════════════════════════


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Gère l'exécution des tools demandés par Claude.
    
    Args:
        name: Nom du tool à exécuter
        arguments: Paramètres du tool
    
    Returns:
        Réponse MCP (liste de TextContent/ImageContent)
    """
    log(f"Tool called: {name} with args: {arguments}")
    
    # Vérifier que le tool existe
    if name not in TOOL_HANDLERS:
        error_msg = f"Unknown tool: {name}"
        log(f"ERROR: {error_msg}")
        return [TextContent(
            type="text",
            text=f"Error: {error_msg}"
        )]
    
    try:
        # Appeler le handler correspondant
        handler = TOOL_HANDLERS[name]
        result = handler(**arguments)
        
        log(f"Tool '{name}' executed successfully")
        return result
    
    except Exception as e:
        error_msg = f"Error executing {name}: {str(e)}"
        log(f"ERROR: {error_msg}")
        
        # Log stack trace pour debugging
        import traceback
        log(f"Stack trace:\n{traceback.format_exc()}")
        
        return [TextContent(
            type="text",
            text=f"Error: {error_msg}"
        )]


# ═══════════════════════════════════════════════════════════════
# SERVEUR PRINCIPAL
# ═══════════════════════════════════════════════════════════════

async def run_server():
    """
    Point d'entrée principal du serveur MCP.
    Utilise stdio transport (stdin/stdout) pour communication avec Claude Desktop.
    
    IMPORTANT:
    - L'état partagé (queue, image, lock) DOIT être initialisé par api.py
      AVANT d'appeler cette fonction
    - stdout est RÉSERVÉ pour le protocole MCP (JSON-RPC)
    - Tous les logs vont vers stderr
    """
    log("="*60)
    log("Starting Buddy MCP Server...")
    log("="*60)
    log("Shared state should be initialized by api.py")
    log("Transport: stdio (stdin/stdout)")
    log("Protocol: JSON-RPC 2.0 via MCP")
    log("="*60)
    
    try:
        # Créer transport stdio
        async with stdio_server() as (read_stream, write_stream):
            log("✓ stdio transport created successfully")
            log("✓ Waiting for Claude Desktop connection...")
            
            # Lancer le serveur MCP
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    
    except Exception as e:
        log(f"FATAL ERROR in MCP server: {e}")
        import traceback
        log(f"Stack trace:\n{traceback.format_exc()}")
        raise


# ═══════════════════════════════════════════════════════════════
# POINT D'ENTRÉE (si exécuté directement)
# ═══════════════════════════════════════════════════════════════

def main():
    """
    Point d'entrée si le serveur MCP est exécuté directement.
    
    NOTE: En production, c'est api.py qui lance ce serveur.
    Cette fonction est ici pour tests/debugging uniquement.
    """
    try:
        log("⚠️ WARNING: Running MCP server in standalone mode")
        log("⚠️ Shared state NOT initialized - Queue will be empty!")
        log("⚠️ For production, use: python api.py")
        
        asyncio.run(run_server())
    
    except KeyboardInterrupt:
        log("\n✓ Server stopped by user (Ctrl+C)")
    
    except Exception as e:
        log(f"✗ Server error: {e}")
        import traceback
        log(f"Stack trace:\n{traceback.format_exc()}")
        raise


if __name__ == "__main__":
    main()
```

**Points clés du code** :
- ✅ 8 tools exposés avec descriptions détaillées
- ✅ Schémas JSON complets pour chaque tool
- ✅ Gestion d'erreurs robuste avec stack traces
- ✅ Logs vers stderr (stdout réservé MCP)
- ✅ Support standalone pour debugging

---

## ⚙️ Configuration Claude Desktop

### Étape 6.1 : Localiser le fichier de configuration

Le fichier de configuration Claude Desktop varie selon l'OS :

**Windows** :
```
%APPDATA%\Claude\claude_desktop_config.json
```
Chemin complet typique :
```
C:\Users\<VotreNom>\AppData\Roaming\Claude\claude_desktop_config.json
```

**macOS** :
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Linux** :
```
~/.config/Claude/claude_desktop_config.json
```

### Étape 6.2 : Créer/Éditer le fichier de configuration

**Si le fichier n'existe pas** :

```powershell
# Windows PowerShell
New-Item -Path "$env:APPDATA\Claude\claude_desktop_config.json" -ItemType File -Force

# Ouvrir avec notepad
notepad "$env:APPDATA\Claude\claude_desktop_config.json"
```

**Contenu complet du fichier** `claude_desktop_config.json` :

```json
{
  "mcpServers": {
    "buddy": {
      "command": "python",
      "args": [
        "C:\\Users\\<VotreNom>\\flaskBuddy\\api.py"
      ],
      "env": {}
    }
  }
}
```

**⚠️ IMPORTANT** : Remplacez `<VotreNom>` et le chemin par votre chemin réel !

**Exemple avec chemin réel** :
```json
{
  "mcpServers": {
    "buddy": {
      "command": "python",
      "args": [
        "C:\\Users\\Elissanna Barcet\\Downloads\\flaskBuddy-main\\flaskBuddy-main\\api.py"
      ],
      "env": {}
    }
  }
}
```

### Étape 6.3 : Vérifier le chemin Python

**Test rapide** :
```powershell
# Windows
where python

# macOS/Linux
which python3
```

Si Python n'est pas dans le PATH, utiliser le chemin complet :

```json
{
  "mcpServers": {
    "buddy": {
      "command": "C:\\Users\\<VotreNom>\\AppData\\Local\\Programs\\Python\\Python311\\python.exe",
      "args": [
        "C:\\Users\\<VotreNom>\\flaskBuddy\\api.py"
      ],
      "env": {}
    }
  }
}
```

### Étape 6.4 : Configuration avec environnement virtuel

Si vous utilisez un **venv** (recommandé) :

```json
{
  "mcpServers": {
    "buddy": {
      "command": "C:\\Users\\<VotreNom>\\flaskBuddy\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\<VotreNom>\\flaskBuddy\\api.py"
      ],
      "env": {
        "PYTHONPATH": "C:\\Users\\<VotreNom>\\flaskBuddy"
      }
    }
  }
}
```

### Étape 6.5 : Redémarrer Claude Desktop

**CRITIQUE** : Après avoir modifié la configuration :

1. **Fermer complètement** Claude Desktop
2. **Attendre 5 secondes**
3. **Rouvrir** Claude Desktop
4. Claude devrait détecter automatiquement le serveur MCP

---

## 🚀 Déploiement & Tests

### Étape 7 : Configuration réseau Buddy

#### 7.1 : Trouver votre adresse IP

```powershell
# Windows
ipconfig

# Chercher "IPv4 Address"
# Exemple: 192.168.1.100
```

```bash
# macOS/Linux
ifconfig | grep "inet "
# Ou
ip addr show
```

#### 7.2 : Autoriser le pare-feu Windows

```powershell
# Exécuter PowerShell EN TANT QU'ADMINISTRATEUR

# Créer règle pare-feu
New-NetFirewallRule `
  -DisplayName "Flask Buddy API" `
  -Direction Inbound `
  -LocalPort 5000 `
  -Protocol TCP `
  -Action Allow

# Vérifier la règle
Get-NetFirewallRule -DisplayName "Flask Buddy API"
```

**Si vous n'avez pas les droits admin** :
- Aller dans "Pare-feu Windows Defender" → Paramètres avancés
- Règles de trafic entrant → Nouvelle règle
- Port → TCP → Port 5000 → Autoriser

#### 7.3 : Tester l'accessibilité réseau

```powershell
# Sur votre PC (terminal 1)
python api.py --cli

# Sur Buddy ou autre appareil (navigateur ou curl)
curl http://<VOTRE_IP>:5000/operation

# Devrait retourner:
# {"status":"success","operation":null}
```

### Étape 8 : Premier lancement

#### 8.1 : Mode CLI (Test sans Claude)

```bash
# Terminal
python api.py --cli
```

Vous devriez voir :
```
🚀 Démarrage en mode CLI...
✓ Flask server started on http://0.0.0.0:5000

╔════════════════════════════════════════╗
║     Buddy CLI - Mode Interactif       ║
╚════════════════════════════════════════╝
Tapez 'help' pour la liste des commandes
Tapez 'quit' pour quitter

buddy>
```

**Tests CLI** :
```bash
buddy> help              # Voir les commandes
buddy> move 100 1.0      # Queue move forward
buddy> queue             # Voir la queue
buddy> speak Bonjour     # Queue speak
buddy> quit              # Quitter
```

#### 8.2 : Mode MCP (Production avec Claude)

**Terminal** :
```bash
python api.py
```

Vous devriez voir :
```
🚀 Démarrage en mode MCP...
[buddy_functions] Shared state initialized successfully
✓ Shared state initialized
✓ Flask server started on http://0.0.0.0:5000
✓ Starting MCP server on stdio...
[MCP Server] ============================================================
[MCP Server] Starting Buddy MCP Server...
[MCP Server] ============================================================
[MCP Server] Shared state should be initialized by api.py
[MCP Server] Transport: stdio (stdin/stdout)
[MCP Server] Protocol: JSON-RPC 2.0 via MCP
[MCP Server] ============================================================
```

**Claude Desktop** devrait maintenant afficher en bas :
```
🔌 MCP: buddy (connected)
```

#### 8.3 : Vérifier la connexion MCP

Dans Claude Desktop, tapez :
```
"Quels tools as-tu pour contrôler Buddy ?"
```

Claude devrait répondre avec la liste des 8 tools.

### Étape 9 : Tests de validation

#### Test 1 : Mouvement simple

**Dans Claude** :
```
"Buddy, avance de 1 mètre à vitesse normale"
```

**Dans terminal Python**, vous devriez voir :
```
[MCP Server] Tool called: move_buddy with args: {'speed': 100, 'distance': 1.0}
[buddy_functions] Queued: {"type":"MoveOperation","speed":100,"distance":1.0}
[buddy_functions] Queue size: 1 (ID: ...)
```

**Depuis Buddy** (polling) :
```bash
curl http://<VOTRE_IP>:5000/operation
```

Devrait retourner :
```json
{
  "status": "success",
  "operation": {
    "type": "MoveOperation",
    "speed": 100,
    "distance": 1.0
  }
}
```

#### Test 2 : MultiAction

**Dans Claude** :
```
"Buddy, avance en disant 'J'arrive' avec un sourire"
```

Claude devrait utiliser `multi_action` avec :
- move (distance positive)
- talk (message "J'arrive")
- mood (happy)

#### Test 3 : Upload photo

**Simuler upload depuis Buddy** :
```bash
# Créer une image test base64
echo "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" | base64 -d > test.png
base64 test.png > test_b64.txt

# Upload
curl -X POST http://localhost:5000/upload_image \
  -H "Content-Type: application/json" \
  -d '{"image_base64":"<CONTENU DE test_b64.txt>"}'
```

**Dans Claude** :
```
"Prends une photo et dis-moi ce que tu vois"
```

Claude devrait voir l'image de test.

---

## 💡 Utilisation avancée

### Exemple 1 : Séquence d'actions complexe

```
"Buddy, fais une démonstration de tes capacités"
```

Claude peut enchaîner :
```javascript
1. speak("Bonjour! Je suis Buddy")
2. multi_action([
     {type: "head", axis: "yes"},
     {type: "mood", mood: "happy"}
   ])
3. multi_action([
     {type: "rotate", speed: 50, angle: 360},
     {type: "talk", message: "Je peux tourner sur moi-même"}
   ])
4. multi_action([
     {type: "move", speed: 100, distance: 1.0},
     {type: "talk", message: "Et me déplacer"}
   ])
5. take_picture()
6. speak("Voilà ce que je vois!")
```

### Exemple 2 : Mode gardien


```
"Buddy, surveille la pièce et alerte-moi si tu vois quelqu'un"
```

Claude peut implémenter :
```python
while True:
    photo = track_person()
    if person_detected(photo):
        multi_action([
            {type: "talk", message: "Alerte! Quelqu'un est détecté!"},
            {type: "mood", mood: "surprised"}
        ])
        track_person("move_forward", "Approche pour identifier")
        break
    else:
        track_person("search", "Je surveille...")
        wait(5 seconds)
```

---

## 🔧 Troubleshooting détaillé

### Problème 1 : Claude ne voit pas les tools

**Symptômes** :
- Claude dit "Je ne peux pas contrôler Buddy"
- Pas d'icône MCP en bas de Claude Desktop

**Solutions** :

1. **Vérifier config** :
```powershell
cat "$env:APPDATA\Claude\claude_desktop_config.json"
```

2. **Vérifier chemins** :
- Chemin Python correct ?
- Chemin api.py correct ?
- Barres obliques inversées doublées ( `\\` ) ?

3. **Vérifier logs MCP** :
```powershell
# Windows
cat "$env:APPDATA\Claude\logs\mcp.log"
```

4. **Redémarrer Claude** :
- Fermer COMPLÈTEMENT (pas juste la fenêtre)
- Attendre 5 secondes
- Rouvrir

5. **Tester manuellement** :
```powershell
python C:\chemin\vers\api.py
# Devrait démarrer sans erreur
```

---

### Problème 2 : L'API ne démarre pas

**Symptômes** :
```
ModuleNotFoundError: No module named 'flask'
```

**Solution** :
```bash
# Vérifier environnement
pip list | grep -i flask

# Réinstaller
pip install flask mcp pillow

# Ou depuis requirements.txt
pip install -r requirements.txt
```

---

### Problème 3 : Buddy ne reçoit pas les opérations

**Symptômes** :
- Queue toujours vide côté Buddy
- `GET /operation` retourne toujours `null`

**Diagnostic** :

1. **Vérifier la queue** dans terminal Python :
```
# Doit afficher quand Claude envoie commande :
[buddy_functions] Queued: {"type":"MoveOperation",...}
[buddy_functions] Queue size: 1
```

2. **Tester endpoint** :
```bash
# Depuis Claude, envoyer commande
# Puis immédiatement :
curl http://localhost:5000/operation
```

3. **Vérifier Queue ID** :
Les logs doivent montrer le **même** Queue ID partout :
```
[buddy_functions] Queue size: 1 (ID: 2234567890123)
[/operation] Queue size: 1 (ID: 2234567890123)  # ← DOIT être identique
```

**Si IDs différents** → Queue pas partagée correctement !

---

### Problème 4 : Images ne fonctionnent pas

**Symptômes** :
- `take_picture()` retourne "No image available"

**Solutions** :

1. **Vérifier fichier existe** :
```bash
ls -l latest_image.png
# Doit exister et avoir une taille > 0
```

2. **Tester upload** :
```bash
curl -X POST http://localhost:5000/upload_image \
  -H "Content-Type: application/json" \
  -d '{"image_base64":"iVBORw0KGgoAAAANSU..."}'
```

3. **Vérifier permissions** :
```bash
chmod 666 latest_image.png  # Linux/macOS
```

---

### Problème 5 : Conflit rotate + move

**Symptômes** :
- Buddy ne bouge plus correctement
- Commandes ignorées

**Solution** :

**JAMAIS** faire dans `multi_action` :
```javascript
// ❌ INTERDIT !
multi_action([
  {type: "move", ...},
  {type: "rotate", ...}
])
```

**Toujours** séparer :
```javascript
// ✅ CORRECT
move_buddy(...)
// Attendre fin
rotate_buddy(...)
```

Ou utiliser `track_person()` qui garantit la sécurité.

---

## 🛠️ Développement & Contribution

### Structure complète du projet

```
flask Buddy/
├── api.py                      # Flask API (241 lignes)
├── buddy_functions.py          # Implémentations tools (400 lignes)
├── mcp_server.py               # Serveur MCP (285 lignes)
├── requirements.txt            # Dépendances
├── README.md                   # Documentation (cette page)
├── .gitignore                  # Fichiers ignorés Git
├── .venv/                      # Environnement virtuel (ne pas commit)
├── latest_image.png            # Dernière photo (ne pas commit)
└── __pycache__/                # Cache Python (ne pas commit)
```

### Fichier .gitignore recommandé

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/

# Images
latest_image.png
*.jpg
*.jpeg
*.png

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
```

### Ajouter un nouveau tool

1. **Dans `buddy_functions.py`** :
```python
def my_new_tool(param1: str):
    """Description."""
    operation = {
        "type": "MyNewOperation",
        "param1": param1
    }
    return queue_operation(operation, "Mon tool exécuté")

# Ajouter au dict
TOOL_HANDLERS["my_new_tool"] = my_new_tool
```

2. **Dans `mcp_server.py`** :
```python
# Dans list_tools(), ajouter:
Tool(
    name="my_new_tool",
    description="Description pour Claude",
    inputSchema={
        "type": "object",
        "properties": {
            "param1": {"type": "string"}
        },
        "required": ["param1"]
    }
)

# Dans imports:
from buddy_functions import (
    # ... existing
    my_new_tool,
)
```

### Contribuer au projet

1. Fork le repository
2. Créer une branche :
```bash
git checkout -b feature/amazing-feature
```

3. Commit vos changements :
```bash
git commit -m "feat: Add amazing feature"
```

4. Push vers GitHub :
```bash
git push origin feature/amazing-feature
```

5. Créer une Pull Request

---

## 📚 Ressources additionnelles

- **MCP Documentation** : https://modelcontextprotocol.io/
- **Flask** : https://flask.palletsprojects.com/
- **Claude Desktop** : https://claude.ai/download
- **Repository GitHub** : https://github.com/Nokiwholaughs/Buddy

---

## ✅ Checklist de démarrage rapide

- [ ] Python 3.8+ installé
- [ ] Dépendances installées (`pip install -r requirements.txt`)
- [ ] Fichiers créés (api.py, buddy_functions.py, mcp_server.py)
- [ ] Configuration Claude Desktop (`claude_desktop_config.json`)
- [ ] Pare-feu configuré (port 5000)
- [ ] Buddy configuré (polling /operation)
- [ ] Test CLI réussi (`python api.py --cli`)
- [ ] Test MCP réussi (Claude voit les tools)
- [ ] Premier mouvement testé
- [ ] Photo testée

---

**🎉 Félicitations ! Votre système FlaskBuddy est opérationnel ! 🤖**

**Pour toute question** : Créez une issue sur GitHub
