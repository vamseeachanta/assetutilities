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
            sheetname: inputs
            make_a_copy: True
            output_filename: target_updated.xlsx

<code>
    if 'basename' in cfg:
        basename = cfg["basename"]
    elif 'meta' in cfg:
        basename = cfg["meta"]["basename"]
    else:
        raise ValueError("basename not found in cfg")
</code>

