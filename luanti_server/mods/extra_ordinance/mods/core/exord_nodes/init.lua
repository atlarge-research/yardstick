local mod_name = minetest.get_current_modname()
local mod_path = minetest.get_modpath(mod_name)
local S = minetest.get_translator(mod_name)

exord_nodes = {}
exord_nodes.enable_debug_translucent = false

exord_nodes.damage_max = 5
exord_nodes.enable_self_heal = false
exord_nodes.enable_cheap_node_textures = ISDEBUG

local function debug_translucify(def)
    def.tiles = {
        {
            name = "blank.png^[noalpha^[colorize:#fff:255^[opacity:10",
        },
    }
    def.use_texture_alpha = "blend"
    def.drawtype = "glasslike"
end

function exord_nodes.damage_floor(pos, amount)
    pos.y = 1
    local node = minetest.get_node(pos)
    if minetest.get_item_group(node.name, "destructible") <= 0 then return end
    local dmg = minetest.get_item_group(node.name, "damaged")
    local new_dmg = math.ceil(math.min(exord_nodes.damage_max, math.max(0, dmg + amount)))
    local ndef = minetest.registered_nodes[node.name]
    if new_dmg == 0 then
        node.name = ndef._undamaged_node
    else
        node.name = ndef._undamaged_node .. "_" .. new_dmg
        if exord_nodes.enable_self_heal then
            minetest.get_node_timer(pos):start(2)
        end
    end
    minetest.set_node(pos, node)
end

local function damage_node(pos, amount, no_op)
    local node = minetest.get_node(pos)
    if minetest.get_item_group(node.name, "destructible") <= 0 then return end
    local dmg = minetest.get_item_group(node.name, "damaged")
    local new_dmg = math.ceil(math.min(exord_nodes.damage_max+1, math.max(0, dmg + amount)))
    local ndef = minetest.registered_nodes[node.name]
    if new_dmg == 0 then
        node.name = ndef._undamaged_node
    elseif new_dmg > exord_nodes.damage_max then
        node.name = "air"
    else
        node.name = ndef._undamaged_node .. "_" .. new_dmg
        if exord_nodes.enable_self_heal then
            minetest.get_node_timer(pos):start(2)
        end
    end
    if not no_op then
        for i = 2, exord_core.map.wall_height do
            pos.y = i
            minetest.set_node(pos, node)
        end
    end
    return node
end

local function heal_node(pos)
    return damage_node(pos, -1)
end

function exord_nodes.damage_node(pos, amount)
    return damage_node(pos, amount)
end

local function darken_tiles(tiles, i)
    if i == 0 then return tiles end
    i = 1 - i / exord_nodes.damage_max
    i = i * 0.5 + 0.4
    i = math.floor(i * 15)
    for k = 1, #tiles do
        tiles[k].color = "#" .. string.format("%x%x%x", i, i, i)
    end
    return tiles
end

local function register_damaged(_name, _def)
    for i = 0, exord_nodes.damage_max do
        local def = table.copy(_def)
        def._undamaged_node = _name
        local name = _name .. (i>0 and ("_"..i) or "")
        def.groups = table.copy(def.groups)
        def.tiles = darken_tiles(table.copy(def.tiles), i)
        def.groups.damaged = i
        def.groups.destructible = 1
        def.on_timer = (i>0) and heal_node or nil
        minetest.register_node(name, def)
    end
end

function exord_nodes.register_node(name, _def)
    local def = table.copy(_def)
    def.tiles = {{
        name = def._tile,
        align_style = "world",
        scale = 8,
    }}
    def.groups = def.groups or { game_area = 1, }
    if (def.groups.destructible or 0) > 0 then
        register_damaged(name, def)
    else
        minetest.register_node(name, def)
    end

    def = table.copy(_def)
    def.groups = (def.groups and table.copy(def.groups)) or { game_area = 1, }
    def.groups.floor = 0
    def.tiles = {
        -- {
        --     name = "blank.png^[noalpha^[colorize:#020202:255",
        -- },
        {
            name = def._tile .. "^[colorize:#001:200",
            -- name = def._tile .. "^[multiply:#547",
            -- name = "[fill:1x1:0,0:#010101",
            align_style = "world",
            scale = 8,
        },
        {
            name = def._tile,
            align_style = "world",
            scale = 8,
        },
    }
    if exord_nodes.enable_debug_translucent then
        debug_translucify(def)
    end
    if (def.groups.destructible or 0) > 0 then
        register_damaged(name.."_wall", def)
    else
        minetest.register_node(name.."_wall", def)
    end
