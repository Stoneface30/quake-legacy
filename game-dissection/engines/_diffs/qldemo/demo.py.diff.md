# Diff: `qldemo/demo.py`
**Canonical:** `demodumper` (sha256 `5754b5453b4e...`, 16949 bytes)

## Variants

### `qldemo-python`  — sha256 `840a05b2ac71...`, 15709 bytes

_Diff stat: +42 / -90 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\demodumper\qldemo\demo.py	2026-04-16 20:02:27.598239300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\qldemo-python\qldemo\demo.py	2026-04-16 20:02:26.532759700 +0100
@@ -9,7 +9,6 @@
 import os
 import re
 import struct
-import sys
 
 # C-Extension wrapping Q3A Huffman Routines
 import huffman
@@ -17,7 +16,7 @@
 
 # Constants and enum maps
 from qldemo.constants import *
-from qldemo.data import (GameState, EntityState, PlayerState,
+from qldemo.data import (GameState, EntityState, PlayerState, 
                          EntityStateNETF, PlayerStateNETF,
                          ServerCommand, Snapshot)
 
@@ -26,55 +25,38 @@
 # Utility Functions
 
 # Classes
-
-
+ 
 class QLDemo:
+    gamestate=GameState()
+    packets=[]
+    snapshots=[]
+    scores=[]
 
-    def __init__(self, demofilename):
+    def __init__(self, filename):
         huffman.init()
-        huffman.open(demofilename)
-        self.demoname = demofilename
-        self.gamestate = GameState()
-        self.gamestate.players = {}
-        self.gamestate.spectators = {}
-        self.chatseqs = set()
-        self.packets = []
-        self.snapshots = []
-        self.scores = []
-        self.chats = []
-        self.error = False
-
-    def get_demoname(self):
-        return self.demoname
+        huffman.open(filename)
 
     def __iter__(self):
         while True:
             seq=huffman.readrawlong()
             length=huffman.readrawlong()
-            r = None
-
             if seq == -1 or length == -1:
                 break
             huffman.fill(length)
             ack = huffman.readlong()
             cmd = huffman.readbyte()
-
-            if cmd == SVC_GAMESTATE:
+            r = None
+            if cmd == SVC_GAMESTATE: 
                 r = self.parse_gamestate()
-            elif cmd == SVC_SERVERCOMMAND:
+            elif cmd == SVC_SERVERCOMMAND: 
                 r = self.parse_servercommand()
             elif cmd == SVC_SNAPSHOT:
-                # not necessary for summary
-                continue
                 r = self.parse_snapshot()
-            if r is None:
-                self.error = True
-                break
-            yield r
-
-    def closefile(self):
-        huffman.close(self.demoname)
-        return
+                if len(self.snapshots) and r.serverTime == self.snapshots[-1].serverTime:
+                    raise StopIteration
+                self.snapshots.append(r)
+            self.packets.append(r)
+            if r: yield r
 
     def parse_gamestate(self):
         ack=huffman.readlong()
@@ -82,7 +64,7 @@
             cmd = huffman.readbyte()
             if cmd == SVC_EOF:
                 break
-            elif cmd == SVC_CONFIGSTRING:
+            elif cmd == SVC_CONFIGSTRING: 
                 self.parse_configstring()
             elif cmd == SVC_BASELINE:
                 self.parse_baseline()
@@ -91,7 +73,6 @@
         return self.gamestate
 
     def parse_configstring(self, data=(None, None)):
-
         i, string = data
         if not i:
             i = huffman.readshort()
@@ -116,17 +97,16 @@
             output = {}
             for x in range(0, len(subfields), 2):
                 output[subfields[x]]=subfields[x+1]
-                #print output[subfields[x]]
             if output['t'] == TEAM_SPECTATOR:
                 dest=self.gamestate.spectators
             else:
                 dest=self.gamestate.players
-        #if i >= CS_SOUNDS and i < CS_SOUNDS+MAX_SOUNDS:
-            #dest=self.gamestate.config
-            #fieldname='sound'+str(i-CS_SOUNDS)
-        #if i >= CS_LOCATIONS and i < CS_LOCATIONS+MAX_LOCATIONS:
-            #dest=self.gamestate.config
-            #fieldname='location{:02d}'.format(i-CS_LOCATIONS)
+        if i >= CS_SOUNDS and i < CS_SOUNDS+MAX_SOUNDS:
+            dest=self.gamestate.config
+            fieldname='sound'+str(i-CS_SOUNDS)
+        if i >= CS_LOCATIONS and i < CS_LOCATIONS+MAX_LOCATIONS:
+            dest=self.gamestate.config
+            fieldname='location{:02d}'.format(i-CS_LOCATIONS)
         dest[fieldname]=output
 
     def parse_baseline(self):
@@ -170,24 +150,19 @@
     def parse_servercommand(self):
         seq = huffman.readlong()
         string = huffman.readstring()
-
+        
         sc=ServerCommand(seq, string)
-        if sc.cmd == "scores_duel":
-            sc = self.parse_duel_scores(sc)
-            self.scores.append(sc.scores)
-        elif sc.cmd == "scores_ctf":
-            sc = self.parse_ctf_scores(sc)
-            self.scores.append(sc.scores)
-        elif sc.cmd == "scores":
-            sc = self.parse_old_scores(sc)
-            self.scores.append(sc.scores)
-        elif sc.cmd == 'cs' or sc.cmd == 'bcs':
+        #if sc.cmd == "scores_duel":
+        #    sc = self.parse_duel_scores(sc)
+        #    self.scores.append(sc.scores)
+        #elif sc.cmd == "scores_ctf":
+        #    sc = self.parse_ctf_scores(sc)
+        #    self.scores.append(sc.scores)
+        #elif sc.cmd == "scores":
+        #    sc = self.parse_old_scores(sc)
+        #    self.scores.append(sc.scores)
+        if sc.cmd == 'cs' or sc.cmd == 'bcs':
             self.update_configstring(sc)
-        elif sc.cmd == "chat":
-            sc = self.parse_chat_event(sc)
-            if sc.chats is not None:
-                self.chats.append(sc.chats)
-            self.chatseqs.add(seq)
         return sc
 
     def update_configstring(self, command):
@@ -196,28 +171,6 @@
         cs = ' '.join(ls[1:]).strip('"')
         self.parse_configstring((cs_num, cs))
 
-
-    def parse_chat_event(self, command):
-        ls=command.string.split()
-        command.chats = None
-        offset = 1
-
-        # offset+0 = clan tag + player name
-        # offset+1 = playername only
-        #num_chat = ls[offset+1]
-
-        # message = clan tag + playername + message
-        message = ' '.join(ls[1:]).strip('"')
-        player = message.split(':', 1)[0].replace(u'\x19', '')
-
-        if command.seq not in self.chatseqs:
-            if command.chats is None:
-                command.chats = {}
-            command.chats['player'] = player
-            command.chats['msg'] = message
-
-        return command
-
     def parse_duel_scores(self, command):
         offset = 1
         ls = command.string.split()
@@ -256,7 +209,7 @@
                 weapon['damage_dealt'] = ls[offset+3]
                 weapon['kills'] = ls[offset+4]
                 command.scores[client_num]['weapon_stats'].append(weapon)
-                offset += 5
+                offset+=5
         return command
 
     def parse_ctf_scores(self, command):
@@ -299,11 +252,11 @@
         command.scores['TEAM_BLUE']['invisibility_time']  = ls[32]
         command.scores['TEAM_BLUE']['flag_time']  = ls[33]
 
-        num_scores = ls[34]
+        num_scores = int(ls[34])
         command.scores['TEAM_RED']['score'] = ls[35]
         command.scores['TEAM_BLUE']['score'] = ls[36]
         offset = 0
-        for client in range(int(num_scores)):
+        for client in range(num_scores):
             client_num = ls[offset+37]
             command.scores[client_num]={}
             command.scores[client_num]['team'] = ls[offset+38]
@@ -324,7 +277,7 @@
             command.scores[client_num]['captures'] = ls[offset+53]
             command.scores[client_num]['perfect'] = ls[offset+54]
             command.scores[client_num]['alive'] = ls[offset+55]
-            offset += 19
+            offset+=19
         return command
 
     def parse_old_scores(self, command):
@@ -333,7 +286,7 @@
         num_scores = int(ls[0])
         command.scores['TEAM_RED'] = ls[1]
         command.scores['TEAM_BLUE'] = ls[2]
-        offset = 3
+        offset=3
         for client in range(num_scores):
             client_num = ls[offset+0]
             command.scores[client_num]={}
@@ -359,9 +312,9 @@
     def parse_snapshot(self):
         new_snap = Snapshot()
         new_snap.serverTime=huffman.readlong()
-        delta_num = huffman.readbyte()
-        new_snap.snapFlags = huffman.readbyte()
-        new_snap.areamaskLen = huffman.readbyte()
+        #delta_num = huffman.readbyte()
+        #new_snap.snapFlags = huffman.readbyte()
+        #new_snap.areamaskLen = huffman.readbyte()
         #for i in range(new_snap.areamaskLen+1):
         #    new_snap.areamask.append(huffman.readbyte())
         #ps = self.parse_playerstate()
@@ -417,4 +370,3 @@
 
         return player
 
-

```
