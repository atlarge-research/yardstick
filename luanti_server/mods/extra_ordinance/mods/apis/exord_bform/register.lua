
---@return bform
function exord_bform.register_form(name, form)
    exord_bform.forms[name] = form
    return form
end

---@return bform | nil | bform_prepend
function exord_bform.get_form(name)
    return exord_bform.forms[name]
end

---@return string
function exord_bform.get_formspec(name, player, forceupdate)
    return exord_bform.forms[name] and exord_bform.forms[name]:get_form(player, forceupdate)
end

---@return bform | bform_prototype | nil
function exord_bform.add_element_to_id(name, id, element)
    local form = exord_bform.forms[name]
    if not form then return end
    local host = exord_bform.prototype.get_element_by_id(form, id)
    if not host then return end
    return exord_bform.prototype.add_child(host, element)
end

---@return self | nil
function exord_bform.show_form(name, player, ...)
    ---@type bform
    local form = exord_bform.forms[name]
    if not form then return end
    return form:show_form(player, ...)
end
