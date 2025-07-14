# Create list of dataframes
import pandas as pd

array_len = 5

# All elements of list reference the same df.
# i.e. Assigning value to one df assigns to all df elements of array
df_array = [pd.DataFrame()] * array_len

# Elements of list have unique df to assign values as needed
df_array = []
for _i in range(array_len):
    df_array.append(pd.DataFrame())
