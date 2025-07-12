import subprocess
import os

def generate_leave(player_count, leaves_per_second, burstiness, file_path):
    script_fpath = os.path.join(os.path.dirname(__file__), 'generate_leaving.js')

    command = [
        'node',
        script_fpath,
        str(player_count),
        str(leaves_per_second),
        str(burstiness),
        file_path
    ]

    print(subprocess.run(command, capture_output=True, text=True))

def generate_join(player_count, joins_per_second, burstiness, file_path):
    script_fpath = os.path.join(os.path.dirname(__file__), 'generate_joining.js')

    command = [
        'node',
        script_fpath,
        str(player_count),
        str(joins_per_second),
        str(burstiness),
        file_path
    ]

    print(subprocess.run(command, capture_output=True, text=True))

def generate_tp(player_count, global_spread, tps_a_second, duration, file_path):
    script_fpath = os.path.join(os.path.dirname(__file__), 'generate_movement_tp.js')

    command = [
        'node',
        script_fpath,
        str(player_count),
        str(global_spread),
        str(tps_a_second),
        str(duration),
        file_path
    ]

    print(subprocess.run(command, capture_output=True, text=True))

def generate_fighting(player_count, fight_interval, file_path):
    script_fpath = os.path.join(os.path.dirname(__file__), 'generate_fighting.js')

    command = [
        'node',
        script_fpath,
        str(player_count),
        str(fight_interval),
        file_path
    ]

    print(subprocess.run(command, capture_output=True, text=True))

def generate_movement(player_count, global_preferential_attachment, local_preferential_attachment, file_path):
    script_fpath = os.path.join(os.path.dirname(__file__), 'generate_movement.js')

    command = [
        'node',
        script_fpath,
        str(player_count),
        str(global_preferential_attachment),
        str(local_preferential_attachment),
        file_path
    ]

    subprocess.run(command, capture_output=True, text=True)

def generate_movement_relative(player_count, global_preferential_attachment, local_preferential_attachment, file_path):
    script_fpath = os.path.join(os.path.dirname(__file__), 'generate_movement_relative.js')

    command = [
        'node',
        script_fpath,
        str(player_count),
        str(global_preferential_attachment),
        str(local_preferential_attachment),
        file_path
    ]

    subprocess.run(command, capture_output=True, text=True)

def generate_terrain_modification(player_count, build_interval, blocks_at_a_time, duration, file_path):
    script_fpath = os.path.join(os.path.dirname(__file__), 'generate_terrain_modification.js')
    command = [
        'node',
        script_fpath,
        str(player_count),
        str(build_interval),
        str(blocks_at_a_time),
        str(duration),
        file_path
    ]

    subprocess.run(command, capture_output=True, text=True)

def generate_entity_attack(player_count, attack_interval, duration, file_path):
    script_fpath = os.path.join(os.path.dirname(__file__), 'generate_entity_attack.js')
    command = [
        'node',
        script_fpath,
        str(player_count),
        str(attack_interval),
        str(duration),
        file_path
    ]

    subprocess.run(command, capture_output=True, text=True)
