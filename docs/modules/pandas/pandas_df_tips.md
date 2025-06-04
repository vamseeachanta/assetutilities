## Pandas dataframe tips

encountered Empty dataframe even though there were matching results, This can happen if the data types are different.

```python
df_snwar_remarks = remark_df[remark_df['SN_WAR'].isin(snwar_list)].copy()
```

investigate first datatypes of columns using below code snippet:

```python
df['column_name'].dtype

```

convert either of two along with the datataype

example :

```python
remark_df['SN_WAR'].dtype
output: int64

snwar_list = ['-123456', '-789012']  # Example list of SN_WAR values
these are strings.

remark_df['SN_WAR'] = remark_df['SN_WAR'].astype(str)

df_snwar_remarks = remark_df[remark_df['SN_WAR'].isin(snwar_list)].copy()

```