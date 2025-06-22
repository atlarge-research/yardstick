
exord_bform.shown = {}

function exord_bform.on_auth_failed(player, formname, fields)
end

---comment
---@param form bform
---@param player table
---@param fields table
---@return boolean
local function has_probably_quit_form(form, player, fields)
    if fields.quit then
        return true
    end
    local field = fields.key_enter_field
    local elem = form:get_element_by_id(field)
    if elem and elem.close_on_enter then
        return true
    end
    for fieldname, v in pairs(fields) do
        elem = form:get_element_by_id(fieldname)
        if elem and elem.close_on_enter then
            return true
        end
    end
    return false
end

minetest.register_on_player_receive_fields(function(player, formname, fields)
    local fname = formname
    ---@type bform | nil
    local form
    if fname == "" then
        form = exord_bform.get_inventory_form_or_nil(player)
        if form then
            form.is_used_as_fake_inventory = false
        end
        fname = "player_inventory"
    elseif fname == "fakeinv" then
        form = exord_bform.get_inventory_form_or_nil(player)
        if form then
            form.is_used_as_fake_inventory = true
        end
    end
    if not form then form = exord_bform.shown[fname] end
    if not form then form = exord_bform.forms[fname] end
    if not form then return end

    form.is_active = false

    local pli = form.pl and form.pl[player] or {}
    exord_bform.debug(minetest.colorize("#fea", "EXPECTING HASH: ") .. (pli.last_hash or "nil"), "auth")
    exord_bform.debug(minetest.colorize("#fea", "BUT IT IS: ") .. (fields[pli.last_hash or "nil"] or "nil"), "auth")
    for n, v in pairs(fields) do
        exord_bform.debug(minetest.colorize("#fea", " ") .. (n), "auth")
    end

    if not form.auth_enabled then
        exord_bform.debug(minetest.colorize("#2a6", "Auth is DISABLED, allowing fields sent"), "auth")
    elseif form:is_auth(player, fields) then
        exord_bform.debug(minetest.colorize("#2f6", "HAS auth, allowing fields sent"), "auth")
    elseif (not fields.quit) then
        exord_bform.debug(minetest.colorize("#f34", "DOES NOT have auth"), "auth")
        exord_bform.on_auth_failed(player, formname, fields)
        return
    else
        exord_bform.debug(minetest.colorize("#fd2", "DOES NOT have auth") .. ", but is from inventory formspec or closing form", "auth")
        return
    end

    -- hacky solution to show faked inventory forms again when updated
    form.is_active = not has_probably_quit_form(form, player, fields)

    exord_bform.prototype._propagate_event(form, player, fname, fields)
end)
