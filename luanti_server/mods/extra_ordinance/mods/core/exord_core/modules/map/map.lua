
exord_core.map = {}
exord_core.map.wall_height = 6

function exord_core.debug_particle(pos, color, time, vel, size)
    -- do return end
    minetest.add_particle({
        size = size or 2, pos = pos,
        texture = "blank.png^[noalpha^[colorize:"..(color or "#fff")..":255",
        velocity = vel or vector.new(0, 0, 0),expirationtime = time, glow = 14,
    })
end

function exord_core.map.destroy_column(pos)
    pos = vector.copy(pos)
    local destroyed = false
    for i = 2, exord_core.map.wall_height do
        pos.y = i
        local node = minetest.get_node(pos)
        if minetest.get_item_group(node.name, "destructible") > 0 then
            minetest.set_node(pos, {name="air"})
            destroyed = true
        end
    end
    return destroyed
end

function exord_core.map.damage_column(pos, amount)
    pos = vector.copy(pos)
    local destroyed = false
    pos.y = 2
    local node = minetest.get_node(pos)
    local new_node = exord_nodes.damage_node(pos, amount)
    if new_node and new_node.name ~= node.name then
        destroyed = true
    end
    return destroyed
end

function exord_core.map.damage_radius(pos, radius, amount, floors, sound)
    pos = vector.copy(pos)
    pos.y = 2
    pos.x = math.ceil(pos.x-0.5)
    pos.y = math.ceil(pos.y-0.5)
    pos.z = math.ceil(pos.z-0.5)
    local destroyed = false
    local r = math.ceil(radius)
    for x = -r, r do
        for z = -r, r do
            local p = vector.offset(pos, x, 0, z)
            p.y = pos.y
            local dist2 = exord_core.dist2(pos, p)
            if dist2 < radius^2 then
                destroyed = exord_core.map.damage_column(p, amount) or destroyed
                if floors then
                    exord_nodes.damage_floor(p, 1)
                end
            end
        end
    end
    if destroyed and sound then
        minetest.sound_play("exord_rubble_explosion", {
            pos = pos,
            max_hear_distance = 60,
            gain = 0.5 * exord_core.sound_gain_multiplier * sound,
            pitch = 0.8 + math.random() * 0.6,
        })
    end
    return destroyed
end

function exord_core.map.build_radius(pos, radius, nodename, overwrite)
    pos = vector.copy(pos)
    pos.y = 2
    pos.x = math.ceil(pos.x-0.5)
    pos.y = math.ceil(pos.y-0.5)
    pos.z = math.ceil(pos.z-0.5)
    local destroyed = false
    local r = math.ceil(radius)
    for x = -r, r do
        for z = -r, r do repeat
            local p = vector.offset(pos, x, 0, z)
            local dist2 = exord_core.dist2(pos, p)
            if dist2 > radius^2 then break end

            for y = 2, exord_core.map.wall_height do
                pos.y = y
                p = vector.offset(pos, x, 0, z)
                local n = minetest.get_node(p)
                if n.name == "air"
                or (overwrite and (minetest.get_item_group(n.name, "destructible") > 0)) then
                    minetest.set_node(p, {name = nodename})
                end
            end
        until true end
    end
    return destroyed
end
