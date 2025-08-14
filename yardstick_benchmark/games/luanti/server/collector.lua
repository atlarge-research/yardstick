-- Enhanced Yardstick Collector Mod for Luanti Server Performance Monitoring
-- This mod collects performance metrics for benchmarking purposes
-- Writes TSV files for system and application metrics

local last_time = minetest.get_us_time()
local tick_count = 0
local start_time = minetest.get_us_time()

-- Create metrics file in mod_storage (where Luanti has write permissions)
local metrics_file = minetest.get_worldpath() .. "/mod_storage/tick_metrics.tsv"
local player_file = minetest.get_worldpath() .. "/mod_storage/player_metrics.tsv"
local interaction_file = minetest.get_worldpath() .. "/mod_storage/interaction_metrics.tsv"

-- Initialize metrics files
local function init_metrics()
    -- Create mod_storage directory if it doesn't exist
    minetest.mkdir(minetest.get_worldpath() .. "/mod_storage")
    
    -- Initialize tick metrics file
    local file = io.open(metrics_file, "w")
    if file then
        file:write("timestamp_s\ttick_duration_ms\ttick_count\tplayers_online\n")
        file:close()
        minetest.log("action", "YARDSTICK: Initialized tick metrics file: " .. metrics_file)
    else
        minetest.log("error", "YARDSTICK: Failed to create tick metrics file: " .. metrics_file)
    end
    
    -- Initialize player metrics file
    local pfile = io.open(player_file, "w")
    if pfile then
        pfile:write("timestamp_s\tevent_type\tplayer_name\ttotal_players\n")
        pfile:close()
        minetest.log("action", "YARDSTICK: Initialized player metrics file: " .. player_file)
    else
        minetest.log("error", "YARDSTICK: Failed to create player metrics file: " .. player_file)
    end
    
    -- Initialize interaction metrics file
    local ifile = io.open(interaction_file, "w")
    if ifile then
        ifile:write("uuid\tphase\ttimestamp_s\ttick_count\tplayers_online\n")
        ifile:close()
        minetest.log("action", "YARDSTICK: Initialized interaction metrics file: " .. interaction_file)
    else
        minetest.log("error", "YARDSTICK: Failed to create interaction metrics file: " .. interaction_file)
    end
end

-- Record tick performance
minetest.register_globalstep(function(dtime)
    local now = minetest.get_us_time()
    local duration_us = now - last_time
    last_time = now
    tick_count = tick_count + 1
    
    -- Convert to useful units
    local timestamp_s = now / 1e6  -- seconds since epoch
    local duration_ms = duration_us / 1000  -- milliseconds
    local players_online = #minetest.get_connected_players()
    
    -- Write metrics every tick (for detailed analysis)
    local file = io.open(metrics_file, "a")
    if file then
        file:write(string.format("%.3f\t%.3f\t%d\t%d\n", 
            timestamp_s, duration_ms, tick_count, players_online))
        file:close()
    end
    
    -- Log significant lag events
    if duration_ms > 100 then  -- More than 100ms (should be ~50ms for 20 TPS)
        minetest.log("warning", string.format("YARDSTICK: High tick duration: %.2fms (players: %d)", 
            duration_ms, players_online))
    end
    
    -- Log performance every 100 ticks (roughly every 5 seconds at 20 TPS)
    if tick_count % 100 == 0 then
        local uptime = (now - start_time) / 1000000 -- Convert to seconds
        minetest.log("action", string.format(
            "[YARDSTICK] Tick: %d, Players: %d, Uptime: %.1fs, Step: %.2fms",
            tick_count, players_online, uptime, duration_ms
        ))
    end
end)

-- Track player connections
minetest.register_on_joinplayer(function(player)
    local now = minetest.get_us_time()
    local timestamp_s = now / 1e6
    local player_name = player:get_player_name()
    local total_players = #minetest.get_connected_players()
    
    local file = io.open(player_file, "a")
    if file then
        file:write(string.format("%.3f\tjoin\t%s\t%d\n", 
            timestamp_s, player_name, total_players))
        file:close()
    end
    
    minetest.log("action", string.format("YARDSTICK: Player joined: %s (total: %d)", 
        player_name, total_players))
end)

minetest.register_on_leaveplayer(function(player, timed_out)
    local now = minetest.get_us_time()
    local timestamp_s = now / 1e6
    local player_name = player:get_player_name()
    local total_players = #minetest.get_connected_players() - 1  -- Player hasn't left yet
    
    local file = io.open(player_file, "a")
    if file then
        file:write(string.format("%.3f\tleave\t%s\t%d\n", 
            timestamp_s, player_name, total_players))
        file:close()
    end
    
    local reason = timed_out and "timeout" or "quit"
    minetest.log("action", string.format("YARDSTICK: Player left: %s (%s, total: %d)", 
        player_name, reason, total_players))
end)

-- Track block interactions for benchmarking
local function log_interaction(uuid, phase)
    local now = minetest.get_us_time()
    local timestamp_s = now / 1e6
    local players_online = #minetest.get_connected_players()
    
    local file = io.open(interaction_file, "a")
    if file then
        file:write(string.format("%s\t%s\t%.3f\t%d\t%d\n", 
            uuid, phase, timestamp_s, tick_count, players_online))
        file:close()
    end
end

-- Register interaction tracking (for block placement/digging)
minetest.register_on_placenode(function(pos, newnode, placer, oldnode, itemstack, pointed_thing)
    if placer and placer:is_player() then
        log_interaction("block_place_" .. minetest.pos_to_string(pos), "place")
    end
end)

minetest.register_on_dignode(function(pos, oldnode, digger)
    if digger and digger:is_player() then
        log_interaction("block_dig_" .. minetest.pos_to_string(pos), "dig")
    end
end)

-- Server status command
minetest.register_chatcommand("status", {
    description = "Show server performance status",
    func = function(name, param)
        local current_time = minetest.get_us_time()
        local uptime = (current_time - start_time) / 1000000
        local players_online = #minetest.get_connected_players()
        
        return true, string.format(
            "Server Status - Uptime: %.1fs, Players: %d, Ticks: %d",
            uptime, players_online, tick_count
        )
    end,
})

-- Benchmark command for testing
minetest.register_chatcommand("benchmark", {
    description = "Run a simple benchmark test",
    func = function(name, param)
        local start = minetest.get_us_time()
        
        -- Simulate some work
        local count = 0
        for i = 1, 100000 do
            count = count + i
        end
        
        local duration = (minetest.get_us_time() - start) / 1000
        
        return true, string.format(
            "Benchmark completed in %.2fms (result: %d)",
            duration, count
        )
    end,
})

-- Initialize when mods are loaded
minetest.register_on_mods_loaded(function()
    init_metrics()
    minetest.log("action", "YARDSTICK: Enhanced tick duration collector loaded successfully")
end)

-- Final summary on shutdown
minetest.register_on_shutdown(function()
    local final_time = minetest.get_us_time()
    local total_uptime = (final_time - start_time) / 1000000
    minetest.log("action", string.format("YARDSTICK: Server shutdown after %.1fs, %d ticks total", 
        total_uptime, tick_count))
end)

minetest.log("action", "[YARDSTICK] Enhanced collector mod loaded successfully")
