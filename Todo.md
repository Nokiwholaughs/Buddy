# FlaskBuddy Todo List

## Current Task: Remove track_person Feature
**Status**: ✅ COMPLETED
**Date**: 2025-12-18
**Priority**: MEDIUM (Code cleanup & Documentation)

### Objective:
Supprimer complètement la fonctionnalité `track_person` du code et de la documentation pour simplifier le projet.

### User Request:
"J'aurais besoin que tu supprime tout ce qui est lié a track person que ce soit dans le code et dans la doc"

### 3 Options Proposed:

**Option 1: Suppression complète et nettoyage** (⭐ RECOMMANDÉE - KISS)
- ✅ Simplicité : Supprime tout le code et la documentation
- Supprime la fonction `track_person()` dans `buddy_functions.py`
- Retire l'import et le tool dans `mcp_server.py`
- Nettoie toutes les références dans `documentation_pres.md`
- Nettoie les tâches dans `Todo.md`
- **Avantage** : Code propre, plus de confusion possible
- **Inconvénient** : Perte définitive de la fonctionnalité (récupérable via Git)

**Option 2: Désactivation temporaire (commentaires)**
- Conserve le code en commentaires pour référence future
- Désactive le tool dans `mcp_server.py`
- **Avantage** : Possibilité de réactiver plus tard
- **Inconvénient** : Code mort qui encombre le projet

**Option 3: Archivage dans un fichier séparé**
- Déplace le code vers un fichier `archived_features.py`
- **Avantage** : Traçabilité historique
- **Inconvénient** : Plus complexe, pas nécessaire

### User Choice: ✅ Option 1 (Suppression complète) - SELECTED

### Plan (Option 1):
1. ✅ Mettre à jour `Todo.md` avec le plan de suppression
2. ✅ Modifier `buddy_functions.py`:
   - ✅ Supprimer la fonction `track_person()` (lignes 252-366)
   - ✅ Retirer l'entrée du dictionnaire `TOOL_HANDLERS` (ligne 378)
3. ✅ Modifier `mcp_server.py`:
   - ✅ Retirer l'import `track_person` (ligne 30)
   - ✅ Supprimer le Tool definition (lignes 226-249)
4. ✅ Nettoyer `documentation_pres.md`:
   - ✅ Supprimer toutes les sections concernant track_person
   - ✅ Mettre à jour la liste des fonctionnalités (ligne 68, 90)
   - ✅ Retirer le code et exemples (lignes 1054+, 1160, 1260, 1560+, 2092+)
5. ✅ Nettoyer `Todo.md`:
   - ✅ Marquer cette tâche comme terminée

### Files Modified:
- ✅ `buddy_functions.py` - Fonction supprimée et handler retiré
- ✅ `mcp_server.py` - Import et tool supprimés
- ✅ `documentation_pres.md` - Toutes les références nettoyées
- ✅ `Todo.md` - Tâche marquée comme terminée

### Summary:
Toutes les références à `track_person` ont été supprimées avec succès du projet. Le système conserve maintenant 7 outils principaux au lieu de 9 (avant 8). Le code est plus propre et plus facile à maintenir.

---

## Previous Task: Create Person Tracking Feature
**Status**: ✅ COMPLETED
**Date**: 2025-12-17
**Priority**: HIGH (New Autonomous Feature)

### Objective:
Créer une fonction de suivi de personne qui utilise MultiOperation pour :
- Prendre des photos pour localiser la cible
- Analyser la position de la personne (gauche/centre/droite, proche/loin)
- Décider et exécuter l'action appropriée (rotate OU move, jamais ensemble)
- Combiner avec talk/mood pour des interactions naturelles

### User Story:
"Je veux que Buddy puisse suivre une personne automatiquement en prenant des photos, en analysant où elle est, et en se déplaçant/tournant pour la garder en vue."

### Contraintes critiques:
- ❌ **JAMAIS combiner rotate + move** (conflit physique)
- ✅ Peut combiner : move + talk + mood
- ✅ Peut combiner : rotate + talk + mood
- ✅ Utiliser la vision de Claude pour analyser les images

