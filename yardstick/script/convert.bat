
for %%f in (workload\*.bin) do (
  java -jar target\yardstick-1.0.1-jar-with-dependencies.jar -e 4 -h localhost -Ebots=1 -Eduration=20 --csvdump --input %%f --output workload\%%~nf.csv"
)
