# Diff: `lcc/src/dag.c`
**Canonical:** `quake3-source` (sha256 `077f10274471...`, 22851 bytes)

## Variants

### `q3vm`  — sha256 `e456ae47f210...`, 22875 bytes

_Diff stat: +13 / -12 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\src\dag.c	2026-04-16 20:02:20.081593400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\src\dag.c	2026-04-16 22:48:28.095133400 +0100
@@ -2,9 +2,9 @@
 
 
 #define iscall(op) (generic(op) == CALL \
-	|| IR->mulops_calls \
+	|| (IR->mulops_calls \
 	&& (generic(op)==DIV||generic(op)==MOD||generic(op)==MUL) \
-	&& ( optype(op)==U  || optype(op)==I))
+	&& ( optype(op)==U  || optype(op)==I)))
 static Node forest;
 static struct dag {
 	struct node node;
@@ -102,7 +102,7 @@
 	Node p = NULL, l, r;
 	int op;
 
-	assert(tlab || flab || tlab == 0 && flab == 0);
+	assert(tlab || flab || (tlab == 0 && flab == 0));
 	if (tp == NULL)
 		return NULL;
 	if (tp->node)
@@ -172,8 +172,8 @@
 		      	p = node(op, NULL, NULL, constant(ty, tp->u.v)); } break;
 	case RIGHT: { if (   tp->kids[0] && tp->kids[1]
 			  &&  generic(tp->kids[1]->op) == ASGN
-			  && (generic(tp->kids[0]->op) == INDIR
-			  && tp->kids[0]->kids[0] == tp->kids[1]->kids[0]
+			  && ((generic(tp->kids[0]->op) == INDIR
+			  && tp->kids[0]->kids[0] == tp->kids[1]->kids[0])
 			  || (tp->kids[0]->op == FIELD
 			  &&  tp->kids[0] == tp->kids[1]->kids[0]))) {
 		      	assert(tlab == 0 && flab == 0);
@@ -276,11 +276,11 @@
 				unsigned int fmask = fieldmask(f);
 				unsigned int  mask = fmask<<fieldright(f);
 				Tree q = tp->kids[1];
-				if (q->op == CNST+I && q->u.v.i == 0
-				||  q->op == CNST+U && q->u.v.u == 0)
+				if ((q->op == CNST+I && q->u.v.i == 0)
+				||  (q->op == CNST+U && q->u.v.u == 0))
 					q = bittree(BAND, x, cnsttree(unsignedtype, (unsigned long)~mask));
-				else if (q->op == CNST+I && (q->u.v.i&fmask) == fmask
-				||       q->op == CNST+U && (q->u.v.u&fmask) == fmask)
+				else if ((q->op == CNST+I && (q->u.v.i&fmask) == fmask)
+				||       (q->op == CNST+U && (q->u.v.u&fmask) == fmask))
 					q = bittree(BOR, x, cnsttree(unsignedtype, (unsigned long)mask));
 				else {
 					listnodes(q, 0, 0);
@@ -621,11 +621,11 @@
 	return forest;
 }
 static Node visit(Node p, int listed) {
-	if (p)
+	if (p) {
 		if (p->syms[2])
 			p = tmpnode(p);
-		else if (p->count <= 1 && !iscall(p->op)
-		||       p->count == 0 &&  iscall(p->op)) {
+		else if ((p->count <= 1 && !iscall(p->op))
+		||       (p->count == 0 &&  iscall(p->op))) {
 			p->kids[0] = visit(p->kids[0], 0);
 			p->kids[1] = visit(p->kids[1], 0);
 		}
@@ -654,6 +654,7 @@
 			if (!listed)
 				p = tmpnode(p);
 		};
+	}
 	return p;
 }
 static Node tmpnode(Node p) {

```
