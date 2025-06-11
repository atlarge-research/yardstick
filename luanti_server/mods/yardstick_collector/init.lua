-- Yardstick Collector mod for Minetest
-- Provides HTTP metrics for benchmarking

-- Print debug info to console immediately 
print("==========================================")
print("YARDSTICK COLLECTOR MOD INITIALIZING")
print("==========================================")

-- Store server start time
local server_start_time = os.time()

-- Request HTTP API
local http = minetest.request_http_api()

-- Check if HTTP API is available
if not http then
    print("ERROR: HTTP API not available! Check your minetest.conf settings:")
    print("  - secure.enable_security = false")
    print("  - http_enable = true")
    print("  - secure.trusted_mods = yardstick_collector")
    print("  - secure.http_mods = yardstick_collector")
    minetest.log("error", "[yardstick_collector] HTTP API not available")
    return
else
    print("SUCCESS: HTTP API is available")
end

-- Initialize metrics
local metrics = {
    players_count = 0,
    entities_count = 0,
    loaded_blocks = 0,
    mem_usage = 0,
    uptime = 0,
    cpu_usage = 0,
    tps = 0  -- ticks per second (20 is ideal)
}

-- Register HTTP endpoint
local port = tonumber(minetest.settings:get("port")) or 30000
print("Server port: " .. port)

-- Debug settings
local settings_debug = {
    ["secure.enable_security"] = minetest.settings:get("secure.enable_security"),
    ["http_enable"] = minetest.settings:get("http_enable"),
    ["secure.trusted_mods"] = minetest.settings:get("secure.trusted_mods"),
    ["secure.http_mods"] = minetest.settings:get("secure.http_mods"),
    ["load_mod_yardstick_collector"] = minetest.settings:get("load_mod_yardstick_collector")
}

-- Print settings
print("Settings:")
for name, value in pairs(settings_debug) do
    print("  - " .. name .. " = " .. (value or "nil"))
end

-- Update metrics periodically
local function update_metrics()
    -- Count players
    metrics.players_count = #minetest.get_connected_players()
    
    -- Memory usage
    metrics.mem_usage = collectgarbage("count") -- in KB
    
    -- Get uptime
    metrics.uptime = os.difftime(os.time(), server_start_time)
    
    -- Attempt to get loaded blocks
    if minetest.get_mapgen_stats then
        local mapgen_stats = minetest.get_mapgen_stats()
        metrics.loaded_blocks = mapgen_stats.loaded_blocks or 0
    end
    
    -- Entity count (ensure luaentities exists)
    metrics.entities_count = 0
    if minetest.luaentities then
        local count = 0
        for _ in pairs(minetest.luaentities) do
            count = count + 1
        end
        metrics.entities_count = count
    end
    
    -- Schedule next update
    minetest.after(5, update_metrics)  -- Update every 5 seconds
end

-- Handle HTTP requests
minetest.register_on_mods_loaded(function()
    print("REGISTERING METRICS ENDPOINT")
    
    -- Start metrics collection
    update_metrics()
    
    -- Register metrics endpoint
    http.register_endpoint("/metrics", function(request)
        print("RECEIVED METRICS REQUEST FROM: " .. (request.peer or "unknown"))
        
        if request.method ~= "GET" then
            return {status = 405, body = "Method not allowed"}
        end
        
        local response = "# Yardstick Metrics for Minetest/Luanti\n\n"
        
        -- Format metrics
        response = response .. "# HELP players_count Number of connected players\n"
        response = response .. "# TYPE players_count gauge\n"
        response = response .. "players_count " .. metrics.players_count .. "\n\n"
        
        response = response .. "# HELP entities_count Number of active entities\n"
        response = response .. "# TYPE entities_count gauge\n"
        response = response .. "entities_count " .. metrics.entities_count .. "\n\n"
        
        response = response .. "# HELP loaded_blocks Number of loaded map blocks\n"
        response = response .. "# TYPE loaded_blocks gauge\n"
        response = response .. "loaded_blocks " .. metrics.loaded_blocks .. "\n\n"
        
        response = response .. "# HELP mem_usage Memory usage in KB\n"
        response = response .. "# TYPE mem_usage gauge\n"
        response = response .. "mem_usage " .. metrics.mem_usage .. "\n\n"
        
        response = response .. "# HELP uptime Server uptime in seconds\n"
        response = response .. "# TYPE uptime counter\n"
        response = response .. "uptime " .. metrics.uptime .. "\n\n"
        
        response = response .. "# HELP cpu_usage CPU usage percentage\n"
        response = response .. "# TYPE cpu_usage gauge\n"
        response = response .. "cpu_usage " .. metrics.cpu_usage .. "\n\n"
        
        response = response .. "# HELP tps Server ticks per second\n"
        response = response .. "# TYPE tps gauge\n"
        response = response .. "tps " .. metrics.tps .. "\n\n"
        
        print("SENDING METRICS RESPONSE, SIZE: " .. #response)
        return {status = 200, body = response}
    end)
    
    -- Also register a root endpoint for testing
    http.register_endpoint("/", function(request)
        print("RECEIVED ROOT REQUEST FROM: " .. (request.peer or "unknown"))
        return {
            status = 200, 
            body = "Yardstick Collector is running. Access metrics at /metrics"
        }
    end)
    
    print("METRICS ENDPOINT REGISTERED at http://localhost:" .. port .. "/metrics")
    minetest.log("action", "[yardstick_collector] Metrics endpoint registered at http://localhost:" .. port .. "/metrics")
end)

-- Log successful initialization
print("==========================================")
print("YARDSTICK COLLECTOR MOD INITIALIZED")
print("METRICS URL: http://localhost:" .. port .. "/metrics")
print("==========================================")
minetest.log("action", "[yardstick_collector] Mod initialized") 