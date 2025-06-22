
# Procedural Event Bus
## SIGNAL : LISTEN : CONDITIONAL

These functions are for signalling and listening for event triggers. Basically it's a way of your code being able to tell the whole game what just happened, such as if a player did some action, or some other event happened. Note that this is more for games than for general modding.

This is a global set of functions that do what they say on the tin mostly. The exception is `CONDITIONAL` which is a bit more involved (see below). Signals and listeners mean not only can you sometimes save on constant checks by using one-off events instead, but you can also allow extending, avoid some dependencies, and generally make things more reactive and less constant polling. Instead of checking constantly whether the player has just died and then come back to life, we use `core.register_on_respawnplayer`. This is no different except it is generalised and you can signal whatever thing you want.

## Example Use
```lua
LISTEN("on_player_damage", function(player, damage, source)
    core.chat_send_all(
        "Player "..player:get_player_name()..
        " was hit for "..damage.." HP"
    )
end)

LISTEN("can_player_take_damage", function(player, damage, source)
    if player:get_meta():get_string("invulnerable") == "true" then
        return false
    else
        return true
    end
end)

if CONDITIONAL("can_player_take_damage", player, damage, source) then
    SIGNAL("on_player_damage", player, damage, source)
end
```

## SIGNAL
```lua
SIGNAL(tag, ...)
```

## LISTEN
If any function calls `SIGNAL(tag)`, it will call the function you have passed to `LISTEN(tag, callback)`
```lua
LISTEN(tag, function() end)
```

## CONDITIONAL
If any signal returns `==false`, it will return `false` immediately. Otherwise, if one or more callback returns `true` it returns true, and if nothing gets returned then it returns `false`. 

```lua
local mybool = CONDITIONAL(tag, ...)
```

Example:
```lua
LISTEN("can_be_damaged", function(self)
    if self._invulnerable then
        return false
    else
        return true
    end
end)

[...]

local is_damaged = CONDITIONAL("can_be_damaged", self)
```
This is good for conditions that need to be able to be extended, such as when an object should enter a "sleep" state, or to test if it is allowed to take some action.


## Things you should be aware of
Signals are not good for *all* things; generally you should use them only for things that have an outward effect. That means when you `SIGNAL`, that block of code that contains the `SIGNAL` call doesn't care what happens next. Only the `LISTEN`-er cares. This means signals are one-way. You tell the entire world something happened, and whether someone picks that up and does something is entirely up to circumstance, ***whether or not you currently know there is a listener out there who will pick it up!*** This is not like normal procedural code, where you cause the effects *within* the very block of code you're writing. That said, you *could* create an entire game using nothing but signals. It would just be confusing.

For the sake of consistency it's often best to observe the following rules with signals; signals where you don't care about the effect and you are only broadcasting the event happening at all, should be named `on_`[something happen]`ed`. The thing has already happen**ed** and it's **on** that thing happen**ed**. For `CONDITIONAL`s, it would be `can_`[something happen], or `is_`[something true].

Examples of when it makes sense to use them are:
- `on_gamestate_changed` --> when you change from "waiting for players" to "playing the game", maybe other parts of the game want to know this
- `on_mapgen_finished` --> if you have a set area you're generating, often you want to know when it's done, and callbacks can be just thrown away and use signals instead
- `is_player_ready` --> could be that you are waiting for players to be ready, and you don't care how "ready" is determined
- `on_player_ready` --> same thing, but this time it's when it actually triggers actively; some code has determined the player to be ready and has told you so

In reality, what it will be useful for is up to your circumstances. If you know you need it, use it. Don't try to shove it into some mod or game that doesn't benefit from it.

Another thing to note is that, used in this way you are essentially polluting the global scope of signal names. If you feel the need  to do something like `on_mymod_thing_happened` instead of `on_thing_happened` then you should seriously question what you're doing, because you probably best not be doing it. Signals are more or less the domain of the game they are within. If you make a mod that expects `on_player_damaged` to give you a player, damage number and an object, but then some other mod expects it to give an entity instead of an object, you're gonna have a bad time. That's why signals are intended to be very non-specific to the event, or be game-domain where it doesn't matter. Don't make mods that use signals in silly ways in other words.


## Getting a standalone copy of event bus
It is only recommended for internal use where you know a feature / mod will not need to be accessed externally, but it is possible to get your own copy of the eventbus. This is not really necessary since Lua tables are super fast, but you can do it if you really super duper want to. This is not OOP, it returns a full copy of the functions with their own scope, so it is not memory optimised or anything. Don't make 1,000,000 of them please.

You can do this by getting a copy:
```lua
local signal_copy = SIGNALS.new()
signal_copy.SIGNAL("on_something_happen", 38.2, 4)
```
Or you can insert the functions into an existing table (recommended):
```lua
my_mod = {}
SIGNALS.new(my_mod)
my_mod.SIGNAL("on_something_happen", 38.2, 4)
```
