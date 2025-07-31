-- Luanti Tick Duration Collector for Yardstick Benchmarking
-- Based on Option 1: Minimal Tick Duration Collector

local last_time = minetest.get_us_time()
local tick_count = 0
local start_time = minetest.get_us_time()

-- Create metrics file in mod_storage (where Luanti has write permissions)
local metrics_file = minetest.get_worldpath() .. "/mod_storage/tick_metrics.tsv"
local player_file = minetest.get_worldpath() .. "/mod_storage/player_metrics.tsv"

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

-- Initialize when mods are loaded
minetest.register_on_mods_loaded(function()
    init_metrics()
    minetest.log("action", "YARDSTICK: Tick duration collector loaded successfully")
end)

-- Final summary on shutdown
minetest.register_on_shutdown(function()
    local now = minetest.get_us_time()
    local total_time_s = (now - start_time) / 1e6
    local avg_tps = tick_count / total_time_s
    
    minetest.log("action", string.format("YARDSTICK: Shutdown summary - Ticks: %d, Time: %.1fs, Avg TPS: %.2f", 
        tick_count, total_time_s, avg_tps))
end) 