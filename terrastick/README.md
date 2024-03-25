The structure of the project is as follows:
```
├── Deployment                          # Contains the deployment scripts for DAS5 and DAS6
├── PlayerEmulations                    # Contains the terraria bot code
├── README.md
├── Server-side-packet-logging-plugin   # Contains the terraria server plugin for logging packets
└── analysis-scripts                    # Contains the analysis scripts
```

To prepare for terrastick deployment make sure to do the following:
* The world file to test should be placed in `terrastick/Deployment/worlds` directory. We have a default world file `2022DistSys.wld` in the directory.
* If you would like to make a code change in `analysis-scripts`, `PlayerEmulations` or `Server-side-packet-logging-plugin` directories, make sure to create a new release. Then, once the version you would like to test is available in https://github.com/atlarge-research/yardstick/releases, the `TERRASTICK_VERSION` in das-config.txt (terrastick/Deployment/scripts/configs/das-config.txt) should be set to this desired release name.
* Then, go to the `terrastick/Deployment/scripts` directory and run the `das.sh` script. For any change made to das.sh or das-config.txt, there is no need to create a new release. 
* You can tweak the `das-config.txt` file to change the number of players, the number of bots, the number of iterations, etc. Possible options for `TERRASTICK_WORKLOAD` are `TEL` and `WLK`. The `TEL` workload is the default workload which represents teleportation and the `WLK` workload is the workload with the walking bot.

The result of the experiment can be found in /var/scratch/{VU username}/terraria-experiment-{datetime of run} folder. The plots are in the plots subfolder. 

For testing the bot on local, follow the advice in terrastick/PlayerEmulations/README.md.