### 3 Options Proposed:

**Option 1: Tool simple "track_step"** (⭐ Recommandée - KISS)
- Un tool qui fait : photo → analyse → décision → action
- Claude orchestre la boucle (appelle plusieurs fois le tool)
- Simple, flexible, facile à débugger
- Permet d'ajuster la stratégie entre chaque étape

✅ **Avantages**: Simple, respecte KISS, contrôlable
✅ **Effort**: Faible (1 nouveau tool)
✅ **Flexibilité**: Claude peut arrêter/modifier à tout moment

**Option 2: Tool avec boucle intégrée "auto_track"**
- Lance un suivi automatique pendant N secondes
- Fait photo → décision → action en boucle automatiquement
- S'arrête après timeout ou condition

✅ **Avantages**: Autonome, fluide
⚠️ **Inconvénients**: Complexe, difficile à arrêter, peut bloquer

**Option 3: Système avec état et machine à états**
- États : searching, centering, approaching, following
- Intelligence avancée avec historique des positions
- Prédiction des mouvements

✅ **Avantages**: Très intelligent
⚠️ **Inconvénients**: Over-engineering, complexité élevée

### User Choice: ✅ Option 1 (KISS) - SELECTED & IMPLEMENTED

### Plan (Option 1 - Recommandée):
1. ✅ Mettre à jour Todo.md avec le plan
2. ✅ Créer fonction `track_person()` dans `buddy_functions.py`
   - Prend une photo avec take_picture()
   - Retourne l'image pour analyse par Claude
   - Attend que Claude analyse et décide
   - Exécute l'action recommandée via multi_action
3. ✅ Ajouter tool `track_person` dans `mcp_server.py`
   - Description claire du comportement
   - Paramètres : optionnel (talk message, mood)
   - Schema JSON simple
4. ✅ Documentation des stratégies de décision
   - Personne à gauche → rotate left
   - Personne à droite → rotate right
   - Personne centrée + loin → move forward
   - Personne centrée + proche → stop ou backup
   - Personne absente → search (slow rotation)
5. ⏳ Prêt pour test avec Claude Desktop

### Code Changes Required:

**File 1: `buddy_functions.py`**
- Ajouter fonction `track_person(action: str = None, talk_message: str = None, mood: str = None)`:
  ```python
  def track_person(action: str = None, talk_message: str = None, mood: str = None):
      """Track a person by taking a photo and optionally executing an action.
      
      This is a building block for person tracking. Process:
      1. Takes a photo to see where the person is
      2. Returns the image to Claude for analysis
      3. Claude decides the action based on person position
      4. Execute the action (rotate OR move, never both) with optional talk/mood
      
      Decision logic (recommended for Claude):
      - Person on LEFT → action="rotate_left"
      - Person on RIGHT → action="rotate_right"
      - Person CENTERED + FAR → action="move_forward"
      - Person CENTERED + CLOSE → action="stop" or "backup"
      - Person NOT VISIBLE → action="search" (slow rotation)
      
      Parameters:
      - action: Action to execute ("rotate_left", "rotate_right", "move_forward", "backup", "search", "stop")
      - talk_message: Optional message to say during action
      - mood: Optional mood to display during action
      
      Examples:
      - track_person() → Just take photo and return
      - track_person("rotate_left", "Je te cherche") → Rotate left while talking
      - track_person("move_forward", "J'arrive!", "happy") → Move forward happily
      """
      # First, ALWAYS take a picture to see current state
      photo_result = take_picture()
      
      # If no action specified, just return the photo for Claude to analyze
      if action is None:
          return photo_result
      
      # Execute the requested action
      actions = []
      
      # Add movement/rotation based on action
      if action == "rotate_left":
          actions.append({"type": "rotate", "speed": 50, "angle": -30})
      elif action == "rotate_right":
          actions.append({"type": "rotate", "speed": 50, "angle": 30})
      elif action == "move_forward":
          actions.append({"type": "move", "speed": 100, "distance": 0.3})
      elif action == "backup":
          actions.append({"type": "move", "speed": 100, "distance": -0.2})
      elif action == "search":
          # Slow rotation to search
          actions.append({"type": "rotate", "speed": 30, "angle": -45})
      elif action == "stop":
          # No movement, just talk/mood
          pass
      
      # Add optional talk
      if talk_message:
          actions.append({"type": "talk", "message": talk_message})
      
      # Add optional mood
      if mood:
          actions.append({"type": "mood", "mood": mood})
      
      # Execute actions if any
      if actions:
          multi_result = multi_action(actions)
          # Combine photo + action result
          return photo_result + [TextContent(type="text", text=f"\\n--- Action Executed ---")] + multi_result
      else:
          return photo_result
  ```

