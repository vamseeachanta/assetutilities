SET py_environment=MySQL_env
CALL activate %py_environment%

CALL (echo y) | conda install spyder
CALL (echo y) | conda install pandas
CALL (echo y) | conda install munch
pip install mysqlclient-1.3.12-cp35-cp35m-win_amd64.whl
pip install mysql_connector_python-8.0.6-cp35-cp35m-win_amd64.whl
pip install mysqlclient
