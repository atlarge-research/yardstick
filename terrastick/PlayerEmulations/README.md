### Building the bot code for an OS+Platform
* cd to `TrClientTest` and run `dotnet build -r <RID>` where RIDs for the OS+Platform are listed below in the table.
* The build is placed in `TrClientTest/bin/Debug/net6.0/<RID>/`

### Creating a release for an OS+Platform
* cd to `TrClientTest` and run `dotnet publish -r <RID> -c Release` where RIDs for the OS+Platform are listed below in the table.
* The release is placed in `TrClientTest/bin/Release/net6.0/<RID>/publish/`

### RIDs
| OS | Platform | RID |
| --- | --- | --- |
| Windows | x64 | win-x64 |
| Linux | x64 | linux-x64 |
| OSX | x64 | osx-x64 |
| OSX | ARM64 | osx-arm64 |