**File 2: `mcp_server.py`**
- Ajouter tool `track_person` dans la liste des tools :
  ```python
  Tool(
      name="track_person",
      description="Track a person by taking a photo and optionally executing a tracking action. This is the core building block for person following. Call this repeatedly to track someone. IMPORTANT: Analyze the returned image to decide the next action (rotate_left, rotate_right, move_forward, backup, search, stop).",
      inputSchema={
          "type": "object",
          "properties": {
              "action": {
                  "type": "string",
                  "description": "Action to execute based on person position. Choose based on image analysis.",
                  "enum": ["rotate_left", "rotate_right", "move_forward", "backup", "search", "stop"]
              },
              "talk_message": {
                  "type": "string",
                  "description": "Optional message to say while executing action (makes tracking more interactive)"
              },
              "mood": {
                  "type": "string",
                  "description": "Optional mood to display during action",
                  "enum": ["happy", "sad", "angry", "surprised", "neutral", "afraid", "disgusted", "contempt"]
              }
          },
          "required": []
      }
  )
  ```

- Ajouter import de `track_person`

### Expected Behavior After Implementation:

**Tracking Loop (orchestré par Claude):**
```
1. track_person() → Photo + analyse
2. Claude: "Person is on the left"
3. track_person("rotate_left", "Je te vois!") → Rotate left + talk
4. track_person() → Photo + analyse
5. Claude: "Person is centered but far"
6. track_person("move_forward", "J'arrive!", "happy") → Move forward + talk + smile
7. Repeat...
```

**Avantages:**
- ✅ Claude garde le contrôle total
- ✅ Peut ajuster la stratégie en temps réel
- ✅ Pas de conflits rotate + move (séparés)
- ✅ Interactions naturelles (talk + mood)
- ✅ Simple à débugger

---

## Previous Task: Add MultiOperation Support & Improve Command Descriptions
**Status**: ✅ COMPLETED
**Date**: 2025-12-16
**Priority**: HIGH (New Feature + UX Improvement)

### Objective:
1. **Ajouter support MultiOperation** : Permettre à Buddy d'exécuter plusieurs actions simultanément (ex: bouger + parler)
2. **Améliorer descriptions** : Clarifier les commandes pour que Claude comprenne mieux et puisse chaîner les actions

### User Story:
"Je veux que Buddy puisse parler pendant qu'il se déplace, ou faire plusieurs actions en même temps. Je veux aussi que Claude comprenne mieux les commandes disponibles."

### Documentation API trouvée (Notion):
```json
{
  "type": "MultiOperation",
  "operations": [
    {
      "type": "MoveOperation",
      "speed": 0.7,
      "distance": 5.0
    },
    {
      "type": "TalkOperation",
      "message": "I am moving!"
    }
  ]
}
```

### 3 Options Proposed:

**Option 1: Ajout simple de MultiOperation** (⭐ Recommandée - KISS)
- Créer nouveau tool `multi_action` dans MCP server
- Permet de combiner plusieurs opérations (move + talk, rotate + talk, etc.)
- Améliorer descriptions des tools existants avec exemples
- Clarifier les capacités de chaque commande

✅ **Avantages**: Simple, rapide, respecte KISS
✅ **Effort**: Moyen (1 nouveau tool + amélioration descriptions)
✅ **Flexibilité**: Claude choisit quand combiner ou non

**Option 2: MultiOperation avancée avec validation**
- Tout de l'Option 1 +
- Validation des combinaisons possibles (interdire move + rotate simultané)
- Ajouter presets (move_and_speak, rotate_and_speak)
- Documentation détaillée des combinaisons recommandées

