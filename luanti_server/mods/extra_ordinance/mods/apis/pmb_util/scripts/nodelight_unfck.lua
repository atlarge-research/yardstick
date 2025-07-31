local ew = "#ababac"
local ns = "#d2d1d5"
local bo = "#777776"
function pmb_util.node_light_unfck(texture)
    return {
        texture,
        texture.."^[multiply:"..bo,
        texture.."^[multiply:"..ew,
        texture.."^[multiply:"..ew,
        texture.."^[multiply:"..ns,
        texture.."^[multiply:"..ns,
    }
end

