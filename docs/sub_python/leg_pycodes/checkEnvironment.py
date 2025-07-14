import os

projectPythonEnvironment = "OrcaFlex_env"

osPath = os.__file__
osPathList = osPath.split("\\")

if projectPythonEnvironment in osPathList:
    print("Running in project python virtual environment : " + projectPythonEnvironment)
else:
    print("Warning: NOT running in project python environment")
