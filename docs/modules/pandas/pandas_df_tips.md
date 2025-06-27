## Pandas dataframe tips


### Pandas column datatypes mismatch

encountered Empty dataframe even though there were matching results, This can happen if the data types are different.

Below , some values from SN_WAR column , there are some matching values but the data types are different, so the filtering returns an empty dataframe.
```python
snwar_list = snwar_df['SN_WAR'].dropna().unique().tolist()

df_snwar_remarks = remark_df[remark_df['SN_WAR'].isin(snwar_list)].copy()
```

investigate first datatypes of columns using below code snippet:
```python
df['column_name'].dtype

```

convert either of two along with the datataype.

example :

```python
remark_df['SN_WAR'].dtype
output: int64

snwar_list = ['-123456', '-789012'] # Example list of SN_WAR values
dtype : str 
remark_df['SN_WAR'] = remark_df['SN_WAR'].astype(str)

df_snwar_remarks = remark_df[remark_df['SN_WAR'].isin(snwar_list)].copy()
Now , df_snwar_remarks will contain the filtered dataframe with matching SN_WAR values.
```

### Move column to the position


**Example DataFrame**

```python
import pandas as pd

df = pd.DataFrame({
    'A': [1, 2],
    'B': [3, 4],
    'C': [5, 6],
    'D': [7, 8]
})
```
**Move column 'C' to position 0**

```python
col = df.pop('C')
df.insert(0, 'C', col)

print(df)
```

output:
```
   C  A  B  D
0  5  1  3  7
1  6  2  4  8
```

