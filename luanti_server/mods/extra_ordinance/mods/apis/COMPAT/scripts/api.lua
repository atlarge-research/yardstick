local ver = minetest.get_version().proto_max

COMPAT.flags.set_bone_override = ver >= 45
--[[

    COMPAT.set_bone_override(object, "head", {
        position = {
            vec = vector.new(0,1,1),
            -- if false, it's transposed, composed or multiplied for position, rotation or scale
            absolute = true,
            -- interpolates between last and current value over this many seconds
            interpolation = 0.5,
        },
        rotation = {...},
        scale = {...},
    })
]]
---@param object table
---@param bone string
---@param overrides table
function COMPAT.set_bone_override(object, bone, overrides)
    if COMPAT.flags.set_bone_override then
        -- do things normally / according to new function
        return object:set_bone_override(bone, overrides)
    else
        -- discard all but the allowed params for this old function
        local rot = (overrides.rotation or {}).vec
        if rot then
            rot = (rot / 180) * math.pi
        end
        object:set_bone_position(bone, (overrides.position or {}).vec, rot)
    end
end


COMPAT.flags.hud_add_uses_type = ver >= 44
--[[
    
    return COMPAT.hud_add(player, {
        type = "image",
        text = "blank.png",
        position = {x=0.5, y=0.5}
        scale = {x=1, y=1},
    })
]]
---@param player table
---@param def table
---@return integer
function COMPAT.hud_add(player, def)
    if COMPAT.flags.hud_add_uses_type then
        -- old versions use `hud_elem_type` but new is `type`
        def.type, def.hud_elem_type = def.hud_elem_type or def.type, nil
    else
        -- old version should use new `type` and discard the new version
        def.type, def.hud_elem_type = nil, def.type
    end
    return player:hud_add(def)
end
