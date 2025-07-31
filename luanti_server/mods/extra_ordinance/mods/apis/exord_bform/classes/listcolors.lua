local elemname = "bform_listcolors"

---@class bform_listcolors : bform_prototype
---@field listcolors table
local class = setmetatable({}, {__index = exord_bform.prototype})
class.type = elemname

-- listcolors[<slot_bg_normal>;<slot_bg_hover>;<slot_border>;<tooltip_bgcolor>;<tooltip_fontcolor>]

local defaults = {
    slot_bg_normal = "#808080",
    slot_bg_hover = "#c0c0c0",
    slot_border = "#00000000",
    tooltip_bgcolor = "#6e823c",
    tooltip_fontcolor = "#ffffff",
}

---@return table
function class:render(fs, data, ...)
    table.insert(fs, "listcolors[")
    local first = true
    local root = self:get_root()
    local store
    if root and root.type == "bform" then store = root.store end
    for i, def in ipairs(self.listcolors) do
        local col = def[2] or (store and store[def[1]]) or defaults[def[1]] or "#f0f"
        if store then
            store[def[1]] = col
        end

        if first then
            first = false
        else
            table.insert(fs, ";")
        end
        table.insert(fs, col)
    end
    table.insert(fs, "]")
    return fs
end
---Params are all color strings, nil to not change since last set
---@return bform_listcolors
function class.new(slot_bg_normal, slot_bg_hover, slot_border, tooltip_bgcolor, tooltip_fontcolor)
    local ret = {
        listcolors = {
            {"slot_bg_normal", slot_bg_normal},
            {"slot_bg_hover", slot_bg_hover},
            {"slot_border", slot_border},
            {"tooltip_bgcolor", tooltip_bgcolor},
            {"tooltip_fontcolor",tooltip_fontcolor}
        },
        --
        children = {},
    }
    return setmetatable(ret, {__index = class})
end

exord_bform.element.listcolors = class
