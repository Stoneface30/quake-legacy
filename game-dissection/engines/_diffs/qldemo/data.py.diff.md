# Diff: `qldemo/data.py`
**Canonical:** `demodumper` (sha256 `4648bed1fd82...`, 12718 bytes)

## Variants

### `qldemo-python`  — sha256 `c267331cef28...`, 12656 bytes

_Diff stat: +3 / -8 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\demodumper\qldemo\data.py	2026-04-16 20:02:27.598239300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\qldemo-python\qldemo\data.py	2026-04-16 20:02:26.531757500 +0100
@@ -26,7 +26,7 @@
 
 #class Scores(FlattenableObject):
 #    def __init__(self, score_string):
-#
+#        
 
 class GameState(FlattenableObject):
     def __init__(self):
@@ -36,7 +36,6 @@
         self.spectators = {}
         self.baselines = {}
         self.scores = {}
-        self.error = False
 
 class Trajectory(FlattenableObject):
   def __init__(self):
@@ -51,7 +50,6 @@
     seq = None
     cmd = None
     string = None
-    error = False
 
     def __init__(self, seq, string):
         self.seq = seq
@@ -168,7 +166,7 @@
 
   def __getitem__(self,index):
     return self.fields[ index ]
-
+    
   def update(self):
     self.player.commandTime = self.fields[ 0 ]
     self.player.origin[ 0 ] = self.fields[ 1 ]
@@ -219,7 +217,6 @@
     self.player.jumppad_ent = self.fields[ 46 ]
     self.player.loopSound = self.fields[ 47 ]
 
-
 class Snapshot(FlattenableObject):
   def __init__(self):
     self.valid = False
@@ -234,8 +231,6 @@
     self.numEntities = 0
     self.parseEntitiesNum = 0
     self.serverCommandNum = 0
-    #self.Error = False
-
 
 class EntityState(FlattenableObject):
     def __init__(self):
@@ -268,7 +263,7 @@
         self.torsoAnim = 0
         self.generic1 = 0
 
-
+  
 
 class EntityStateNETF:
   def __init__(self,entity):

```
