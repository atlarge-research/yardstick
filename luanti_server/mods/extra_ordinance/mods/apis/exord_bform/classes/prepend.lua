
exord_bform.global_prepend = nil

local elemname = "bform_prepend"

---@class bform_prepend : bform
---@field set_player_prepend function
local class = setmetatable({}, {__index = setmetatable(exord_bform.element.form, {__index = exord_bform.prototype})})
class.type = elemname

---@return string
function class:render(data, ...)
    for k, v in pairs(self.store) do self.store[k] = nil end
    self:apply_offsets()
    local fs = {}
    self:render_children(fs, data, ...)
    return table.concat(fs)
end

---@return string, string
function class:get_hash_elem(player)
    return "", ""
end

---@return boolean
function class:is_auth(player, fields)
    return true
end


function class:set_player_prepend(player)
    player:set_formspec_prepend(self:get_form(player))
end

function class:on_changed(sources)
    for i, player in ipairs(minetest.get_connected_players()) do
        self:set_player_prepend(player)
    end
end

---@param self bform_prepend
---@param children table
---@return bform_prepend
function class:add_children(children)
    for i, child in ipairs(children or {}) do
        self:add_child(child)
    end
    exord_bform.prototype.signal_changes(self)
    exord_bform.prototype.init_children(self)
    return self
end

---@return bform_prepend
function class:new()
    local ret = {
        formname = "global_prepend",
        id = "root",
        children = {},
        send_on_update = true,
        auth_enabled = false,
        changes_acknowledged = false,
        store = {},
    }
    return setmetatable(ret, {__index = class})
end

exord_bform.element.prepend = class
