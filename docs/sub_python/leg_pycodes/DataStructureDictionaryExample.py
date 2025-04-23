# We created data as dictionary and stored keys and values into it

>>> data = dict(length=50, height=60, width=40, thickness = 10)
>>> data['length']   #To view the value of 'length'
50
>>> data.keys() # To view all the keys in the dictionary
dict_keys(['length', 'height', 'width', 'thickness'])

>>> data.values()  # To view the values in the dictionary
dict_values([50, 60, 40, 10])

>>> data.items() # To view all the items in the dictionary we user items()
dict_items([('length', 50), ('height', 60), ('width', 40), ('thickness', 10)])

>>> data['pressure']=200 # To add a key and values in dict.
>>> data.items()
dict_items([('length', 50), ('height', 60), ('width', 40), ('thickness', 10), ('pressure', 200)])

>>> del data['width'] #To delete the key in the dict.
# We have deleted 'Width' in the above dictionary
>>> data.items()
dict_items([('length', 50), ('height', 60), ('thickness', 10), ('pressure', 200)])

>>> data['height']
60
>>> data['thickness']
10