end


exord_nodes.register_node("exord_nodes:stone", {
    description = S("Stone"),
    groups = { game_area = 1, traversible_extra_cost = 10, solid = 1, destructible = 1, floor = 1, },
    _tile = "polyhaven_rocks.jpg",
})

exord_nodes.register_node("exord_nodes:gravel", {
    description = S("Gravel"),
    groups = { game_area = 1, traversible_extra_cost = 10, solid = 1, destructible = 1, floor = 1, },
    _tile = "polyhaven_gravel.jpg",
})

exord_nodes.register_node("exord_nodes:dirt_gravel", {
    description = S(""),
    groups = { game_area = 1, traversible_extra_cost = 10, solid = 1, destructible = 1, floor = 1, },
    _tile = "polyhaven_dirt_gravel.jpg",
})

exord_nodes.register_node("exord_nodes:dirt_rocks_2", {
    description = S(""),
    groups = { game_area = 1, traversible_extra_cost = 10, solid = 1, destructible = 1, floor = 1, },
    _tile = "polyhaven_dirt_rocks_2.jpg",
})

exord_nodes.register_node("exord_nodes:tan_dirt", {
    description = S(""),
    groups = { game_area = 1, traversible_extra_cost = 10, solid = 1, destructible = 1, floor = 1, },
    _tile = "polyhaven_tan_dirt.jpg",
})

exord_nodes.register_node("exord_nodes:tan_mud_cracked", {
    description = S(""),
    groups = { game_area = 1, traversible_extra_cost = 10, solid = 1, destructible = 1, floor = 1, },
    _tile = "polyhaven_tan_mud_cracked.jpg",
})

exord_nodes.register_node("exord_nodes:tan_mud_blend", {
    description = S(""),
    groups = { game_area = 1, traversible_extra_cost = 10, solid = 1, destructible = 1, floor = 1, },
    _tile = "polyhaven_tan_mud_cracked_blend.jpg",
})

exord_nodes.register_node("exord_nodes:tan_stone", {
    description = S(""),
    groups = { game_area = 1, traversible_extra_cost = 10, solid = 1, destructible = 1, floor = 1, },
    _tile = "polyhaven_tan_rock.jpg",
})

exord_nodes.register_node("exord_nodes:sandstone", {
    description = S(""),
    groups = { game_area = 1, traversible_extra_cost = 10, solid = 1, destructible = 1, floor = 1, },
    _tile = "polyhaven_sandstone.jpg",
})

exord_nodes.register_node("exord_nodes:grass_stone", {
    description = S("Forest Grass"),
    groups = { game_area = 1, traversible_extra_cost = 10, solid = 1, destructible = 1, floor = 1, },
    _tile = "polyhaven_grass_stone_blend.jpg",
})

exord_nodes.register_node("exord_nodes:concrete", {
    description = S("Concrete"),
    groups = { game_area = 1, traversible_extra_cost = 10, solid = 1, destructible = 1, floor = 1, },
    _tile = "polyhaven_concrete.jpg",
})

exord_nodes.register_node("exord_nodes:rocks_lava", {
    description = S("Lava Rocks"),
    groups = {
        game_area = 1, traversible_extra_cost = 10, solid = 1, destructible = 0, floor = 1,
        traversible_floor_extra_cost = 4,
    },
    _tile = "polyhaven_rocks_lava.jpg",
    paramtype = "light",
    light_source = 14,
})

exord_nodes.register_node("exord_nodes:lava", {
    description = S("Lava"),
    groups = {
        game_area = 1, traversible_extra_cost = 10, solid = 1, destructible = 0, floor = 1,
        traversible_floor_extra_cost = 5,
    },
    _tile = "polyhaven_lava.jpg",
    paramtype = "light",
    light_source = 14,
})

function exord_nodes.clamp(v, m, n)
    return math.min(n, math.max(v, m))
end