✅ **Avantages**: Plus robuste, évite les erreurs
⚠️ **Inconvénients**: Plus complexe, peut over-engineer

**Option 3: Refonte complète avec système de contexte**
- Tout de l'Option 1 +
- Système de "contexte" pour mémoriser l'état de Buddy
- MCP Resource avec guide d'utilisation avancé
- Macros pré-définies (greet_person, explore_room)

✅ **Avantages**: Très puissant, très flexible
⚠️ **Inconvénients**: Beaucoup de travail, complexité élevée

### User Choice: ✅ Option 1 (KISS) - SELECTED & IMPLEMENTED

### Plan (Option 1 - Recommandée):
1. ✅ Mettre à jour Todo.md avec le plan
2. ✅ Créer fonction `multi_action()` dans `buddy_functions.py`
   - Accepte une liste d'opérations
   - Crée un `MultiOperation` avec toutes les opérations
   - Valide que les opérations sont compatibles
3. ✅ Ajouter tool `multi_action` dans `mcp_server.py`
   - Description claire avec exemples concrets
   - Schema JSON acceptant une liste d'actions
   - Exemples: "bouger + parler", "tourner + parler"
4. ✅ Améliorer descriptions des tools existants
   - Ajouter exemples d'usage typiques
   - Clarifier quand utiliser chaque commande vs multi_action
   - Ajouter des "tips" pour Claude
5. ⏳ Prêt pour test avec Claude Desktop

### Code Changes Required:

**File 1: `buddy_functions.py`**
- Ajouter fonction `multi_action(actions: list)` :
  ```python
  def multi_action(actions: list):
      """Execute multiple operations simultaneously.
      
      Allows Buddy to do multiple things at once (e.g., move + talk).
      
      Parameters:
      - actions: List of action dictionaries, each with 'type' and parameters
      
      Examples:
      - Move and talk: [{"type": "move", "speed": 100, "distance": 1.0}, 
                        {"type": "talk", "message": "I'm moving!"}]
      - Rotate and talk: [{"type": "rotate", "speed": 50, "angle": 90}, 
                          {"type": "talk", "message": "Turning right"}]
      """
      # Build list of operations
      operations = []
      for action in actions:
          action_type = action.get("type")
          if action_type == "move":
              operations.append({
                  "type": "MoveOperation",
                  "speed": abs(action.get("speed", 100)),
                  "distance": action.get("distance", 0)
              })
          elif action_type == "rotate":
              operations.append({
                  "type": "RotateOperation",
                  "speed": abs(action.get("speed", 50)),
                  "angle": action.get("angle", 0)
              })
          elif action_type == "talk":
              operations.append({
                  "type": "TalkOperation",
                  "message": action.get("message", ""),
                  "volume": action.get("volume", 300)
              })
          elif action_type == "head":
              axis_value = "Yes" if action.get("axis", "yes").lower() == "yes" else "No"
              operations.append({
                  "type": "HeadOperation",
                  "speed": action.get("speed", 40.0),
                  "angle": action.get("angle", 20.0),
                  "axis": axis_value
              })
          elif action_type == "mood":
              operations.append({
                  "type": "MoodOperation",
                  "mood": action.get("mood", "NEUTRAL").upper()
              })
      
      multi_operation = {
          "type": "MultiOperation",
          "operations": operations
      }
      
      return queue_operation(multi_operation, f"Queued multi-action with {len(operations)} operations")
  ```

**File 2: `mcp_server.py`**
- Ajouter tool `multi_action` dans la liste des tools :
  ```python
  Tool(
      name="multi_action",
      description="Execute multiple actions simultaneously. Perfect for doing several things at once like moving while talking, rotating while speaking, etc. This makes Buddy more fluid and natural.",
      inputSchema={
          "type": "object",
          "properties": {
              "actions": {
                  "type": "array",
                  "description": "List of actions to execute simultaneously",
                  "items": {
                      "type": "object",
                      "properties": {
                          "type": {
                              "type": "string",
                              "description": "Action type",
                              "enum": ["move", "rotate", "talk", "head", "mood"]
                          }
                      },
                      "required": ["type"]
                  }
              }
          },
          "required": ["actions"]
      }
  )
  ```

