for i in {1..50}; do
  dotnet run --project ../PlayerEmulations/TrClientTest/TrClientTest.csproj &
done

# Wait for all instances to finish
wait
