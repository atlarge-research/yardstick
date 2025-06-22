local elemname = "bform_image"

---@class bform_image : bform_prototype
---@field texture string
---@field middle string
local class = setmetatable({}, {__index = exord_bform.prototype})
class.type = elemname

-- image[<X>,<Y>;<W>,<H>;<texture name>;<middle>]

---@return table
function class:render(fs, data, ...)
    table.insert(fs, "image["..self.pos[1]..","..self.pos[2]..";")
    table.insert(fs, self.size[1]..","..self.size[2]..";")
    table.insert(fs, self.texture)
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

---@return bform_image
function class.new(texture, size, middle, id)
    local ret = {
        id = id,
        size = size or {0, 0},
        offset = {0, 0},
        texture = minetest.formspec_escape(texture or "blank.png"),
        middle = middle and minetest.formspec_escape(middle) or nil,
        dir = {0,1},
        --
        pos = {0, 0},
        children = {},
    }
    return setmetatable(ret, {__index = class})
end

exord_bform.element.image = class
