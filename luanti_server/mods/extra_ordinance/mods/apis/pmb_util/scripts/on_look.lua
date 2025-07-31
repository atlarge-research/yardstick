--[[

    -- entity_def
    _on_pointed = function(self, player, itemstack, pointed_thing, dtime, is_new) end,
    -- node_def
    _on_pointed = function(pos, player, itemstack, pointed_thing, dtime, is_new) end,
]]

local pl = {}

local UP = vector.new(0,1,0)
local function get_eyepos(player)
    local eyepos = player:get_pos() + (player:get_eye_offset()*0.1):rotate_around_axis(UP, player:get_look_horizontal())
    eyepos.y = eyepos.y + player:get_properties().eye_height
    return eyepos
end

local function get_tool_range(itemstack)
    local range = itemstack and itemstack:get_definition().range
    if not range then
        range = minetest.registered_items[""].range or 4
    end
    return range
end

local _reg_node = {}
local _reg_entity = {}
-- pmb_util.register_on_node_pointed(function(pos, player, itemstack, pointed_thing, dtime) end)
function pmb_util.register_on_node_pointed(callback) table.insert(_reg_node, callback) end
-- pmb_util.register_on_entity_pointed(function(self, player, itemstack, pointed_thing, dtime) end)
function pmb_util.register_on_entity_pointed(callback) table.insert(_reg_entity, callback) end

local function on_node_point(pos, player, itemstack, pointed_thing, dtime, is_new)
    for i, callback in ipairs(_reg_node) do
        itemstack = callback(pos, player, ItemStack(itemstack), pointed_thing, dtime, is_new) or itemstack
    end
    return itemstack
end

local function on_entity_point(self, player, itemstack, pointed_thing, dtime, is_new)
    for i, callback in ipairs(_reg_node) do
        itemstack = callback(self, player, ItemStack(itemstack), pointed_thing, dtime, is_new) or itemstack
    end
    return itemstack
end

local function on_pointed(itemstack, player, dtime)
    local pi = pl[player]
    local pos = get_eyepos(player)
    local range = get_tool_range(itemstack)
    local ray = minetest.raycast(pos, vector.add(pos, vector.multiply(player:get_look_dir(), range)), true, false)
    for pt in ray do
        if pt.ref and player ~= pt.ref then
            local ent = pt.ref:get_luaentity()
            local is_new = pi.last_pointed ~= ent
            pi.last_pointed = ent
            itemstack = ent and on_entity_point(ent, player, itemstack, pt, dtime, is_new) or itemstack
            if ent and ent._on_pointed then
                return ent._on_pointed(ent, player, itemstack, pt, dtime, is_new)
            end
            return -- any entity stops further tests
        elseif pt.type == "node" then
            local node = minetest.get_node(pt.under)
            local def = minetest.registered_nodes[node.name]
            local is_new = pi.last_pointed ~= tostring(pt.under)
            pi.last_pointed = tostring(pt.under)
            itemstack = on_node_point(pos, player, itemstack, pt, dtime, is_new) or itemstack
            if def._on_pointed then
                return def._on_pointed(pt.under, player, itemstack, pt, dtime, is_new) or itemstack
            end
            return -- any pointable node stops further tests
        end
    end
    pi.last_pointed = nil
    return nil
end


----------------------------------
do return end -- DISABLED FOR NOW.
----------------------------------

minetest.register_globalstep(function(dtime)
    for i, player in ipairs(minetest.get_connected_players()) do
        if not pl[player] then pl[player] = {} end
        local wield_stack = player:get_wielded_item()
        local ret = on_pointed(wield_stack, player, dtime)
        if ret and not wield_stack:equals(ret) then
            player:set_wielded_item(ret)
        end
    end
end)


