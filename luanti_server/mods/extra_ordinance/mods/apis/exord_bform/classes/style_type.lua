local elemname = "bform_style_type"

---@class bform_style_type : bform_prototype
---@field elemtype string
---@field arglist table
local class = setmetatable({}, {__index = exord_bform.prototype})
class.type = elemname

-- style_type[<selector 1>,<selector 2>,...;<prop1>;<prop2>;...]
-- style_type[label;font_size=*0.8;textcolor=#ddd;font=normal]

---@return table
function class:render(fs, data, ...)
    local arglist = {}
    for k, v in pairs(self.arglist) do
        table.insert(arglist, tostring(k).."="..tostring(v))
    end
    local argstring = table.concat(arglist, ";")
    table.insert(fs, "style_type["..self.elemtype..";"..argstring.."]")
    return fs
end

---@return bform_style_type
function class.new(elemtype, arglist)
    local ret = {
        elemtype = elemtype,
        arglist = arglist or {},
        --
        pos = {0, 0},
        children = {},
        spacing = {0, 0},
    }
    return setmetatable(ret, {__index = class})
end

exord_bform.element.style_type = class
