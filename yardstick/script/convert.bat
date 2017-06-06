@echo off
for %%f in (workload\*.bin) do (
  java -jar yardstick-1.0-jar-with-dependencies.jar --csvdump --input %%f --output workload\%%~nf.csv"
)