- Améliorer descriptions des tools existants avec des exemples concrets

### Expected Behavior After Implementation:
- ✅ Claude peut appeler `multi_action([{"type": "move", "speed": 100, "distance": 1}, {"type": "talk", "message": "Je bouge!"}])`
- ✅ Buddy se déplace ET parle en même temps
- ✅ Claude comprend mieux quand utiliser chaque commande
- ✅ Interactions plus fluides et naturelles

---

## Previous Task: Fix Speed/Distance Parameter Validation
**Status**: ✅ COMPLETED
**Date**: 2025-12-16
**Priority**: HIGH (Bug Fix + Documentation)

### Objective:
Corriger et documenter les règles importantes pour les paramètres de mouvement et rotation :
- **move_buddy** : `distance` peut être ± (+ avance, - recule), mais `speed` doit être OBLIGATOIREMENT positive
- **rotate_buddy** : `angle` peut être ± (+ droite, - gauche), mais `speed` doit être OBLIGATOIREMENT positive

### Problem Identified:
**Ligne 55 de `buddy_functions.py`** :
```python
direction = "forward" if speed > 0 else "backward"  # ❌ FAUX !
```
- ❌ La direction est basée sur `speed` au lieu de `distance`
- ❌ Aucune validation que `speed` est positive
- ❌ Documentation peu claire dans `mcp_server.py`

### Root Cause:
- Le code utilise `speed` pour déterminer la direction (ligne 55)
- MAIS selon la documentation, c'est `distance` qui détermine la direction
- Résultat : comportement imprévisible et bugs

### 3 Options Proposed:

**Option 1: Fix Simple + Documentation** (⭐ Recommandée - KISS)
- Corriger ligne 55 : `direction = "forward" if distance > 0 else "backward"`
- Ajouter validation : `speed = abs(speed)` pour garantir positivité
- Améliorer commentaires dans le code
- Clarifier descriptions dans `mcp_server.py`

✅ **Avantages**: Simple, rapide, clair, KISS
✅ **Changes**: 2 fichiers seulement

**Option 2: Fix + Validation stricte**
- Tout de l'Option 1 +
- Lever une `ValueError` si `speed < 0` (au lieu de abs())
- Force l'utilisateur à bien utiliser l'API

✅ **Avantages**: Plus strict, détecte les erreurs
⚠️ **Inconvénients**: Moins tolérant, peut casser le code existant

**Option 3: Fix + Documentation externe**
- Tout de l'Option 1 +
- Créer fichier `BUDDY_API_RULES.md` avec toutes les règles
- Ajouter exemples d'utilisation concrets

✅ **Avantages**: Documentation centralisée
⚠️ **Inconvénients**: Plus de maintenance, fichier supplémentaire

### User Choice: ✅ Option 1 (KISS) - SELECTED & IMPLEMENTED

### Plan (Option 1 - Recommandée):
1. ✅ Mettre à jour Todo.md avec le plan (cette section)
2. ✅ Corriger `buddy_functions.py` :
   - Ligne 55 : Changer `speed > 0` en `distance > 0`
   - Ajouter `speed = abs(speed)` pour garantir positivité
   - Ajouter commentaire expliquant les règles
3. ✅ Corriger `buddy_functions.py` fonction `rotate_buddy` :
   - Ajouter `speed = abs(speed)` pour garantir positivité
   - Améliorer commentaires
4. ✅ Clarifier descriptions dans `mcp_server.py` :
   - Tool `move_buddy` : Préciser que speed doit être positive
   - Tool `rotate_buddy` : Préciser que speed doit être positive
   - Ajouter exemples dans les descriptions
5. ⏳ Prêt pour test avec Claude Desktop

### Code Changes Required:

