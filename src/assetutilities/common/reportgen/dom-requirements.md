# additional requirements along the way 

redo. updated instructions below

- DocumentDOM is not a singleton. need not be. 
- handle updated yml cfg file. 

- add a private variable to DocumentDOM this should be a dictionary called model
- the dictionary models data present in reportgen-cfg , except the "basename" attribute present in reportgen-cfg
- also update initialize_from_config function to load to the re-structured dictionary
- list changes make 1 change at a time get confirmation before proceeding on to the next change

# 20241202-note 

Migrated functionality from aeCon repo.