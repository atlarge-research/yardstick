
local UP = vector.new(0,1,0)

local function dist2(v, b)
    return (v.x - b.x)^2 + (v.y - b.y)^2 + (v.z - b.z)^2
end exord_mobpath.dist2 = dist2

local function distn(v, b, n)
    return math.abs(v.x - b.x)^(n or 1) + math.abs(v.y - b.y)^(n or 1) + math.abs(v.z - b.z)^(n or 1)
end exord_mobpath.distn = distn

function exord_mobpath.debug_particle(pos, color, time, vel, size)
    do return end
    minetest.add_particle({
        size = size or 2, pos = pos,
        texture = "blank.png^[noalpha^[colorize:"..(color or "#fff")..":255",
        velocity = vel or vector.new(0, 0, 0),expirationtime = time, glow = 14,
    })
end

local adjacent = {
    vector.new( 1, 0, 0),
    vector.new(-1, 0, 0),
    vector.new( 0, 0, 1),
    vector.new( 0, 0,-1),
    vector.new( 1, 0, 1),
    vector.new(-1, 0,-1),
    vector.new(-1, 0, 1),
    vector.new( 1, 0,-1),
    vector.new( 1, 1, 0),
    vector.new(-1, 1, 0),
    vector.new( 0, 1, 1),
    vector.new( 0, 1,-1),
    vector.new( 1,-1, 0),
    vector.new(-1,-1, 0),
    vector.new( 0,-1, 1),
    vector.new( 0,-1,-1),
}

-- distance as if you have to turn 90deg corners and can't just beeline
local function manhattan_distance(p1, p2)
    return math.abs(p1.x - p2.x) + math.abs(p1.y - p2.y) + math.abs(p1.z - p2.z)
end exord_mobpath.manhattan_distance = manhattan_distance

-- distance or broad estimate cost from target node (usually just manhattan distance)
local function H(p, target)
    return dist2(p, target)
end exord_mobpath.H = H

