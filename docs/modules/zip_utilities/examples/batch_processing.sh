#!/bin/bash
# Example batch processing script for ZIP utilities
# This script demonstrates the consistent pattern for processing multiple scenarios

# Set error handling
set -e

echo "Starting ZIP utilities batch processing..."

# 03c series - 100yr scenarios
echo "Processing 03c_100yr..."
python -m assetutilities zip_config.yml "{'meta': {'label': '03c_100yr'}, 'analysis': {'input_directory': '../output/csv/03c_100yr'}, 'file_management': {'input_directory': '../03c_100yr', 'output_directory': '../output/zip/03c_100yr'}}"

# 03c environmental sensitivity
echo "Processing 03c_100yr_env_sens..."
python -m assetutilities zip_config.yml "{'meta': {'label': '03c_100yr_env_sens'}, 'analysis': {'input_directory': '../output/csv/03c_100yr_env_sens'}, 'file_management': {'input_directory': '../03c_100yr_env_sens', 'output_directory': '../output/zip/03c_100yr_env_sens'}}"

# 04c maintenance scenarios
echo "Processing 04c_maintenance_1yr..."
python -m assetutilities zip_config.yml "{'meta': {'label': '04c_maintenance_1yr'}, 'analysis': {'input_directory': '../output/csv/04c_maintenance_1yr'}, 'file_management': {'input_directory': '../04c_maintenance_1yr', 'output_directory': '../output/zip/04c_maintenance_1yr'}}"

# 05c topside isolation scenarios
echo "Processing 05c_topside_iso_1000yr..."
python -m assetutilities zip_config.yml "{'meta': {'label': '05c_topside_iso_1000yr'}, 'analysis': {'input_directory': '../output/csv/05c_topside_iso_1000yr'}, 'file_management': {'input_directory': '../05c_topside_iso_1000yr', 'output_directory': '../output/zip/05c_topside_iso_1000yr'}}"

# 06c tsunami scenario
echo "Processing 06c_0500yr_tsunami..."
python -m assetutilities zip_config.yml "{'meta': {'label': '06c_0500yr_tsunami'}, 'analysis': {'input_directory': '../output/csv/06c_0500yr_tsunami'}, 'file_management': {'input_directory': '../06c_0500yr_tsunami', 'output_directory': '../output/zip/06c_0500yr_tsunami'}}"

# 07c fatigue scenario
echo "Processing 07c_fatigue..."
python -m assetutilities zip_config.yml "{'meta': {'label': '07c_fatigue'}, 'analysis': {'input_directory': '../output/csv/07c_fatigue'}, 'file_management': {'input_directory': '../07c_fatigue', 'output_directory': '../output/zip/07c_fatigue'}}"

# 08c damaged scenarios
echo "Processing 08c_0100yr_damaged..."
python -m assetutilities zip_config.yml "{'meta': {'label': '08c_0100yr_damaged'}, 'analysis': {'input_directory': '../output/csv/08c_0100yr_damaged'}, 'file_management': {'input_directory': '../08c_0100yr_damaged', 'output_directory': '../output/zip/08c_0100yr_damaged'}}"

# 09c sensitivity scenarios
echo "Processing 09c_sens..."
python -m assetutilities zip_config.yml "{'meta': {'label': '09c_sens'}, 'analysis': {'input_directory': '../output/csv/09c_sens'}, 'file_management': {'input_directory': '../09c_sens', 'output_directory': '../output/zip/09c_sens'}}"

echo "All ZIP utilities processing completed successfully!"

# Optional: Generate summary report
echo "=== Processing Summary ==="
echo "Check the following directories for ZIP files:"
echo "  - ../output/zip/03c_100yr/"
echo "  - ../output/zip/03c_100yr_env_sens/"
echo "  - ../output/zip/04c_maintenance_1yr/"
echo "  - ../output/zip/05c_topside_iso_1000yr/"
echo "  - ../output/zip/06c_0500yr_tsunami/"
echo "  - ../output/zip/07c_fatigue/"
echo "  - ../output/zip/08c_0100yr_damaged/"
echo "  - ../output/zip/09c_sens/"