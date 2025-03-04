import subprocess
import os

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
