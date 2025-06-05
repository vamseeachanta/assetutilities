## Handling large data objects in python

When working with large data objects in Python, it is important to consider memory management and performance. Here are some tips and techniques to handle large data objects efficiently:

- Do not generate csv files with large data storage. Instead, use the python `pickle` module to serialize and deserialize Python objects. This is more efficient than writing to CSV files, especially for large data objects.
- Instead of large csv files storage for data, generate binary files with the `pickle` module. This will save space and improve performance when reading and writing data.

reference:
https://snyk.io/blog/guide-to-python-pickle/