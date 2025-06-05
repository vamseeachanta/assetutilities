meta:
    basename: excel_utilities
    type: csv_copy_to_excel

data:
    groups:
        - name: csv_copy_to_excel
          input: 
            filename: inputs.csv
          target: 
            filename: target.xlsx
            sheet_name: inputs

<code>
    if 'basename' in cfg:
        basename = cfg["basename"]
    elif 'meta' in cfg:
        basename = cfg["meta"]["basename"]
    else:
        raise ValueError("basename not found in cfg")
</code>

