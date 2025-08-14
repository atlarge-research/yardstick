-- Yardstick Collector Mod for Luanti Server Performance Monitoring
-- This mod collects performance metrics for benchmarking purposes

-- Initialize metrics collection
local metrics = {}
local start_time = minetest.get_us_time()
local player_count = 0

-- Performance counters
local tick_count = 0
local lag_threshold = 100000 -- 100ms in microseconds

-- Register player events
minetest.register_on_joinplayer(function(player)
    player_count = player_count + 1
    minetest.log("action", "[YARDSTICK] Player joined: " .. player:get_player_name() .. " (total: " .. player_count .. ")")
end)

minetest.register_on_leaveplayer(function(player)
    player_count = player_count - 1
    minetest.log("action", "[YARDSTICK] Player left: " .. player:get_player_name() .. " (total: " .. player_count .. ")")
end)

-- Performance monitoring
local last_step_time = minetest.get_us_time()

minetest.register_globalstep(function(dtime)
    tick_count = tick_count + 1
    local current_time = minetest.get_us_time()
    local step_duration = current_time - last_step_time
    
    -- Log performance every 100 ticks (roughly every 10 seconds at 10 steps/sec)
    if tick_count % 100 == 0 then
        local uptime = (current_time - start_time) / 1000000 -- Convert to seconds
        local avg_step_time = step_duration / 1000 -- Convert to milliseconds
        
        minetest.log("action", string.format(
            "[YARDSTICK] Tick: %d, Players: %d, Uptime: %.1fs, Step: %.2fms",
            tick_count, player_count, uptime, avg_step_time
        ))
        
        -- Warn about lag
        if step_duration > lag_threshold then
            minetest.log("warning", string.format(
                "[YARDSTICK] LAG DETECTED: Step took %.2fms (threshold: %.2fms)",
                step_duration / 1000, lag_threshold / 1000
            ))
        end
    end
    
    last_step_time = current_time
end)

-- Server status command
minetest.register_chatcommand("status", {
    description = "Show server performance status",
    func = function(name, param)
        local current_time = minetest.get_us_time()
        local uptime = (current_time - start_time) / 1000000
        
        return true, string.format(
            "Server Status - Uptime: %.1fs, Players: %d, Ticks: %d",
            uptime, player_count, tick_count
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

minetest.log("action", "[YARDSTICK] Collector mod loaded successfully")
