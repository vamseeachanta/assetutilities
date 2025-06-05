## Date format edge cases


encountered below error while appending dates with formats into excel

```
time data '8/11/2025' does not match format '%d/%m/%Y' (match)
```

### This error occurs when the date format in the data does not match the expected format.

**code snippet to handle this:**

```python
def date_to_sortable_int(date_str):
    """Convert date string in various formats to sortable integer (YYYYMMDD)"""
    try:
        # Try to extract month, day, year with flexible regex
        match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', date_str)
        if match:
            month, day, year = match.groups()
            month = int(month)
            day = int(day)
            year = int(year)
            
            # Handle 2-digit years (assuming 20xx for years < 50, 19xx otherwise)
            if year < 50:
                year += 2000
            elif year < 100:
                year += 1900
            
            return year * 10000 + month * 100 + day
    except:
        pass
    return 0  # Default value for invalid dates
```