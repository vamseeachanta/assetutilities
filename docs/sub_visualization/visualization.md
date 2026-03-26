### Introduction

### Architecture

### Data Input

- The data input can be  multiple .CSV file

#### Data in Input file

- The input file should contain the following columns:
  - X-axis data
  - Y-axis data
  - Legend data (optional)

#### CSV Files

- Define csv files and appropriate data definitions in input file
- CSV file rules:
  - The first row is the header row
  - For equal X and Y columns defined, the program chooses legend labels based on Y columns by default.
    - If X columsn are to be given, provide the legend labels in settings['legend']['label'] (Add test case for this)
    - Usecase should arise to change this

#### YML files (To be coded?)

- Should be by keys
- Define x, y and legend data in an input file

## Test

| Test ID | Test Description | Test File | Status (Pass/Fail) |
|---------|------------------|-----------|--------------------|
| 1       | Test for CSV file | x-y_.py | Pass               |
