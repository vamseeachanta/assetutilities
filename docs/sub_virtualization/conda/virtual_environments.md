# VIRTUAL ENVIRONMENTS

##	Introduction
Virtualization helps create isolated environments and help in transferring the application to another computer or scaling applications to a larger scale such as a cluster or cloud computers.
Dockers is a system level virtualization while python virtual environment is program level virtualization. A high level rough estimate comparison is given in Table 13.1.

|Feature          |Virtual Machine|Docker/ Container                   |Program Environment|
|-----------------|---------------|------------------------------------|-------------------|
|Level            |System         |System                              |Program            |
|Installation Time|>5  mins       |<5 mins                             |1-2 mins           |
|Start-up Time    |>5  mins       |5-10 s                              |2 - 3 s            |
|Configuration    |OS, programs   |OS, programs                        |program            |
|Operating System |               |Linux preferred. Unstable in windows|                   |

Virtual environments help isolate the development and (also) deployment of code. The virtual environments help with a stable and consistent environment. 

A virtual environment helps in support and maintenance of reliable code when working on multiple projects:
- Updating or downgrading python modules is easy to do but dependencies can be rendered incompatible. 
- Upgrading some dependencies will sometimes remove or uninstall other required basic dependencies. Therefore, it is recommended to work in virtual environments to avoid this problem. See example in Section 
- If the programmer is required to work on multiple projects which require different modules then it is highly recommended to develop, run and deploy in each application in a dedicated virtual environment. 




Virtual environments also help run legacy codes with ease:
- Legacy codes may not be supported in latest python installations. Therefore, it may be difficult to maintain a reliable code with 1 python installation. 

Virtual Environments and why? 	https://www.python.org/dev/peps/pep-0405/

## Pip

13.3.1	Create venv
•	go to directory where the virtual environment needs to be installed. creates a virtual environment named "pipflask"
o	python -m venv pipflask
•	Activate environment to ensure the packages are installed in appropriate environment
o	activate pipflask
•	Use below command to install. Requirements full path required if in separate directory
o	pip install -r K:\digitaltwinfeed\requirements.txt
•	to check all packages and associated versions.
o	pip list


##	Conda (Anaconda/Miniconda)
13.4.1	Environment.yml
•	Define environment.yml file with an environment name and dependencies.  
o	Example contents of environment.yml:
name: <environment_name>

o	Example with pip packages
			name: API579
channels:
  - defaults
  - conda-forge
dependencies:
  - python=3.6
  - pyyaml
  - yaml
  - oyaml
  - matplotlib
  - scipy
  - pandas
  - python-docx
  - pip:
    - imgkit
    - openpyxl
    - xlrd

•	Create Environment:
	conda env create -f environment.yml 

or use below and Program will search for default environment.yml in current folder and then create the environment.
	conda env create 

•	Removing Environment:
	conda env remove -n FOO

•	Update Environment:
	conda env update -n statistical_assessment –f statistical_assessment.yml


•	Example 1 : environment.yml:
o	name: Common
o	channels:
o	  - defaults
o	dependencies:
o	  - cx_oracle=6.3.1=py35h2fa13f4_0
o	  - numpy=1.14.5=py35h9fa60d3_0
o	  - pandas=0.23.1=py35h830ac7b_0
o	  - pyodbc=4.0.22=py35h6538335_0
o	  - python=3.5.5=h0c2934d_2
o	  - sqlalchemy=1.2.8=py35hfa6e2cd_0
•	Example 2 : environment.yml:
o	name : finance
o	channels:
o	  - defaults
o	dependencies:
o	  - python=3.5
o	  - pandas=0.22.0
o	  - pandas-datareader=0.6.0 

### Detailed Explanation
Install Anaconda. Ensure conda is installed prior to creating the below virtual directory.

•	Create a virtual box
o	(echo y) | conda create -n my_env python=3.5
•	Enter the virtual box
o	activate my_env
•	Install all required packages
o	(echo y) | conda install numpy
o	(echo y) | conda install pandas
o	(echo y) | conda install pymssql
o	(echo y) | conda install spyder
o	(echo y) | conda install matplotlib
•	Run the python file
o	python dynaCard.py --filename 30015201550000MibA1_lf_rpc1_Hprd6_Card_Items_Lastshutdown_SurfaceCardinput.json
•	Exit the environment
o	deactivate my_env
•	ANother EXAMPLE
o	%windir%\system32\cmd.exe "/K" c:\data\Continuum\Anaconda3\Scripts\activate.bat c:\data\Continuum\Anaconda3
o	C:\ProgramData\Anaconda3\pythonw.exe C:\ProgramData\Anaconda3\cwp.py C:\ProgramData\Anaconda3 
o	%windir%\system32\cmd.exe "/K" C:\ProgramData\Anaconda3\Scripts\activate.bat C:\ProgramData\Anaconda3 
o	Working Line for Env
o	CALL %windir%\system32\cmd.exe "/K" c:\data\Continuum\Anaconda3\Scripts\activate.bat  ESPExceptions_env

conda env list	REM Display all environments in Conda
|Task             |Conda package and environment manager command|Pip package manager command         |Virtualenv environment manager command|
|-----------------|---------------------------------------------|------------------------------------|--------------------------------------|
|Install a package|conda install  $PACKAGE_NAME                 |pip install PACKAGE_NAME            |X                                     |
|                 |conda install PACKAGE_NAME ?-channel conda-forge|??                                  |                                      |
|Install a package from a channel|                                             |                                    |                                      |
|Update a package |conda update name ENVIRONMENT_NAME PACKAGE_NAME|pip install upgrade PACKAGE_NAME    |X                                     |
|Update package manager|conda update conda                           |Linux/macOS: pip install U pip Win python m pip install U pip|X                                     |
|Uninstall a package|conda remove name ENVIRONMENT_NAME PACKAGE_NAME|pip uninstall PACKAGE_NAME          |X                                     |
|Create an environment|conda create name ENVIRONMENT_NAME python    |X                                   |cd ENV_BASE_DIR virtualenv ENVIRONMENT_NAME|
|Activate an environment|conda activate ENVIRONMENT_NAME*             |X                                   |source ENV_BASE_DIR/$ENVIRONMENT_NAME/bin/activate|
|Deactivate an environment|conda deactivate                             |X                                   |deactivate                            |
|Search available packages|conda search SEARCH_TERM                     |pip search SEARCH_TERM              |X                                     |
|Install package from specific source|conda install channel URL PACKAGE_NAME       |pip install index-url URL PACKAGE_NAME|X                                     |
|List installed packages|conda list name ENVIRONMENT_NAME             |pip list                            |X                                     |
|Create requirements file|conda list export                            |pip freeze                          |X                                     |
|List all environments|conda info envs                              |X                                   |Install virtualenv wrapper, then lsvirtualenv|
|Install other package manager|conda install pip                            |pip install conda                   |X                                     |
|Install Python   |conda install python=x.x                     |X                                   |X                                     |
|Update Python    |conda update python*                         |X                                   |X                                     |

### Errors

"ERROR: Could not install packages due to an OSError: [WinError 5] Access is denied: 'C:\\Users\\username\\AppData\\Local\\Temp\\pip-uninstall-3senkzeyr\\flask.exe'"

or server:

ERROR: Could not install packages due to an OSError: [WinError 5] Access is 
denied: 'd:\\programs\\miniconda3\\envs\\analysis\\scripts\\flask.exe'
 Consider using the `--user` option or check the permissions.