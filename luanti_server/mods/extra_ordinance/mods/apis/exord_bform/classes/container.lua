local elemname = "bform_container"

---@class bform_container : bform_prototype
local class = setmetatable({}, {__index = exord_bform.prototype})
class.type = elemname

-- container[<X>,<Y>]

---@return table
function class:render(fs, data, ...)
    table.insert(fs, "container["..self.pos[1]..","..self.pos[2].."]")
    return fs
end

---@return table
function class:render_after(fs, data, ...)
    table.insert(fs, "container_end[]")
    return fs
end

---@return bform_container
function class.new(size, dir, id)
    local ret = {
        id = id,
        offset = {0, 0},
        dir = dir or {1, 0},
        size = size,
        --
        pos = {0, 0},
        children = {},
        spacing = {0, 0},
    }
    return setmetatable(ret, {__index = class})
end

exord_bform.element.container = class
