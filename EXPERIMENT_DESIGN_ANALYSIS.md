# Experimental Design Analysis for Luanti Performance Testing

## Overview

This document analyzes the experimental questions for Luanti performance testing, considering implementation complexity and experimental design given our current walkbot infrastructure.

## Current Infrastructure Capabilities

- **Rust walkbot**: Works perfectly with configurable movement modes (random, circular, static, follow)
- **Python walkbot**: Available as backup/alternative
- **Ansible deployment**: Automated server and workload deployment
- **Monitoring**: Tick rate collection and performance metrics
- **Multi-node support**: Can distribute bots across multiple nodes

## Experimental Questions Analysis

### 1. Player Capacity Testing: "How many players can Luanti support under good conditions (and how does this compare to vanilla Minecraft?)"

**Implementation Complexity: EASY** ⭐⭐⭐⭐⭐

**Why Easy:**

- Builds directly on existing walkbot infrastructure
- Simple scaling experiment (increase bot count until performance degrades)
- Existing monitoring already captures tick rate metrics
- Can reuse existing server deployment automation

**Experimental Design:**

```
Methodology:
1. Start with baseline (1 bot)
2. Incrementally add bots (5, 10, 20, 50, 100, 200, etc.)
3. Monitor server tick rate, memory usage, CPU usage
4. Determine breaking point (when tick rate drops below threshold)
5. Repeat with different bot behaviors to validate

Variables to Control:
- Server hardware (consistent across tests)
- Bot behavior (start with simple random walk)
- World size/complexity (use flat test world)
- Network conditions (local/controlled environment)

Success Metrics:
- Maximum concurrent players before tick rate drops below 19 TPS
- Server resource utilization at capacity
- Bot connectivity stability at high player counts

Comparison with Minecraft:
- Run identical test with Minecraft server
- Same hardware, same bot behavior patterns
- Compare absolute numbers and resource efficiency
```

**Infrastructure Needs:**

- Modify ansible playbooks to support variable bot counts
- Enhance monitoring to track resource usage
- Parallel Minecraft testing setup

### 2. Mod Impact Assessment: "How much impact on performance do these mods have?"

**Implementation Complexity: MEDIUM** ⭐⭐⭐⭐⭐

**Why Medium:**

- Requires multiple server configurations
- Need to isolate individual mod impacts
- Requires careful experimental design to control variables
- May need different workloads to trigger mod-specific behavior

**Experimental Design:**

```
Methodology:
1. Baseline: Vanilla Luanti server (no mods)
2. Single mod impact: Add one mod at a time
3. Cumulative impact: Add mods progressively
4. Full load: All mods together
5. Run identical bot workload for each configuration

Test Configurations:
- Vanilla (no mods)
- Vanilla + weather mod only
- Vanilla + yardstick_collector only
- Vanilla + other individual mods
- All mods combined

Variables to Control:
- Same bot count (use capacity from experiment 1)
- Same bot behavior
- Same world conditions
- Same hardware

Success Metrics:
- Tick rate comparison across configurations
- Memory usage per mod
- CPU usage per mod
- Network overhead per mod
- Bot performance impact
```

**Infrastructure Needs:**

- Multiple server configurations in ansible
- Automated mod enable/disable
- Baseline Minecraft server for comparison

### 3. Network Resilience Testing: "How do games deal with unreliable network conditions?"

**Implementation Complexity: HARD** ⭐⭐⭐⭐⭐

**Why Hard:**

- Requires network simulation/manipulation
- Complex infrastructure setup (traffic shaping)
- May require modifications to bot behavior
- Challenging to create repeatable network conditions

**Experimental Design:**

```
Methodology:
1. Baseline: Perfect network conditions
2. Latency simulation: Add artificial delays (50ms, 100ms, 200ms, 500ms)
3. Packet loss: Simulate packet loss (1%, 5%, 10%, 20%)
4. Bandwidth limiting: Reduce available bandwidth
5. Jitter simulation: Variable latency
6. Complete disconnection scenarios

Network Conditions to Test:
- Perfect (baseline)
- High latency (gaming over satellite)
- Packet loss (poor WiFi)
- Bandwidth limitation (mobile data)
- Intermittent connectivity
- Sudden disconnection/reconnection

Variables to Control:
- Same bot count
- Same server configuration
- Same bot behavior initially

Success Metrics:
- Bot connection stability
- Game state synchronization accuracy
- Server tick rate under network stress
- Recovery time after network issues
- Player experience degradation points
```

**Infrastructure Needs:**

- Network emulation tools (tc, netem, or dedicated tools)
- Enhanced bot monitoring for connection state
- Packet capture capabilities
- Network condition automation

### 4. Player Behavior Impact: "How much of an impact does player behavior have? (all players together in one place vs. far apart, or moving vs. building)"

