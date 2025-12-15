# FlaskBuddy Todo List

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
