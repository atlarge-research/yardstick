for i in {1..10}; do
  dotnet run --project ../PlayerEmulations/TrClientTest/TrClientTest.csproj &
done

# Wait for all instances to finish
wait
