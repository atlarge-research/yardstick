local elemname = "bform"

---@class bform : bform_prototype
---@field pl table
---@field send_on_update boolean
---@field auth_enabled boolean
---@field is_active boolean
---@field formname string
---@field version number
---@field hash string
---@field store table -- allows elements to store stuff during creation, gets reset every render
---@field prepend table
---@field changes_acknowledged boolean
---@field on_changed function
local class = setmetatable({}, {__index = exord_bform.prototype})
class.type = elemname

---@return string
function class:render(data, ...)
    for k, v in pairs(self.store) do self.store[k] = nil end
    self:apply_offsets()
    local fs = {}
    table.insert(fs, "formspec_version["..self.version.."]")
    table.insert(fs, "size["..self.size[1]..","..self.size[2].."]")
    table.insert(fs, "no_prepend[]")
    if self.prepend then
        table.insert(fs, table.concat(self.prepend))
    end
     self:render_children(fs, data, ...)
    return table.concat(fs)
end

---@return string, string
function class:get_hash_elem(player)
    if not self.pl[player] then self.pl[player] = {} end
    local hash = string.sub(minetest.sha1(tostring({}) .. tostring(math.random())), 1, 16)
    self.pl[player].last_hash = hash
    local fs = {}
    table.insert(fs, "field[99,99;0,0;"..hash..";hash;hash]")
    table.insert(fs, "field_close_on_enter["..hash..";false]")
    table.insert(fs, "set_focus[nofocus;true]")
    table.insert(fs, "button[99,99;0,0;nofocus; ]")
    table.insert(fs, "field_close_on_enter[nofocus;false]")
    return table.concat(fs), hash
end

---@return string
function class:get_form(player, forceupdate)
    exord_bform.shown[self.formname] = self
    if forceupdate or (self._last_formspec == nil) or (not self.changes_acknowledged) then
        local c = os.clock()
        self._last_formspec = self:render({player=player})
        exord_bform.debug("rendered a formspec and took " .. tostring((os.clock() - c)*1000) .. "ms")
    end
    -- don't store the hash elem in the form, store it for each player instead inside `get_hash_elem`
    local formspec = self._last_formspec
    if self.auth_enabled then
        local hash_fs, hash = self:get_hash_elem(player)
        exord_bform.debug(hash .. " is current hash given", "auth")
        formspec = formspec .. hash_fs
    end
    return formspec
end

---@return bform
function class:show_form(player, forceupdate)
    minetest.show_formspec(player:get_player_name(), self.formname, self:get_form(player, forceupdate))
    return self
end

---@return boolean
function class:is_auth(player, fields)
    if self.pl[player] == nil then return false end
    if self.pl[player].last_hash == nil then return false end
    local hash = self.pl[player].last_hash
    return (fields[hash] ~= nil)
end

---@param self bform
---@param children table
---@return bform
function class:add_children(children)
    for i, child in ipairs(children or {}) do
        self:add_child(child)
    end
    exord_bform.prototype.signal_changes(self)
    exord_bform.prototype.init_children(self)
    return self
end

---@return bform
function class:new(size, version, formname)
    local ret = {
        formname = formname or "no_form_name",
        id = "root",
        size = size or {24, 12},
        version = version or 6,
        children = {},
        hash = "",
        pl = {},
        send_on_update = false,
        auth_enabled = true,
        changes_acknowledged = false,
        store = {},
        id_reg = {},
    }
    return setmetatable(ret, {__index = class})
end

exord_bform.element.form = class