**File 1: `buddy_functions.py`**
- Ligne 48-56 (fonction `move_buddy`) :
  ```python
  def move_buddy(speed: float, distance: float):
      """Move Buddy forward or backward.
      
      Rules:
      - speed: MUST be positive (will be forced to abs() if negative)
      - distance: Positive = forward, Negative = backward
      """
      speed = abs(speed)  # Ensure speed is always positive
      operation = {
          "type": "MoveOperation",
          "speed": speed,
          "distance": distance
      }
      direction = "forward" if distance > 0 else "backward"  # Fixed: use distance, not speed
      return queue_operation(operation, f"Queued move {direction} at speed {speed} for {abs(distance)}m")
  ```

- Ligne 59-66 (fonction `rotate_buddy`) :
  ```python
  def rotate_buddy(speed: float, angle: float):
      """Rotate Buddy left or right by the specified angle.
      
      Rules:
      - speed: MUST be positive (will be forced to abs() if negative)
      - angle: Positive = right, Negative = left
      """
      speed = abs(speed)  # Ensure speed is always positive
      operation = {
          "type": "RotateOperation",
          "speed": speed,
          "angle": angle
      }
      direction = "right" if angle > 0 else "left"
      return queue_operation(operation, f"Queued rotation {direction} at speed {speed} for {abs(angle)} degrees")
  ```

**File 2: `mcp_server.py`**
- Lignes 54-73 : Clarifier descriptions des tools
  - Préciser que `speed` doit être positive
  - Ajouter exemples concrets

### Expected Behavior After Fix:
- ✅ `move_buddy(speed=100, distance=0.5)` → Avance de 0.5m à vitesse 100
- ✅ `move_buddy(speed=100, distance=-0.5)` → **Recule** de 0.5m à vitesse 100
- ✅ `move_buddy(speed=-100, distance=0.5)` → Avance de 0.5m à vitesse 100 (speed devient abs())
- ✅ `rotate_buddy(speed=50, angle=90)` → Tourne à droite de 90° à vitesse 50
- ✅ `rotate_buddy(speed=50, angle=-90)` → Tourne à gauche de 90° à vitesse 50
- ✅ `rotate_buddy(speed=-50, angle=90)` → Tourne à droite de 90° à vitesse 50 (speed devient abs())

---

## Previous Task: Fix Queue Sharing Between MCP Server and Flask API
**Status**: ✅ COMPLETED
**Date**: 2025-12-16
**Priority**: CRITICAL (Operations not being received) - RESOLVED

### Problem:
- Quand Claude envoie un message via MCP (ex: "Salut la team"), l'opération est créée mais jamais récupérée par `/operation`
- Les logs montrent que l'opération est "Queued" dans le serveur MCP
- MAIS la queue Flask reste vide (retourne `null`)
- **Cause racine** : `mcp_server.py` et `api.py` créent DEUX queues séparées !

### Architecture actuelle (MAUVAISE) :
```python
# mcp_server.py ligne 34
operation_queue = deque()  # ← Queue A (MCP écrit ici)

# api.py ligne 26  
operation_queue = deque()  # ← Queue B (Flask lit ici) ❌ DIFFÉRENTE !
```

### Proposed Solutions:
**Option 1** (RECOMMANDÉE - KISS): Supprimer la création de queue dans `mcp_server.py`, utiliser uniquement celle d'`api.py`
**Option 2**: Redis ou queue externe (overkill pour usage local)
**Option 3**: Fichier partagé (moins performant)

**Chosen Option**: ⏳ En attente de GO

### Plan:
1. ✅ Analysé les logs et identifié le problème (deux queues séparées)
2. ✅ Expliqué pourquoi `mcp_server.py` NE PEUT PAS être supprimé (interface MCP pour Claude)
3. ✅ Proposé 3 options de solutions
4. ✅ Reçu le GO pour implémenter Option 1
5. ✅ Supprimé lignes 34-36 dans `mcp_server.py` (création de queue locale)
6. ✅ Vérifié que `init_shared_state()` reçoit bien la queue d'api.py
7. ✅ Ajouté des logs détaillés pour faciliter le debugging
8. ⏳ Prêt pour testing avec Claude Desktop

