local elemname = "bform_scroll_container"

---@class bform_scroll_container : bform_prototype
---@field orientation string | "horizontal" | "vertical"
---@field scroll_factor number
local class = setmetatable({}, {__index = exord_bform.prototype})
class.type = elemname

-- scroll_container[<X>,<Y>;<W>,<H>;<scrollbar name>;<orientation>;<scroll factor>]

-- UNDER CONSTRUCTION

---@return table
function class:render(fs, data, ...)
    table.insert(fs, "scroll_container["..self.pos[1]..","..self.pos[2]..";")
    table.insert(fs, self.size[1]..","..self.size[2]..";")
    table.insert(fs, self.orientation..";"..self.scroll_factor.."]")
    return fs
end

---@return table
function class:render_after(fs, data, ...)
    table.insert(fs, "scroll_container_end[]")
    return fs
end

---@return bform_scroll_container
---@param size table | nil
---@param id string | nil
---@param orientation nil | "horizontal" | "vertical"
---@param scroll_factor number | nil
function class.new(size, id, orientation, scroll_factor)
    local ret = {
        id = id or string.sub(minetest.sha1(tostring({})), 1, 8),
        size = size or {0, 0},
        offset = {0, 0},
        orientation = orientation or "vertical",
        scroll_factor = scroll_factor or 0.1,
        dir = {0,1},
        --
        pos = {0, 0},
        children = {},
    }
    return setmetatable(ret, {__index = class})
end

exord_bform.element.scroll_container = class
