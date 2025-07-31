local mod_name = minetest.get_current_modname()
local mod_path = minetest.get_modpath(mod_name)
local S = minetest.get_translator(mod_name)

local MAX_WEAR = 65534

exord_core.cooldown = {}


local function clamp(a,min,max)
    return math.min(math.max(a, min),max)
end


-- un-wears a tool and returns wear in seconds
function exord_core.cooldown.wear_tick(itemstack, max_sec, dtime)
    -- instant if 0, also avoids x/0
    if max_sec == 0 then
        itemstack:set_wear(0)
        return itemstack
    end

    local wear = itemstack:get_wear()
    local new_wear = clamp(wear - (MAX_WEAR / max_sec) * dtime, 0, MAX_WEAR)
    itemstack:set_wear(new_wear)
    return itemstack
end


-- returns true if it can be used and is in end of windup state
function exord_core.cooldown.is_ready(itemstack)
    local def = itemstack:get_definition()
    local windup = itemstack:get_meta():get_string("_mode") ~= "complete"
    if (windup or (def and def.windup == 0)) and itemstack:get_wear() == 0 then return true
    else return false end
end


-- sets back to max wear so it can count back up again
function exord_core.cooldown.wear_start(itemstack, mode)
    local meta = itemstack:get_meta()
    if meta:get_string("_mode") ~= mode then
        itemstack:set_wear(MAX_WEAR)
        meta:set_string("_mode", mode)
    end
    return itemstack
end


-- just tests if can use, based on wear
function exord_core.cooldown.can_use(itemstack)
    return itemstack:get_wear() == 0
end


-- returns "windup" or "cooldown" or ""
function exord_core.cooldown.get_mode(itemstack)
    return itemstack:get_meta():get_string("_mode") or ""
end


-- call this when you switch from this to something else
function exord_core.cooldown.on_wield_change_from(itemstack, player)
    local meta = itemstack:get_meta()
    local mode = meta:get_string("_mode")
    meta:set_string("_mode", "")
    if exord_core.cooldown.can_use(itemstack) then
        return itemstack
    end

    if mode == "windup" then
        return exord_core.cooldown.windup_cancel(itemstack, player)
    end
end


function exord_core.cooldown.on_trigger(itemstack, player, trigger_name)
    local def = itemstack:get_definition()
    if def[trigger_name] then
        return def[trigger_name](itemstack, player) or itemstack
    end
    return itemstack
end


function exord_core.cooldown.windup_start(itemstack, player)
    itemstack = ItemStack(itemstack)
    exord_core.cooldown.wear_start(itemstack, "windup")
    return exord_core.cooldown.on_trigger(itemstack, player, "_on_windup_start") or itemstack
end


function exord_core.cooldown.windup_cancel(itemstack, player)
    if exord_core.cooldown.get_mode(itemstack) ~= "windup" then return itemstack end
    itemstack = ItemStack(itemstack)
    itemstack:get_meta():set_string("_mode", "cooldown")
    itemstack = exord_core.cooldown.on_trigger(itemstack, player, "_on_windup_cancelled") or itemstack

    -- only call the complete func if _on_windup_cancelled is not defined
    if itemstack:get_definition()._on_windup_cancelled then return itemstack end
    -- allows to make cooldown happen when cancelling
    return exord_core.cooldown.cooldown_complete(itemstack, player)
end


function exord_core.cooldown.windup_complete(itemstack, player)
    itemstack = ItemStack(itemstack)
    itemstack:get_meta():set_string("_mode", "complete")
    return exord_core.cooldown.on_trigger(itemstack, player, "_on_windup_complete") or itemstack
end


function exord_core.cooldown.cooldown_start(itemstack, player)
    itemstack = ItemStack(itemstack)
    itemstack:get_meta():set_string("_mode", "")
    exord_core.cooldown.wear_start(itemstack, "cooldown")
    return exord_core.cooldown.on_trigger(itemstack, player, "_on_cooldown_start") or itemstack
end


function exord_core.cooldown.cooldown_complete(itemstack, player)
    itemstack = ItemStack(itemstack)
    itemstack:get_meta():set_string("_mode", "")
    itemstack:set_wear(0)
    return exord_core.cooldown.on_trigger(itemstack, player, "_on_cooldown_complete") or itemstack
end


