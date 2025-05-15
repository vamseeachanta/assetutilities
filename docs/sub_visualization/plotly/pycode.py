"""
plotly line plot for pandas dataframe
  - for more than 1 unique columns in df
  - single date column for x axis
"""

import pandas as pd
import plotly.express as px

# Sample DataFrame
df = pd.DataFrame({
    'date': pd.date_range(start='2024-01-01', periods=10, freq='D'),
    'well_count': [5, 6, 7, 6, 8, 9, 10, 8, 7, 6],
    'depth_count': [100, 110, 115, 120, 130, 125, 140, 135, 130, 128]
})

# Reshape to long format
df_melted = df.melt(id_vars='date', value_vars=['well_count', 'depth_count'],
                    var_name='type', value_name='count')

# Plot
fig = px.line(df_melted, x='date', y='count', color='type',
              title='Well vs Depth Count Over Time')

fig.show()
