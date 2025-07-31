
---@param c table (collision_box table)
---@param o table | nil (vector for offset)
---@return table (array of vector positions)
function pmb_util.collision_box_to_vertex_list(c, o)
    if o == nil then o = vector.new(0,0,0) end
    local list = {}
    -- back left
    table.insert(list, vector.new(c[1]+o.x, c[5]+o.y, c[3]+o.z))
    table.insert(list, vector.new(c[1]+o.x, c[2]+o.y, c[3]+o.z))
    -- front left
    table.insert(list, vector.new(c[1]+o.x, c[5]+o.y, c[6]+o.z))
    table.insert(list, vector.new(c[1]+o.x, c[2]+o.y, c[6]+o.z))
    -- front right
    table.insert(list, vector.new(c[4]+o.x, c[5]+o.y, c[6]+o.z))
    table.insert(list, vector.new(c[4]+o.x, c[2]+o.y, c[6]+o.z))
    -- back right
    table.insert(list, vector.new(c[4]+o.x, c[5]+o.y, c[3]+o.z))
    table.insert(list, vector.new(c[4]+o.x, c[2]+o.y, c[3]+o.z))
    return list
end