function exord_nodes.clamp3(v)
    v.x = exord_nodes.clamp(v.x, 0, 15)
    v.y = exord_nodes.clamp(v.y, 0, 15)
    v.z = exord_nodes.clamp(v.z, 0, 15)
    return v
end

function exord_nodes.vec3_to_color(v)
    v = exord_nodes.clamp3(vector.copy(v))
    return exord_nodes.vec3_to_color_or_nil(v)
end

function exord_nodes.vec3_to_color_or_nil(v)
    if (v.x > 15) or (v.y > 15) or (v.z > 15) then return end
    return string.format("%x%x%x", math.floor(v.x), math.floor(v.y), math.floor(v.z))
end

local function get_lava_color(i)
    return exord_nodes.vec3_to_color(vector.new(
        15,
        math.min(15, math.floor((i^5 * 0.002)) * 0.5),
        math.min(15, math.floor((4 - i * 0.2 + (i^2 * 0.1)) + (i^4 * 0.0001) - i*0.4) * 0.7)
    ))
end

for i = 1, 8 do
    minetest.register_node("exord_nodes:lava_glow_"..i, {
        drawtype = "glasslike",
        use_texture_alpha = "blend",
        sunlight_propagates = false,
        groups = { indestructible = 1, traversible_extra_cost = 20, },
        pointable = false,
        tiles = {"blank.png^[noalpha^[colorize:#"..get_lava_color(9-i)..":255^[opacity:"..((10-i)/8)^2 * 80},
        paramtype = "light",
        light_source = 14,
        walkable = i == 1
    })
    -- core.log(i .. " " .. get_lava_color(9-i))
end

minetest.register_node("exord_nodes:barrier_light_block", {
    -- drawtype = "glasslike",
    use_texture_alpha = "clip",
    tiles = {
        -- "blank.png",
        -- "blank.png^[noalpha^[colorize:#000:255^[opacity:200",
        "blank.png",
    },
    sunlight_propagates = false,
    paramtype = "light",
    groups = { indestructible = 1, },
    pointable = false,
})

minetest.register_node("exord_nodes:barrier", {
    drawtype = "airlike",
    tiles = {
        "blank.png",
    },
    use_texture_alpha = "clip",
    sunlight_propagates = true,
    paramtype = "light",
    groups = { indestructible = 1, },
    pointable = false,
})

minetest.register_node("exord_nodes:barrier_black", {
    tiles = {
        "[fill:1x1:0,0:#000",
    },
    groups = { indestructible = 1, },
    pointable = false,
})

minetest.register_node("exord_nodes:barrier_sky", {
    drawtype = "airlike",
    tiles = {
        "blank.png",
    },
    use_texture_alpha = "clip",
    sunlight_propagates = true,
    paramtype = "light",
    groups = { indestructible = 1, },
    pointable = false,
})

minetest.register_node("exord_nodes:invis_light", {
    drawtype = "airlike",
    tiles = {
        "blank.png",
    },
    walkable = false,
    use_texture_alpha = "clip",
    sunlight_propagates = true,
    paramtype = "light",
    light_source = 14,
    groups = { indestructible = 1, },
    pointable = false,
})

if minetest.settings:get_bool("exord_no_env_fx", false) then
    return
end
minetest.register_abm({
    nodenames = {"exord_nodes:barrier_sky"},
    interval = 6.0,
    chance = 100,
    action = function(pos, node, active_object_count, active_object_count_wider)
        local dir = vector.new( -1, -1, 0.5)
        minetest.add_particlespawner({
            amount = 10,
            time = 12,
            vertical = false,
            texpool = {
                {name="[fill:1x1:0,0:#996"},
                {name="[fill:1x1:0,0:#776"},
                {name="[fill:1x1:0,0:#443"},
                {name="[fill:1x1:0,0:#111"},
            },
            alpha_tween = {0, 1},
            -- glow = 14,
            minpos = vector.offset(pos, -2, 0, -2) + (dir * math.random() * 5),
            maxpos = vector.offset(pos,  2, 0,  2) + (dir * math.random() * 5),
            minvel = dir*0.5,
            maxvel = dir,
            minexptime = 12,
            maxexptime = 12,
            size = {
                min = 0.1,
                max = 1,
                bias = 0.2,
            },
        })
    end
})