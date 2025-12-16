# FlaskBuddy Todo List

## Current Task: Fix Queue Sharing Between MCP Server and Flask API
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
