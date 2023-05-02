# get a dotnet sdk image linux arm and copy the current folder to the image
FROM mcr.microsoft.com/dotnet/sdk:6.0
WORKDIR /app
COPY . .

# RUN  mkdir ./build
CMD ["dotnet", "run", "--project", "TrClientTest/TrClientTest.csproj"]