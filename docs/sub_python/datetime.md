# Datetime

## Date Formatting and Locators in Matplotlib

### Setting Date on X-Axis

### I. Formatting Dates Style

1. **Formatting Dates in Months with Year**
   - Use `mdates.DateFormatter('%b %Y')` to format the date as the month name followed by the year.
     - Example: `Jan 2022`
   - Apply this formatter using:
     ```python
     ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
     ```

     **Locator with Months**
   - Use `mdates.MonthLocator(interval=2)` to set the interval for ticks on the x-axis to every 2 months.
     ```python
     ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
     ```

2. **Formatting Dates in Days with Month Name**
   - To format the date as the day followed by the month name:
     ```python
     ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
     ```
     - Example: `12 Jan`
   
     **Locator with Days**
   - To set ticks at day intervals:
     ```python
     ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))  # Weekly intervals (every 7 days)
     ```
     **Locator with Weeks**
   - To set ticks at weekly intervals:
     ```python
     ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))  # Every week
     ```


3. **Formatting Dates in Years**
   - If you want to display only the year:
     ```python
     ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
     ```
     - Example: `2022`
  
     **Locator with years**
   - To set ticks at yearly intervals:
     ```python
     ax.xaxis.set_major_locator(mdates.YearLocator(interval=1))  # Every 1 year
     ```
  

### II. Formatting Axis

**Rotating X-Axis Labels**
   - For better readability, rotate x tick labels by 45 degrees:
  
     ```python
     plt.xticks(rotation=45)
     ```

**Auto-formatting Dates**
   - Use `fig.autofmt_xdate()` to adjust the x-axis date labels for better display:
  
     ```python
     fig.autofmt_xdate()
     ```


## References 

 - https://docs.python.org/3/library/datetime.html
 - https://www.dataquest.io/blog/python-datetime/
