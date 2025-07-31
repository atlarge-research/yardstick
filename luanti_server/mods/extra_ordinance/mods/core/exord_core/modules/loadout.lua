

exord_core._registered_loadout_options = {}

local _regloads = {}; exord_core._registered_loadout_options = _regloads
local _regloadslots = {}; exord_core._registered_loadouts_by_slot = _regloadslots
local _regdefaults = {}; exord_core._registered_default_loadout_options = _regdefaults
local _reguids = {}; exord_core._registered_loadout_uids = _reguids
local _uid = 0
function exord_core.register_loadout_option(name, def)
    _regloads[name] = def
    def.name = name
    _uid = _uid + 1
    _reguids[_uid] = def
    def.uid = _uid
    if def.slots then
        def.slot_map = {}
        for i, slotnum in ipairs(def.slots) do
            def.slot_map[slotnum] = true
            local list_for_slot = _regloadslots[slotnum]
            if not list_for_slot then
                list_for_slot = {}
                _regloadslots[slotnum] = list_for_slot
                -- only register defaults once
                if not def._is_default then
                    def._is_default = true
                    _regdefaults[slotnum] = def -- track first registered item as a default for now
                end
            end
            table.insert(list_for_slot, def)
        end
    end
end

function exord_core.get_loadout_by_uid(uid)
    return _reguids[uid]
end

function exord_core.get_loadout_option(name)
    return _regloads[name]
end
-- array with defs
function exord_core.get_loadouts_for_slot(slot)
    return _regloadslots[slot] or {}
end

function exord_core.equip_loadout_option(player, name, slot)
    local def = _regloads[name]
    if not def then return end
    local inv = player:get_inventory()
    inv:set_stack("main", slot or def.slots[1] or 1, ItemStack(def.item))
end

function exord_core.loadout_use(player, slot, pointed_thing)
    local inv = player:get_inventory()
    local stack = inv:get_stack("main", slot)
    if stack:get_count() <= 0 then return end
    local idef = stack:get_definition()
    if not idef.on_use then return end
    local new_stack = idef.on_use(stack, player, pointed_thing)
    if new_stack ~= nil then
        inv:set_stack("main", slot, new_stack)
    end
end

function exord_core.get_default_loadouts()
    local ret = {}
    for slot, def in pairs(_regdefaults) do
        ret[slot] = def.name
    end
    return ret
end

function exord_core.load_player_loadout(player, pi)
    local meta = player:get_meta()
    local saved = meta:get_string("exord_core_loadouts")
    if saved ~= "" then
        pi.selected_loadouts = minetest.deserialize(saved, true)
    else
        pi.selected_loadouts = exord_core.get_default_loadouts()
    end
end

function exord_core.save_player_loadout(player, pi)
    local meta = player:get_meta()
    meta:set_string("exord_core_loadouts", minetest.serialize(pi.selected_loadouts))
end

function exord_core.player_loadout_check(player, pi)
    if not pi.selected_loadouts then
        exord_core.load_player_loadout(player, pi)
    end
end

function exord_core.player_get_selected_loadout_def(player, slot, pi)
    if not pi then pi = exord_core.check_player(player) end
    local name = pi.selected_loadouts[slot]
    return name and _regloads[name] or nil
end

function exord_core.player_get_selected_loadout(player, slot, pi)
    if not pi then pi = exord_core.check_player(player) end
    return pi.selected_loadouts[slot]
end

function exord_core.player_select_loadout(player, slot, loadout_name, pi, override)
    if not pi then pi = exord_core.check_player(player) end
    local def = exord_core.get_loadout_option(loadout_name)
    if not def then return end
    local can_select = override or def.slot_map[slot]
    if not can_select then return end
    pi.selected_loadouts[slot] = def.name
    local id = "selected_loadout:"..slot
    local form = exord_bform.get_inventory_form_or_nil(player)
    local elem = form and form:get_element_by_id(id)
    if elem and elem.type == "bform_item_image" then
        elem:set_itemstring(def.item)
    end
end

function exord_core.player_apply_selected_loadout(player, pi, force)
    if not pi then pi = exord_core.check_player(player) end
    if not force then
        pi.wants_loadout_refresh = true
        exord_core.save_player_loadout(player, pi)
        return
    else
        pi.wants_loadout_refresh = false
    end
    exord_core.save_player_loadout(player, pi)
    local inv = player:get_inventory()
    for i, stack in pairs(inv:get_list("main")) do
        exord_guns.stop_looped(stack, player, exord_guns.check_player(player))
    end
    exord_guns.stop_all_sounds_for_player(player, 50)
    inv:set_list("main", {})
    for slot, name in pairs(pi.selected_loadouts) do
        exord_core.equip_loadout_option(player, name, slot)
    end
end

function exord_core.apply_all_player_loadout_selections()
    for player, pi in pairs(exord_core.pl) do
        if pi.wants_loadout_refresh then
            exord_core.player_apply_selected_loadout(player, nil, true)
        end
    end
end

LISTEN("on_fplayer_spawned", function(player, ent)
    exord_core.player_apply_selected_loadout(player, nil, true)
end)

exord_core.register_loadout_option("mg70", {
    item = "exord_guns:mg70",
    slots = {1},
    title = "MG70",
})
-- exord_core.register_loadout_option("mtaw_mk3_coaxial", {
--     item = "exord_guns:mtaw_mk3_coaxial",
--     slots = {1},
--     title = "MTAW3CA",
-- })
exord_core.register_loadout_option("similon4b", {
    item = "exord_guns:similon4b",
    slots = {1},
    title = "Similon 4bore",
})
exord_core.register_loadout_option("gl30coaxial", {
    item = "exord_guns:gl80coaxial",
    slots = {1},
    title = "Coaxial Grenade Launcher",
})
exord_core.register_loadout_option("turret", {
    item = "exord_guns:turret",
    slots = {1},
    title = "Turret",
})
exord_core.register_loadout_option("he80", {
    item = "exord_guns:he20",
    slots = {2},
    title = "HE80",
})
exord_core.register_loadout_option("gl20", {
    item = "exord_guns:gl80",
    slots = {2,3},
    title = "MK20",
})
exord_core.register_loadout_option("asm100", {
    item = "exord_guns:asm100",
    slots = {3},
    title = "ASM 100",
})
exord_core.register_loadout_option("mtaw_mk3", {
    item = "exord_guns:mtaw_mk3",
    slots = {2,3},
    title = "MTAW3",
})
exord_core.register_loadout_option("amr30", {
    item = "exord_guns:amr30",
    slots = {3},
    title = "MTAW3",
})
exord_core.register_loadout_option("mining_laser", {
    item = "exord_guns:mining_laser",
    slots = {4},
    title = "Mining Laser",
})
exord_core.register_loadout_option("dodge_wallbreak", {
    item = "exord_guns:dodge_wallbreak",
    slots = {5},
    title = "HMDE",
})
exord_core.register_loadout_option("shockwave", {
    item = "exord_guns:shockwave",
    slots = {5},
    title = "Shockwave Explosion",
})
