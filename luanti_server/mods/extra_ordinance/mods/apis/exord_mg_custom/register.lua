local mod_name = minetest.get_current_modname()
local mod_path = minetest.get_modpath(mod_name)

local BUILTIN_GENERATION = true

function exord_mg_custom.sch(name)
    return (mod_path .. "/schematics/" .. name .. ".mts")
end

local mg_name = minetest.get_mapgen_setting("mg_name")
exord_mg_custom.enabled = (mg_name ~= "flat")
if mg_name == "flat" then
    BUILTIN_GENERATION = false
end

exord_mg_custom.registered_generators = {}
exord_mg_custom.generator = nil
exord_mg_custom.generator_name = nil
exord_mg_custom.seed = 12345
exord_mg_custom.generate_everywhere = false

exord_mg_custom.node_cid = {}

function exord_mg_custom.to_cid(node_name)
    if not exord_mg_custom.node_cid[node_name] then
        exord_mg_custom.node_cid[node_name] = minetest.get_content_id(node_name)
    end
    return exord_mg_custom.node_cid[node_name]
end

function exord_mg_custom.register_generator(name, def)
    exord_mg_custom.registered_generators[name] = def
end

function exord_mg_custom.set_generator(name, seed)
    exord_mg_custom.generator = exord_mg_custom.registered_generators[name]
    exord_mg_custom.generator_name = name
    exord_mg_custom.seed = seed or math.random(1,999999999)
end

local ___axes = {"x", "y", "z"}
local function get_axis_overlap(v, r)
    local c = 0
    for _, a in ipairs(___axes) do
        if v[a] == r[a] then c = c + 1 end
    end
    return c
end

-- local avgtime = 0
local data = {}
local after_generated = function(minp, maxp, seed)
    -- local cl = os.clock()
    if not exord_mg_custom.generator then return end
    if not exord_mg_custom.generate_everywhere then
        if (maxp.y < exord_mg_custom.minp.y)
        or (maxp.x < exord_mg_custom.minp.x)
        or (maxp.z < exord_mg_custom.minp.z)
        or (minp.y > exord_mg_custom.maxp.y)
        or (minp.x > exord_mg_custom.maxp.x)
        or (minp.z > exord_mg_custom.maxp.z) then
            return
        end
    end
    local gen = exord_mg_custom.generator
    local w = {}
    w.schems = {}
    w.gen = gen

    -- on_generated
    if BUILTIN_GENERATION then
        w.vm, w.emin, w.emax = minetest.get_mapgen_object("voxelmanip")
        w.area = VoxelArea:new{MinEdge = w.emin, MaxEdge = w.emax}
    end

    -- minetest.log(tostring(minp))

    if not gen.on_position_generated then return end

    local permapdims3d = vector.new(
        maxp.x - minp.x + 1,
        maxp.y - minp.y + 1,
        maxp.z - minp.z + 1)
    for name, p in pairs(gen.nv_maps or {}) do
        -- cl = os.clock()
        if not p.name then p.name = name end
        if not p.seed then p.seed = p.np.seed or 0 end
        if (p.map == nil) or p.np.seed ~= p.seed + exord_mg_custom.seed then
            p.np.seed = p.seed + exord_mg_custom.seed
            p.map = minetest.get_perlin_map(p.np, permapdims3d)
        end
        if not p.data then p.data = {} end
        p.map:get_3d_map_flat(minp, p.data or {})
        -- minetest.log(name.." TOOK: " .. (os.clock()-cl))
    end

    for name, p in pairs(gen.nv_perlin or {}) do
        -- cl = os.clock()
        if not p.name then p.name = name end
        if not p.seed then p.seed = p.np.seed or 0 end
        p.np.seed = p.seed + exord_mg_custom.seed
        if (p.perlin == nil) or p.np.seed ~= p.seed + exord_mg_custom.seed then
            p.perlin = minetest.get_perlin(p.np)
        end
        -- minetest.log(name.." TOOK: " .. (os.clock()-cl))
    end

    if gen.seed ~= exord_mg_custom.seed then
        gen.seed = exord_mg_custom.seed
        if gen.on_initialise then
            gen.on_initialise(gen, exord_mg_custom.seed)
        end
    end

	w.vm:get_data(data)

    local ni = 1
	for z = minp.z, maxp.z do
	for y = minp.y, maxp.y do
		local di = w.area:index(minp.x, y, z)
		for x = minp.x, maxp.x do repeat
            local pos = vector.new(x,y,z)
            if exord_mg_custom.generate_everywhere or not ( -- if it's inside bounds
                ((pos.y < exord_mg_custom.minp.y) or (pos.y > exord_mg_custom.maxp.y))
            or  ((pos.x < exord_mg_custom.minp.x) or (pos.x > exord_mg_custom.maxp.x))
            or  ((pos.z < exord_mg_custom.minp.z) or (pos.z > exord_mg_custom.maxp.z))) then
                gen:on_position_generated(pos, w, data, di, ni)

                if ((get_axis_overlap(pos, exord_mg_custom.minp) > 0)
                or  (get_axis_overlap(pos, exord_mg_custom.maxp) > 0)
                ) then
                    if (pos.y == exord_mg_custom.maxp.y) and exord_mg_custom.generator.barrier_node_top then
                        data[di] = exord_mg_custom.to_cid(exord_mg_custom.generator.barrier_node_top)
                    elseif exord_mg_custom.generator.barrier_node_side then
                        data[di] = exord_mg_custom.to_cid(exord_mg_custom.generator.barrier_node)
                    end
                end
            end
            di = di + 1
            ni = ni + 1
		until true end
	end end

    w.vm:set_data(data)

    for i, def in ipairs(w.schems) do
        -- minetest.log("placing schem : " .. tostring(def.pos))
        minetest.place_schematic_on_vmanip(
            w.vm, def.pos, exord_mg_custom.sch(def.name), def.rot or "random", nil,
            def.force_placement == true, def.flags or "place_center_x, place_center_z")
    end

	w.vm:calc_lighting()
	w.vm:write_to_map()
    minetest.fix_light(minp, maxp)
	-- w.vm:update_liquids()
    -- avgtime = ((avgtime * 9) + (os.clock()-cl)) * 0.1
    -- minetest.log(avgtime .. "  :  " .. (os.clock()-cl))
