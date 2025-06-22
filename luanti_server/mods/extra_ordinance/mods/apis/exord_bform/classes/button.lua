local elemname = "button"

---@class bform_button : bform_prototype
---@field label string
---@field on_fields function
local class = setmetatable({}, {__index = exord_bform.prototype})
class.type = elemname

-- button[<X>,<Y>;<W>,<H>;<name>;<label>]

---@return table
function class:render(fs, data, ...)
    table.insert(fs, "button["..self.pos[1]..","..self.pos[2]..";")
    table.insert(fs, self.size[1]..","..self.size[2]..";")
    table.insert(fs, self.id..";"..self.label.."]")
    return fs
end

function class:on_fields(player, formname, fields)
end

---@return bform_button
function class.new(size, label, id, on_fields)
    local ret = {
        id = id or string.sub(minetest.sha1(tostring({})), 1, 8),
        offset = {0, 0},
        size = size or {1, 1},
        label = label or "",
        on_fields = on_fields,
        --
        pos = {0, 0},
        children = {},
        spacing = {0, 0},
    }
    return setmetatable(ret, {__index = class})
end

exord_bform.element.button = class
