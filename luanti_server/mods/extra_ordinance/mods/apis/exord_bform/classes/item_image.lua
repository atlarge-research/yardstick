local elemname = "bform_item_image"

---@class bform_item_image : bform_prototype
---@field itemstring string
---@field middle string
local class = setmetatable({}, {__index = exord_bform.prototype})
class.type = elemname

-- `item_image[<X>,<Y>;<W>,<H>;<item name>]`

---@return table
function class:render(fs, data, ...)
    table.insert(fs, "item_image["..self.pos[1]..","..self.pos[2]..";")
    table.insert(fs, self.size[1]..","..self.size[2]..";")
    table.insert(fs, self.itemstring)
    if self.middle then
        table.insert(fs, ";"..self.middle)
    end
    table.insert(fs, "]")
    table.insert(fs, "container["..self.pos[1]..","..self.pos[2].."]")
    return fs
end

---@return table
function class:render_after(fs, data, ...)
    table.insert(fs, "container_end[]")
    return fs
end

---@return bform_item_image
function class.new(itemstring, size, id)
    local ret = {
        id = id,
        size = size or {0, 0},
        offset = {0, 0},
        itemstring = itemstring or "",
        dir = {0,1},
        --
        pos = {0, 0},
        children = {},
    }
    return setmetatable(ret, {__index = class})
end

---@param value string
function class:set_itemstring(value) return self:_set_value("itemstring", value) end

exord_bform.element.item_image = class
