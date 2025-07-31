
exord_bform.register_form("global_prepend", exord_bform.element.prepend:new()
):register_on_changed(function(self, sources)
    if not self then return end
    if not self.send_on_update then
        exord_bform.debug("don't update PREPEND", "infoevent")
        return end
    for player, def in pairs(exord_bform.pl) do
        exord_bform.debug("updating PREPEND for player " .. player:get_player_name(), "infoevent")
        self:set_player_prepend(player)
    end
end)

function exord_bform.get_inventory_form_or_nil(player)
    local pi = exord_bform.check_player(player)
    return pi.inventory_form
end

function exord_bform.on_changed_inventory_form(form, sources)
    if not form.player then
        core.log("ERROR, no form.player in on_changed_inventory_form")
    end
    exord_bform.update_player_inventory(form.player)
end

---comment
---@param player any
---@param form bform
---@return bform
function exord_bform.set_inventory_form(player, form)
    local pi = exord_bform.check_player(player)
    pi.inventory_form = form
    form.player = player
    form.formname = "fakeinv"
    exord_bform.update_player_inventory(player)
    form:register_on_changed(exord_bform.on_changed_inventory_form)
    return form
end

function exord_bform.update_player_inventory(player)
    local pi = exord_bform.check_player(player)
    if not pi.inventory_form then return end
    local fs = pi.inventory_form:get_form(player, true)
    player:set_inventory_formspec(fs)
    if pi.inventory_form.is_active and pi.inventory_form.is_used_as_fake_inventory then
        pi.inventory_form.is_used_as_fake_inventory = false
        minetest.show_formspec(player:get_player_name(), "fakeinv", fs)
    end
    exord_bform.debug(minetest.colorize("#f46", "  player_inventory update has been set for player"), "auth")
end

exord_bform.register_form("player_inventory", exord_bform.element.form:new())

exord_bform.get_form("player_inventory"):register_on_changed(function(self, sources)
    exord_bform.debug("player inventory detected changes", "changes")
    if not self then return end
    exord_bform.debug("I saw a change in form " .. self.formname .. " from: " .. table.concat(sources, ", "), "changes")
    if not self.send_on_update then
        exord_bform.debug("player_inventory don't send on update", "changes")
        return end
    for player, def in pairs(exord_bform.pl) do
        exord_bform.debug("player_inventory updating for player " .. player:get_player_name(), "changes")
        exord_bform.update_player_inventory(player)
    end
end)


minetest.register_on_joinplayer(function(player, last_login)
    local pi = exord_bform.check_player(player)
    -- update the inventory on join if form `player_inventory` is set
    exord_bform.update_player_inventory(player)
    -- set global prepend if available
    local global_prepend = exord_bform.get_form("global_prepend")
    if global_prepend then global_prepend:set_player_prepend(player) end
end)
