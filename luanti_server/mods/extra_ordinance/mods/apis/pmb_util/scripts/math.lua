
pmb_util.math = {}

local rotationfacedir_filters = {
    function (x, y, z) return  x, y, z end, -- 0
    function (x, y, z) return  z, y,-x end, -- 90
    function (x, y, z) return -z, y,-x end, -- 180
    function (x, y, z) return -z, y, x end, -- 270
}

-- for rotating schematic data etc
function pmb_util.math.rotate_pos_to_facedir(indexpos, face4dir)
    return vector.new(rotationfacedir_filters[face4dir](indexpos.x, indexpos.y, indexpos.z))
end



function pmb_util.math.dist2(p1, p2)
    return (p1.x-p2.x)^2 + (p1.y-p2.y)^2 + (p1.z-p2.z)^2
end