function exord_core.cooldown.custom_start(itemstack, player, dur, tag)
    itemstack = ItemStack(itemstack)
    itemstack:get_meta():set_string("_mode", "custom")
    itemstack:get_meta():set_string("_cdt", tostring(dur or 0.5))
    itemstack:get_meta():set_string("_cdtag", tag or "n")
    itemstack:set_wear(MAX_WEAR)
    return exord_core.cooldown.on_trigger(itemstack, player, "_on_custom_cooldown_start") or itemstack
end


function exord_core.cooldown.custom_complete(itemstack, player)
    itemstack = ItemStack(itemstack)
    itemstack:get_meta():set_string("_mode", "")
    itemstack:get_meta():set_string("_cdt", "")
    itemstack:get_meta():set_string("_cdtag", "")
    itemstack:set_wear(0)
    return exord_core.cooldown.on_trigger(itemstack, player, "_on_custom_cooldown_complete") or itemstack
end

function exord_core.cooldown.cooldown_step(itemstack, player, dtime)
    itemstack = ItemStack(itemstack)
    return exord_core.cooldown.on_trigger(itemstack, player, "_on_cooldown_step") or itemstack
end

function exord_core.cooldown.attempt_to_use(itemstack, player, pointed_thing)
    if exord_core.cooldown.can_use(itemstack) then
        exord_core.cooldown.windup_start(itemstack, player)
    end
end


-- update all items, by going through entire inventory
function exord_core.cooldown.update_all_in_inventory(player, dtime)
    local inv = player:get_inventory()
    for listname, list in pairs(inv:get_lists()) do
        for i, itemstack in ipairs(list) do
            itemstack = ItemStack(itemstack)
            local def = itemstack:get_definition()
            if def and (def._cooldown or def._windup) then
                local mode = itemstack:get_meta():get_string("_mode") or "" --"windup" or "cooldown"

                --> change durability based on time
                if mode == "cooldown" or mode == "windup" or mode == "custom" then
                    local cdt = ((mode == "custom") and tonumber(itemstack:get_meta():get_string("_cdt"))
                    or def["_"..mode] or 0)
                    itemstack = exord_core.cooldown.wear_tick(itemstack, cdt, dtime)
                end

                if mode == "cooldown" then
                    itemstack = exord_core.cooldown.cooldown_step(itemstack, player, dtime)
                end
                -- wear is 0 / full durability so trigger windup or cooldown end triggers
                if itemstack:get_wear() == 0 then
                    if mode == "windup" then
                        itemstack = exord_core.cooldown.windup_complete(itemstack, player)
                    elseif mode == "cooldown" then
                        itemstack = exord_core.cooldown.cooldown_complete(itemstack, player)
                    elseif mode == "custom" then
                        itemstack = exord_core.cooldown.custom_complete(itemstack, player)
                    end
                end

                if not itemstack:equals(list[i]) then
                    inv:set_stack(listname, i, itemstack)
                end
            end
        end
    end
end


minetest.register_globalstep(function(dtime)
    for i, player in ipairs(minetest.get_connected_players()) do
        exord_core.cooldown.update_all_in_inventory(player, dtime)
    end
end)





minetest.register_tool("exord_core:cooldown_debug", {
    description = S("For debug"),
    inventory_image = "pmb_wooden_pickaxe.png^[transformR180",
    groups = { not_in_creative_inventory = 1 },
    on_use = function(itemstack, player, pointed_thing)
        if exord_core.cooldown.can_use(itemstack) then
            return exord_core.cooldown.windup_start(itemstack, player)
        end
    end,
    on_deselect = function(itemstack, player)
        return exord_core.cooldown.on_wield_change_from(itemstack, player)
    end,
    on_step = function(itemstack, player, dtime)
    end,
    _cooldown = 4,
    _windup = 1,
    _on_windup_start = function(itemstack, player)
        minetest.log("windup start")
        return itemstack
    end,
    _on_windup_cancelled = function(itemstack, player)
        minetest.log("windup cancel")
        return exord_core.cooldown.cooldown_start(itemstack, player)
    end,
    _on_windup_complete = function(itemstack, player)
        minetest.log("hit")
        return exord_core.cooldown.cooldown_start(itemstack, player)
    end,
    _on_cooldown_start = function(itemstack, player)
        minetest.log("cooldown")
        return itemstack
    end,
    _on_cooldown_complete = function(itemstack, player)
        minetest.log("ready")
        return itemstack
    end,
})