end


local function test_on_emerge_callback(calls_remaining, callback)
    if calls_remaining == 0 and callback then
        callback()
    end
end

function exord_mg_custom.emerge(callback, minp, maxp)
    minp, maxp = minp or exord_mg_custom.minp, maxp or exord_mg_custom.maxp
    minetest.emerge_area(minp, maxp, function(blockpos, action, calls_remaining, param)
        test_on_emerge_callback(calls_remaining, callback)
    end)
end

function exord_mg_custom.regenerate(minp, maxp, force_emerge, callback)
    if not exord_mg_custom.enabled then return end
    minetest.log("action", "regenerating for mapgen")
    minetest.delete_area(minp, maxp)
    if not force_emerge then return end
    minetest.emerge_area(minp, maxp, function(blockpos, action, calls_remaining, param)
        -- if action == minetest.EMERGE_ERRORED or action == minetest.EMERGE_CANCELLED then end
        test_on_emerge_callback(calls_remaining, callback)
    end)
end

if BUILTIN_GENERATION then
    minetest.register_on_generated(after_generated)
end

-- NOT USED
function exord_mg_custom.generate_by_LVM()
    local k = 0
    local d = 80

    local mi = exord_mg_custom.minc
    local ma = exord_mg_custom.maxc
	for z = mi.z, ma.z do
	for y = mi.y, ma.y do
	for x = mi.x, ma.x do
        minetest.after(k, function()
            after_generated(
                vector.new(d*x, d*y-10, d*z),
                vector.new(d*x+d, d*y+d-10, d*z+d),
                758
            )
        end)
        k = k + 0.05
    end end end
end

if mg_name ~= "flat" then
    minetest.set_mapgen_setting("mg_name", "singlenode", true)
    minetest.set_mapgen_setting("seed", 324, true)
end

function exord_mg_custom.generate_map(generator_name, seed, force_emerge)
    -- core.log("generating map")
    if not exord_mg_custom.enabled then return end
    if generator_name then
        exord_mg_custom.set_generator(generator_name, seed)
    else
        exord_mg_custom.set_generator(nil, seed)
    end
    -- core.log(tostring(exord_mg_custom.minp) .. "   " .. tostring(exord_mg_custom.maxp))
    exord_mg_custom.regenerate(exord_mg_custom.minp, exord_mg_custom.maxp, force_emerge, function()
        SIGNAL("on_mapgen_finished")
    end)
end
