# WORK IN PROGRESS
Much of this will change before it is releasable, so use at your own risk. It was designed for a specific game (trenchfront) and so is a bit ideosyncratic still until it is made into a more pure API.

# How to use
```lua
-- bounds of the map (caution: setting this to a large number or the whole world will kill your game when it tries to delete it)
exord_mg_custom.minp = vector.new(-1, 0,-1) * 80
exord_mg_custom.maxp = vector.new( 1, 0, 1) * 80
-- to make a generator
exord_mg_custom.register_generator(name, def)
-- to generate the map according to a generator (deletes the map bounds you have defined)
exord_mg_custom.generate_map(generator_name, seed, force_emerge)
--> or to delete and regenerate an area:
exord_mg_custom.regenerate(minp, maxp, force_emerge, callback)
```