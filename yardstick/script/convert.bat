@echo off
for %%f in (workload\*.bin) do (
  java -jar ..\target\yardstick-1.0-jar-with-dependencies.jar --csvdump --input %%f --output workload\%%~nf.csv"
)
