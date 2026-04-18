# Diff: `code/tools/lcc/src/decl.c`
**Canonical:** `wolfcamql-src` (sha256 `daa048df0023...`, 32477 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `openarena-gamecode`  — sha256 `f904f0234d77...`, 32601 bytes

_Diff stat: +30 / -30 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\src\decl.c	2026-04-16 20:02:25.809415100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\tools\lcc\src\decl.c	2026-04-16 22:48:24.206078500 +0100
@@ -32,7 +32,7 @@
 void program(void) {
 	int n;
 	
-	level = GLOBAL;
+	level_lcc = GLOBAL;
 	for (n = 0; t != EOI; n++)
 		if (kind[t] == CHAR || kind[t] == STATIC
 		|| t == ID || t == '*' || t == '(') {
@@ -61,7 +61,7 @@
 		int *p, tt = t;
 		switch (t) {
 		case AUTO:
-		case REGISTER: if (level <= GLOBAL && cls == 0)
+		case REGISTER: if (level_lcc <= GLOBAL && cls == 0)
 		               	error("invalid use of `%k'\n", t);
 		               p = &cls;  t = gettok();      break;
 		case STATIC: case EXTERN:
@@ -151,7 +151,7 @@
 		Coordinate pos;
 		id = NULL;
 		pos = src;
-		if (level == GLOBAL) {
+		if (level_lcc == GLOBAL) {
 			Symbol *params = NULL;
 			ty1 = dclr(ty, &id, &params, 0);
 			if (params && id && isfunc(ty1)
@@ -177,10 +177,10 @@
 			else if (sclass == TYPEDEF)
 				{
 					Symbol p = lookup(id, identifiers);
-					if (p && p->scope == level)
+					if (p && p->scope == level_lcc)
 						error("redeclaration of `%s'\n", id);
-					p = install(id, &identifiers, level,
-						level < LOCAL ? PERM : FUNC);
+					p = install(id, &identifiers, level_lcc,
+						level_lcc < LOCAL ? PERM : FUNC);
 					p->type = ty1;
 					p->sclass = TYPEDEF;
 					p->src = pos;
@@ -346,7 +346,7 @@
 					Symbol *args;
 					ty = tnode(FUNCTION, ty);
 					enterscope();
-					if (level > PARAM)
+					if (level_lcc > PARAM)
 						enterscope();
 					args = parameters(ty);
 					exitparams(args);
@@ -365,7 +365,7 @@
 		case '(': t = gettok(); { Symbol *args;
 					  ty = tnode(FUNCTION, ty);
 					  enterscope();
-					  if (level > PARAM)
+					  if (level_lcc > PARAM)
 					  	enterscope();
 					  args = parameters(ty);
 					  if (params && *params == NULL)
@@ -471,7 +471,7 @@
 	assert(params);
 	if (params[0] && !params[0]->defined)
 		error("extraneous old-style parameter list\n");
-	if (level > PARAM)
+	if (level_lcc > PARAM)
 		exitscope();
 	exitscope();
 }
@@ -496,11 +496,11 @@
 	}
 
 	p = lookup(id, identifiers);
-	if (p && p->scope == level)
+	if (p && p->scope == level_lcc)
 		error("duplicate declaration for `%s' previously declared at %w\n", id, &p->src);
 
 	else
-		p = install(id, &identifiers, level, FUNC);
+		p = install(id, &identifiers, level_lcc, FUNC);
 	p->sclass = sclass;
 	p->src = *pos;
 	p->type = ty;
@@ -540,7 +540,7 @@
 	else if (*tag && (p = lookup(tag, types)) != NULL
 	&& p->type->op == op) {
 		ty = p->type;
-		if (t == ';' && p->scope < level)
+		if (t == ';' && p->scope < level_lcc)
 			ty = newstruct(op, tag);
 	}
 	else {
@@ -673,7 +673,7 @@
 		callee = newarray(n + 1, sizeof *callee, FUNC);
 		memcpy(callee, caller, (n+1)*sizeof *callee);
 		enterscope();
-		assert(level == PARAM);
+		assert(level_lcc == PARAM);
 		while (kind[t] == STATIC || istypename(t, tsym))
 			decl(dclparam);
 		foreach(identifiers, PARAM, oldparam, callee);
@@ -784,8 +784,8 @@
 		apply(events.exit, cfunc, NULL);
 	walk(NULL, 0, 0);
 	exitscope();
-	assert(level == PARAM);
-	foreach(identifiers, level, checkref, NULL);
+	assert(level_lcc == PARAM);
+	foreach(identifiers, level_lcc, checkref, NULL);
 	if (!IR->wants_callb && isstruct(rty)) {
 		Symbol *a;
 		a = newarray(n + 2, sizeof *a, FUNC);
@@ -839,15 +839,15 @@
 	walk(NULL, 0, 0);
 	cp = code(Blockbeg);
 	enterscope();
-	assert(level >= LOCAL);
-	if (level == LOCAL && events.entry)
+	assert(level_lcc >= LOCAL);
+	if (level_lcc == LOCAL && events.entry)
 		apply(events.entry, cfunc, NULL);
 	definept(NULL);
 	expect('{');
 	autos = registers = NULL;
-	if (level == LOCAL && IR->wants_callb
+	if (level_lcc == LOCAL && IR->wants_callb
 	&& isstruct(freturn(cfunc->type))) {
-		retv = genident(AUTO, ptr(freturn(cfunc->type)), level);
+		retv = genident(AUTO, ptr(freturn(cfunc->type)), level_lcc);
 		retv->defined = 1;
 		retv->ref = 1;
 		registers = append(retv, registers);
@@ -868,7 +868,7 @@
 	while (kind[t] == IF || kind[t] == ID)
 		statement(loop, swp, lev);
 	walk(NULL, 0, 0);
-	foreach(identifiers, level, checkref, NULL);
+	foreach(identifiers, level_lcc, checkref, NULL);
 	{
 		int i = nregs, j;
 		Symbol p;
@@ -881,13 +881,13 @@
 	}
 	if (events.blockexit)
 		apply(events.blockexit, cp->u.block.locals, NULL);
-	cp->u.block.level = level;
+	cp->u.block.level = level_lcc;
 	cp->u.block.identifiers = identifiers;
 	cp->u.block.types = types;
 	code(Blockend)->u.begin = cp;
 	if (reachable(Gen))
 		definept(NULL);
-	if (level > LOCAL) {
+	if (level_lcc > LOCAL) {
 		exitscope();
 		expect('}');
 	}
@@ -912,10 +912,10 @@
 	 || p->scope  >= LOCAL)
 	&& !p->addressed && isscalar(p->type) && p->ref >= 3.0)
 		p->sclass = REGISTER;
-	if (level == GLOBAL && p->sclass == STATIC && !p->defined
+	if (level_lcc == GLOBAL && p->sclass == STATIC && !p->defined
 	&& isfunc(p->type) && p->ref)
 		error("undefined static `%t %s'\n", p->type, p->name);
-	assert(!(level == GLOBAL && p->sclass == STATIC && !p->defined && !isfunc(p->type)));
+	assert(!(level_lcc == GLOBAL && p->sclass == STATIC && !p->defined && !isfunc(p->type)));
 }
 static Symbol dcllocal(int sclass, char *id, Type ty, Coordinate *pos) {
 	Symbol p, q;
@@ -933,8 +933,8 @@
 		sclass = AUTO;
 	}
 	q = lookup(id, identifiers);
-	if ((q && q->scope >= level)
-	||  (q && q->scope == PARAM && level == LOCAL)) {
+	if ((q && q->scope >= level_lcc)
+	||  (q && q->scope == PARAM && level_lcc == LOCAL)) {
 		if (sclass == EXTERN && q->sclass == EXTERN
 		&& eqtype(q->type, ty, 1))
 			ty = compose(ty, q->type);
@@ -942,8 +942,8 @@
 			error("redeclaration of `%s' previously declared at %w\n", q->name, &q->src);
 	}
 
-	assert(level >= LOCAL);
-	p = install(id, &identifiers, level, sclass == STATIC || sclass == EXTERN ? PERM : FUNC);
+	assert(level_lcc >= LOCAL);
+	p = install(id, &identifiers, level_lcc, sclass == STATIC || sclass == EXTERN ? PERM : FUNC);
 	p->type = ty;
 	p->sclass = sclass;
 	p->src = *pos;
@@ -1101,7 +1101,7 @@
 		while (t == ID) {
 			char *id = token;
 			Coordinate s;
-			if (tsym && tsym->scope == level)
+			if (tsym && tsym->scope == level_lcc)
 				error("redeclaration of `%s' previously declared at %w\n",
 					token, &tsym->src);
 			s = src;
@@ -1114,7 +1114,7 @@
 					error("overflow in value for enumeration constant `%s'\n", id);
 				k++;
 			}
-			p = install(id, &identifiers, level,  level < LOCAL ? PERM : FUNC);
+			p = install(id, &identifiers, level_lcc,  level_lcc < LOCAL ? PERM : FUNC);
 			p->src = s;
 			p->type = ty;
 			p->sclass = ENUM;

```
