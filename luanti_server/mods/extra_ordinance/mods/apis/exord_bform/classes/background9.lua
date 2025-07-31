local elemname = "background9"

---@class bform_background9 : bform_prototype
---@field texture string
---@field auto_clip boolean
---@field middle string
local class = setmetatable({}, {__index = exord_bform.prototype})

-- `background9[<X>,<Y>;<W>,<H>;<texture name>;<auto_clip>;<middle>]`

---@return table
function class:render(fs, data, ...)
    table.insert(fs, "background9["..self.pos[1]..","..self.pos[2]..";")
    table.insert(fs, self.size[1]..","..self.size[2]..";")
    table.insert(fs, self.texture..";"..tostring(self.auto_clip))
    if self.middle then
        table.insert(fs, ";"..self.middle)
    end
    table.insert(fs, "]")
    return fs
end

---@return table
function class:render_after(fs, data, ...)
    return fs
end

---@return bform_background9
---@param size table | nil
---@param texture string
---@param middle string | number
function class.new(size, texture, auto_clip, middle)
    local ret = {
        size = size or {0, 0},
        offset = {0, 0},
        texture = minetest.formspec_escape(texture or "blank.png"),
        middle = middle and minetest.formspec_escape(middle) or nil,
        auto_clip = auto_clip or false,
        dir = {0,1},
        --
        pos = {0, 0},
        children = {},
        type = elemname,
    }
    return setmetatable(ret, {__index = class})
end

exord_bform.element.background9 = class