-- cost of traversal from last node p1 to this node p2
local function G(p1, p2, opt)
    local node = minetest.get_node_or_nil(p2)
    local extra_cost = node and minetest.get_item_group(node.name, "traversible_extra_cost") or 0
    -- avoid walls
    local nodes = minetest.find_nodes_in_area(
        vector.offset(p2, -3, 0,-3),
        vector.offset(p2,  3, 0, 3),
        "group:traversible_extra_cost"
    )
    extra_cost = extra_cost + math.min(4, #nodes)
    return dist2(p2, p1) + extra_cost
end exord_mobpath.G = G

-- return true if you can get from p1 to p2, or false to ignore this path as an option altogether
local function TRAVERSAL(p1, p2)
    local node = minetest.get_node(p2)
    if minetest.get_item_group(node.name, "no_path") > 0 then
        return false
    end
    return true
end exord_mobpath.TRAVERSAL = TRAVERSAL

-- look through the list of OPEN nodes and find the cheapest option so far
local function get_cheapest_node(node_list)
    local cheapest_node = {H=math.huge,G=0}
    local cheapest_node_key = -1
    for k, v in pairs(node_list) do
        if k ~= "__count" and v.H + v.G < cheapest_node.H + cheapest_node.G then
            cheapest_node_key, cheapest_node = k, v
        end
    end
    return cheapest_node_key, cheapest_node
end

-- make a node in the path based on params
local function Node(pos, fromnode, dist_to_target, cost_from_source)
    return {
        pos = pos, from = fromnode, H = dist_to_target, G = cost_from_source,
        F = cost_from_source + dist_to_target,
        hash = pos:to_string()
    }
end

-- make the path less bumpy I guess
function exord_mobpath.smooth_path(path)
    local last_pos = path[1]
    for i, pos in ipairs(path) do
        last_pos, path[i] = path[i], (path[i] + last_pos) / 2
        exord_mobpath.debug_particle(path[i], "#0f0", 2, nil, 2)
    end
    return path
end

-- traverses from the end to the start, to get a list of points in the path
local function collapse_path(start_node, target_node)
    local path = {}
    local last_node = target_node
    local iter = 0
    while last_node ~= start_node and iter < 10000 do
        table.insert(path, last_node.pos)
        last_node = last_node.from
        iter = iter + 1
    end
    return exord_mobpath.smooth_path(path)
end

-- returns true if a_node is the best option so far at getting to the target
-- sorts the best option, which is used when the actual target is not reached
local function BEST_GUESS_SORT(a_node, b_node)
    return (a_node.H < b_node.H)
end

-- This is used to tune the algo. These are the defaults.
-- You get a setmetatable verstion of this when using `exord_mobpath.Options.new(options)`
exord_mobpath.Options = {
    TRAVERSAL = TRAVERSAL,
    BEST_GUESS_SORT = BEST_GUESS_SORT,
    G = G, H = H, adjacent = adjacent
}

function exord_mobpath.Options.new(options)
    options = options or {}
    for k, v in pairs(exord_mobpath.Options) do
        if options[k] == nil then options[k] = v end
    end
    return options
end

exord_mobpath.default_options = exord_mobpath.Options.new({
    -- TRAVERSAL = function(p1, p2) return true end,
    -- BEST_GUESS_SORT = function(a_node, b_node) return (a_node.H < b_node.H) end,
    -- G = function(p1, p2, opt) return 1 end, -- cost from last node, opt is this table / `self`
    -- H = function(p, target) return 1 end, -- distance or heuristic cost from target
    -- host = {}, -- entity or other instance
    -- adjacent = {} -- list of offsets to try to traverse
})

function exord_mobpath.astar(start_pos, target_pos, opt)
    if not opt then opt = exord_mobpath.default_options end
    local OPEN = {}
    local CLOSED = {}
    local start_node = Node(start_pos, nil, H(start_pos, target_pos), 0)
    OPEN[start_node.hash] = start_node
    OPEN.__count = 1
    local iteration_count = 0
    local closest_node_to_target = start_node
    while OPEN.__count > 0 and iteration_count < (opt.max_search or 200) do
        iteration_count = iteration_count + 1
        -- look at the cheapest node first
        local cur_i, current = get_cheapest_node(OPEN)
        if OPEN[current.hash] then
            OPEN[current.hash] = nil
            OPEN.__count = OPEN.__count - 1
        end
        -- we've looked at the current node, so block it from further tests
        CLOSED[current.hash] = current

        -- keep track of the best option so far for getting to the target
        if opt.BEST_GUESS_SORT(current, closest_node_to_target) then
            closest_node_to_target = current
        end

        -- if the algo finds the target from the source, then use that as the target and end this test
        if dist2(current.pos, target_pos) < 1 then
            exord_mobpath.debug_particle(current.pos, "#f00", 1, UP * 100, 1)
            break -- ACTUALLY GIVE BACK THE PATH LIST
        end

        for i, o in ipairs(opt.adjacent) do repeat
            local p2 = current.pos + o
            if not (opt.TRAVERSAL)(p2, current.pos) then
                break
            end
            if CLOSED[p2:to_string()] then break end -- don't test already closed positions
            -- exord_mobpath.debug_particle(current.pos, "#f00", 4, UP*3, 2)
            local new_neighbour_node = Node(
                p2, current, -- position and fromposition
                opt.H(p2, target_pos), -- H absolute dist from target
                current.G + opt.G(current.pos, p2, opt) -- relative distance or cost from start
            )
            local old_node = OPEN[new_neighbour_node.hash]
            if (not old_node) or (new_neighbour_node.F < old_node.F) then
                OPEN[new_neighbour_node.hash] = new_neighbour_node -- overwrite old node if it's closer / cheaper
                exord_mobpath.debug_particle(new_neighbour_node.pos, "#ff0", 2, nil, 1)
                if not old_node then
                    OPEN.__count = OPEN.__count + 1
                end
            end
        until true end
    end

    return collapse_path(start_node, closest_node_to_target)
end
