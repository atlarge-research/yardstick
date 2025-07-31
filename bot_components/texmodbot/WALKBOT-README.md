# Walkbot for Minetest

A simple bot that connects to a Minetest server and automatically walks around in different patterns.

## Prerequisites

This bot requires the **Rust nightly** toolchain to compile and run. You must install and set nightly as the active toolchain for this project:

```bash
# Install nightly toolchain
rustup install nightly

# Set nightly as the override for this project
rustup override set nightly

# Verify nightly is active
rustc --version
```

## Features

- Four movement modes:
  - **Random**: randomly walks and changes direction
  - **Circular**: walks in a circular pattern
  - **Static**: stands in place but rotates to look around
  - **Follow**: intelligently navigates toward a specified target coordinate (x,y,z) in 3D space
- Configurable movement speed
- Fixed Y-position to prevent falling or getting stuck in the air
- Auto-registration capability
- Automatic reconnection
- Position tracking with logs

## Usage

### Command Line Options

```
walkbot [OPTIONS] <SERVER_ADDRESS>

Arguments:
  <SERVER_ADDRESS>  Server address in format address:port

Options:
  -u, --username <USERNAME>            Player name [default: walkbot]
  -p, --password <PASSWORD>            Password [default: walkbot123]
      --force-lowercase                Force using lowercase username for authentication
      --register                       Register a new account (if false, tries to log in to existing account)
      --auto-register                  If login fails, try registration [default: true]
  -m, --mode <MODE>                    Movement mode: random, circular, static, or follow [default: random]
  -s, --speed <SPEED>                  Movement speed in seconds between direction changes [default: 2.0]
      --target-x <X>                   Target X coordinate for "follow" mode
      --target-y <Y>                   Target Y coordinate (height) for "follow" mode [default: 8.5]
      --target-z <Z>                   Target Z coordinate for "follow" mode
  -q, --quit-after-seconds <SECONDS>   Quit after specified number of seconds
  -h, --help                           Print help information
  -V, --version                        Print version information
```

### Examples

Basic usage:

```
cargo run --bin walkbot -- 127.0.0.1:30000
```

Circular movement pattern:

```
cargo run --bin walkbot -- 127.0.0.1:30000 --mode circular --speed 1.5
```

Follow a target location:

```
cargo run --bin walkbot -- 127.0.0.1:30000 --mode follow --target-x 10 --target-y 12 --target-z -5
```

Custom username and password:

```
cargo run --bin walkbot -- 127.0.0.1:30000 --username testbot --password test123
```

Connect for a limited time:

```
cargo run --bin walkbot -- 127.0.0.1:30000 --quit-after-seconds 300
```

### Using the Run Script

A convenience script is provided:

```bash
./run_walkbot.sh
```

You can edit this script to customize the default parameters.

## Implementation Details

The walkbot is built on the same framework as texmodbot, using the mt_net and mt_auth libraries to handle the network protocol and authentication with the Minetest server.

The bot implements four different walking behaviors:

1. **Random Walk**: Randomly selects movement keys and direction changes with configurable probability.
2. **Circular Walk**: Maintains forward movement while gradually changing direction to create a circular path.
3. **Static Position**: Remains in place but rotates to look around.
4. **Follow Mode**: Intelligently navigates toward a specified coordinate by calculating the angle to the target, rotating to face it, and then moving forward. The bot continuously updates its direction based on its current position and the target, making it capable of navigating to any point in the game world.

## Technical Details

### Y Position Handling

The bot has two modes of Y position handling:

1. **Default Mode** - For random, circular, and static movement patterns, the bot maintains a fixed Y position (height) of 8.5 blocks, which is the standard player height in Minetest. This ensures that:

   - The bot doesn't fall through the ground
   - The bot doesn't float in the air
   - Movement is consistent on a flat surface

2. **Follow Mode** - When following a target, the bot will attempt to reach the specified Y coordinate using jump and sneak controls. It will:
   - Jump if the target Y is significantly higher than current position
   - Sneak if the target Y is significantly lower
   - Otherwise maintain the specified Y coordinate

This is implemented by monitoring and correcting the Y coordinate during movement, adapting to the target coordinates in follow mode.

### Follow Mode Implementation

The Follow mode uses vector mathematics and trigonometry to calculate the most efficient path to the target in 3D space:

1. It calculates the vector from the bot's current position to the target position (x, y, z)
2. It converts the horizontal component (x, z) to a yaw angle that the bot needs to face
3. It gradually rotates the bot to face this angle
4. Based on the vertical difference (y), it will use jump or sneak controls as needed
5. Once the bot is approximately facing the target, it moves forward
6. It continuously recalculates its path in all three dimensions as it moves

The implementation properly handles Minetest's coordinate and angle system:

- In Minetest, 0° yaw is north (+Z), 90° is east (+X), 180° is south (-Z), and 270° is west (-X)
- Movement directions are calculated based on this system using trigonometric functions
- The Y axis is handled separately with jump and sneak controls

## Future Improvements

- Add obstacle detection and avoidance
- Implement pathfinding algorithms for more complex terrain
- Add waypoint systems to follow pre-defined routes
- Implement terrain height detection for variable Y positions
- Add interaction with the environment (e.g., digging, placing blocks)