**Implementation Complexity: MEDIUM-EASY** ⭐⭐⭐⭐⭐

**Why Medium-Easy:**

- Leverages existing movement modes
- Requires some new bot behaviors (building)
- Geographic distribution is straightforward
- Building behavior needs development

**Experimental Design:**

```
Methodology:
Test different behavioral patterns with same player count:

1. Clustering Behavior:
   - All bots in same 50x50 area
   - All bots in same 10x10 area
   - Bots following single leader

2. Distribution Behavior:
   - Bots spread across 1000x1000 area
   - Bots in separate 100x100 clusters
   - Random distribution

3. Activity Patterns:
   - All static (no movement)
   - All walking randomly
   - Mix of static and moving
   - Synchronized movement patterns

4. Building Behavior (if implemented):
   - Bots placing/breaking blocks
   - Collaborative building
   - Destructive behavior

Variables to Control:
- Same total bot count
- Same server configuration
- Same monitoring period

Success Metrics:
- Server tick rate per behavior pattern
- Memory usage patterns
- Network traffic per behavior
- CPU usage per behavior
- Chunk loading/unloading impact
```

**Infrastructure Needs:**

- Extend walkbot with building capabilities
- Coordinate bot positioning
- Enhanced monitoring for spatial distribution

### 5. Environment Modification Impact: "What is the impact of players modifying the environment?"

**Implementation Complexity: MEDIUM-HARD** ⭐⭐⭐⭐⭐

**Why Medium-Hard:**

- Requires significant bot capability extension
- Complex world state management
- Challenging to create meaningful modification patterns
- Requires careful measurement of environmental changes

**Experimental Design:**

```
Methodology:
1. Baseline: No environmental changes
2. Block placement: Bots continuously place blocks
3. Block breaking: Bots continuously break blocks
4. Mixed activity: Some bots build, others destroy
5. Terrain modification: Large-scale changes
6. Collaborative building: Coordinated construction

Modification Patterns:
- Individual building (each bot builds separately)
- Collaborative building (coordinated construction)
- Destructive behavior (mining, clearing)
- Mixed creative/destructive
- High-frequency changes vs. low-frequency changes

Variables to Control:
- Same bot count
- Same server configuration
- Rate of environmental changes

Success Metrics:
- Tick rate during heavy modification
- World save/load times
- Memory usage for world state
- Network traffic for block updates
- Client synchronization accuracy
```

**Infrastructure Needs:**

- Major walkbot extensions for block interaction
- World state monitoring tools
- Block change tracking
- Save/load performance monitoring

## Implementation Priority Ranking

### Tier 1 (Immediate Implementation) - EASY

1. **Player Capacity Testing** - Directly uses existing infrastructure
   - Can be implemented in 1-2 days
   - Provides foundational data for other experiments

### Tier 2 (Next Phase) - MEDIUM

2. **Mod Impact Assessment** - Requires server configuration variants

   - Implementation: 3-5 days
   - Provides valuable mod-specific insights

3. **Player Behavior Impact** - Requires bot behavior extensions
   - Implementation: 5-7 days
   - High research value for game design

### Tier 3 (Advanced Phase) - HARD

4. **Environment Modification Impact** - Requires major bot capability extension

   - Implementation: 1-2 weeks
   - High technical complexity

5. **Network Resilience Testing** - Requires network infrastructure
   - Implementation: 1-2 weeks
   - High infrastructure complexity

## Recommended Implementation Sequence

1. **Start with Player Capacity Testing** - Establishes baseline performance characteristics
2. **Implement Mod Impact Assessment** - Builds on capacity testing with configuration variants
3. **Develop Player Behavior Impact** - Extends bot capabilities incrementally
4. **Choose between Environment Modification OR Network Resilience** based on research priorities
5. **Implement remaining experiment** if time/resources permit

## Infrastructure Development Needs

### For All Experiments:

- Enhanced monitoring dashboard
- Automated result collection and analysis
- Statistical analysis tools
- Comparative reporting system

### For Specific Experiments:

- **Capacity Testing**: Multi-node bot coordination
- **Mod Impact**: Configuration management automation
- **Behavior Impact**: Bot behavior framework extension
- **Environment Modification**: Block interaction API
- **Network Resilience**: Network simulation infrastructure

## Expected Research Outcomes

1. **Quantitative Performance Baselines** - Concrete numbers for Luanti capacity
2. **Mod Performance Profiles** - Which mods impact performance most
3. **Behavioral Optimization Insights** - How player patterns affect server performance
4. **Network Resilience Characteristics** - How Luanti handles poor network conditions
5. **Environmental Scaling Limits** - Impact of world modification on performance
6. **Comparative Analysis** - How Luanti compares to Minecraft across all metrics

This analysis provides both immediate actionable experiments and a roadmap for comprehensive Luanti performance characterization.
