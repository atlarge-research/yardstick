# Compatibility Lib
Provides a way to prevent obtuse back compat conditions. The intent is to have backwards compatibility be handled automatically, so you only ever need to use the "most up to date" form of something, and still retain backwards compatibility, never having to write inline code to handle that.

## How
Basically, this API is like a proxy. You use `COMPAT.some_function` and it handles the rest. If something gets deprecated, you just start using this API instead, and you don't have to stop supporting old versions.

Each function figures out how to do the thing you need to do. The most up to date version of a function is used as the name and format of each function under the `COMPAT` namespace. That is, `set_bone_override` was added to deprecate `set_bone_position` so the function to perform this process is called `COMPAT.set_bone_override`.

## Priorities / Goals
- game does not crash on old versions when using new function calls, meaning devs can just use the new functions without having to make "if old then do this else do this" code blocks
- even on old versions, behaviour is mostly the same as on newer versions where reasonable to implement

## Extra Goals
These are less important but do fit the scope.
- provide a way to track mod and game versions numerically, similar to `proto_max`, so that mods know what version some other mod is; basically a `core.get_modpath` but with more options
- provide an equivalence table of "item in game A == item in game B" so that crafting recipes could be made compatible
- provide the same as above, but for texture names

## Out of scope
These are explicitly not within the scope of the project:
- making whole systems compatible with old versions
- predicting results so that the effect of a function call is exactly the same (e.g. trying to reimplement old formspec versions)

## Development guide
All changes should respect the following:
- if an old behaviour does not allow some parameter, prioritise making the game not crash, by just discarding all non-relevant parameters, instead of trying to "emulate" new versions with old behaviour; for example, using `automatic_rotation` to make smooth rotation was an old workaround that is not needed as of 5.9, where bone overrides can have interpolation, and this is something this API should never try to solve.
- document things wherever relevent, but not verbosely
- functions always use the most up to date method name according to the Luanti version this API is designed for; if a new update deprecates a function in this API and there's a new version of that function, the old function is relegated to `deprecated.lua` and the new one added in its place, and it's a developer's responsibility to update their code, else it will keep throwing warnings like Luanti does currently.

## Contributing
I need your help. To correctly research all deprecated functions and parameters is a ridiculously hard thing to do, and it's much better to have people add their knowledge of things they have actually experienced. If you see something missing, add it, make a pull request. Things will be merged very liberally, as this is a "there is only one way to do it" kind of API, not a creative endeavour.

## List of methods / compat features
```lua
COMPAT.set_bone_override(object, bone, overrides)
COMPAT.hud_add(player, def)
```

## Known missing methods
Obviously not exhaustive.
```lua
object:get_bone_position(bone)
--> get_bone_override(bone)
object:get_entity_name()
--> object:get_luaentity().name
player:get_player_velocity()
--> player:get_velocity()
player:add_player_velocity(vel)
--> player:add_velocity(vel)
core.register_on_auth_fail(function(name, ip) end)
--> core.register_on_authplayer(function(name, ip, is_success) end)
minetest.get_perlin(seeddiff, octaves, persistence, spread)
--> minetest.get_perlin(noiseparams)
minetest.get_mapgen_params()
--> minetest.get_mapgen_setting(name)
minetest.set_mapgen_params(MapgenParams)
--> minetest.set_mapgen_setting(name, value, override)
```
