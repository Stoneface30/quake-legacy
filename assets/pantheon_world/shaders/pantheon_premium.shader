// PANTHEON premium metal -- id's own model-shader recipe, not invented here.
//
// Verified against the released Q3A shader manual and against id's shipping
// model shaders (weapon_rocketlauncher, weapon_railgun). The three things
// that matter on an MD3:
//
//   * a model has NO lightmap. The manual's substitute for a specular pass is
//     `map $whiteimage`, "used for specular lighting on MD3 models".
//   * `rgbGen lightingDiffuse` is the model lighting term. `rgbGen vertex` is
//     for static map-object MD3s and gives a flat logo here.
//   * `tcGen environment` is computed PER VERTEX and interpolated, so a
//     low-poly extruded word gets blocky sheen. The letterform is built with
//     --bevel-res 6 for that reason.
//
// The sheen currently overpowers the diffuse -- the word reads as polished
// silver rather than as its base metal. Dial `rgbGen wave sin` base down, or
// swap the additive env stage for `blendfunc GL_DST_COLOR GL_ONE`.

textures/pantheon/title
{
	nopicmip
	{
		map textures/pantheon/gold.tga
		rgbGen lightingDiffuse
	}
	{
		map textures/pantheon/env.tga
		blendfunc add
		rgbGen wave sin 0.5 0.15 0 0.3
		tcGen environment
		tcMod scale 0.5 0.5
	}
	{
		map $whiteimage
		blendfunc GL_SRC_ALPHA GL_ONE
		rgbGen lightingDiffuse
		tcGen environment
		alphaGen lightingSpecular
	}
}

// Add this line above the stages for a live shimmer that moves the NORMALS
// without moving the vertices, so the glyph silhouette never distorts:
//     deformVertexes normal 0.15 2
