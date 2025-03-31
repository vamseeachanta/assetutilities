CALL conda activate assetutilities
CALL python -m assetutilities .\test_file_management.yml
CALL python -m assetutilities .\test_file_management_not_contain.yml

@REM CALL python -m assetutilities .\test_zip_by_stem.yml "{'meta': {'arg_parse_dict': True, 'label': 'argprase_dict'}}"