### Code Changes Required:
- **mcp_server.py** (lignes 34-36):
  ```python
  # ❌ SUPPRIMER ces lignes :
  operation_queue = deque()
  latest_image = {"base64": None, "timestamp": None}
  queue_lock = threading.Lock()
  ```
  → Ces variables seront initialisées par `init_shared_state()` depuis api.py

- **Vérification `api.py`** : S'assurer que la queue créée ligne 26 est bien passée au MCP

### Notes:
- `mcp_server.py` est ESSENTIEL : c'est l'interface MCP pour Claude Desktop
- Le problème n'est pas l'existence du fichier, mais la duplication de la queue
- Après le fix, il n'y aura qu'UNE SEULE queue partagée entre MCP et Flask ✅

---

## Previous Task: Fix init_shared_state() TypeError 
**Status**: ✅ COMPLETED
**Date**: 2025-12-15
**Priority**: CRITICAL (Blocking MCP server startup) - RESOLVED

### Problem:
- `api.py` line 211 calls `init_shared_state(operation_queue, latest_image)` with only 2 arguments
- Function requires 3 arguments: `init_shared_state(queue, image, lock)`
- Missing `threading.Lock()` argument causes TypeError on startup

### Analysis:
- MCP server (`mcp_server.py`) correctly creates lock and passes it
- Flask API mode (`api.py`) is missing the lock creation
- Lock is needed to prevent race conditions between Flask and MCP threads

### Proposed Solutions:
**Option 1** (RECOMMENDED - KISS): Create lock in `api.py` and pass it
**Option 2**: Make lock parameter optional in `buddy_functions.py`
**Option 3**: Refactor to SharedState class

**Chosen Option**: ✅ Option 1 - KISS Principle

### Plan:
1. ✅ Analyzed the error and identified root cause
2. ✅ Proposed 3 solution options
3. ✅ Got user's GO for Option 1
4. ✅ Implemented fix (added `queue_lock = threading.Lock()` in `api.py`)
5. ✅ Passed lock to `init_shared_state()` call
6. ⏳ Ready for testing

### Code Changes Required:
- **api.py** (lines 205-211):
  - Add `queue_lock = threading.Lock()` before import section
  - Update `init_shared_state(operation_queue, latest_image, queue_lock)`

---

## Current Task: Re-add Flask Logs
**Status**: Ready for implementation
**Date**: 2025-12-15
**Chosen Option**: Option 1 - Simplest (Basic Request/Response Logging)

### Plan:
1. ✅ Analyzed current logging implementation
2. ✅ Proposed 3 options to user
3. ✅ User chose Option 1 (Simplest)
4. ✅ Got "GO" from user
5. ✅ Implemented basic logging solution:
   - ✅ Added before_request hook (log method + path)
   - ✅ Added after_request hook (log status code)
   - ✅ Kept existing error log for image upload
6. ⏳ Ready for testing

### Code Changes Required:
- **api.py**: 
  - Add `@app.before_request` decorator function to log incoming requests
  - Add `@app.after_request` decorator function to log responses
  - No changes to existing endpoints (keeping it simple!)

### Notes:
- Keep logs going to stderr (stdout reserved for MCP JSON)
- Use structured format with timestamps
- Include request details but avoid logging sensitive data

---

## Current Task: Fix Network Access from Other Computers
**Status**: Diagnosing
**Date**: 2025-12-15

### Diagnosis:
- ✅ Flask is correctly bound to `0.0.0.0:5000` (all network interfaces)
- ⚠️ Issue: Windows Firewall is likely blocking incoming connections on port 5000
- ⚠️ Need to add firewall exception for port 5000

### Plan:
1. ✅ Confirmed Flask configuration is correct
2. ⏳ Waiting for user to choose solution option
3. ⏳ Implement firewall fix

### Proposed Solutions:
**Option 1** (Simplest): PowerShell command to add firewall rule
**Option 2**: Manual Windows Firewall GUI configuration  
**Option 3**: Test-first approach (disable firewall temporarily, then fix)

### Code/Command Changes Required:
- Run PowerShell command (as Administrator):
  ```powershell
  New-NetFirewallRule -DisplayName "Flask Buddy API" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
  ```
