
pmb_util.player = pmb_util.player or {}
local pl = {}

local function check_player(player)
    if not pl[player] then
        pl[player] = {}
    end
end

function pmb_util.get_product(player)
    local product = 1
    for tag, def in pairs(pl[player]) do
        product = product * def.fov
    end
    return (product ~= 1 and product) or 0
end

-- player (objectref), def (table)
function pmb_util.set_fov(player, def)
    check_player(player)
    local sf = pl[player]
    if (sf[def.tag] == nil) or (sf[def.tag].fov ~= def.fov) then
        sf[def.tag] = def
        local fov = pmb_util.get_product(player)
        player:set_fov(fov, true, def.transition_time)
    end
end

function pmb_util.has_fov(player, tag)
    if pl[player] and pl[player][tag] then
        return pl[player][tag]
    end
    return nil
end

-- player(objectref), tag (string)
function pmb_util.unset_fov(player, tag)
    check_player(player)
    local sf = pl[player]
    if sf[tag] ~= nil then
        local def = table.copy(sf[tag])
        sf[tag] = nil
        local fov = pmb_util.get_product(player)
        player:set_fov(fov, true, def.transition_time)
    end
end

--[[
pmb_util.set_fov(player, {
    tag = "pmb_telescope:zoom",
    fov = 0.2,
    transition_time = 0.1,
})
]]--
