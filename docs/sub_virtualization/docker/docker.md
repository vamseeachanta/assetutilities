# Introduction


# Summary


# Example go-by Code

### Python Docker - Conda & PIP hybrid route

Example file 1
<pre>
FROM continuumio/miniconda

ARG conda_env=my_env

# ssl verification bypass settings
RUN mkdir -p /etc/xdg/pip
COPY /docker/pip.conf /etc/xdg/pip/pip.conf

WORKDIR /app
ADD . /app/

# conda ssl verification bypass settings
RUN conda config --set ssl_verify false
#RUN conda update conda

RUN conda env create -f environment.yml

# Make RUN commands use the new environment:
ENV PATH /opt/conda/envs/$conda_env/bin:$PATH
ENV CONDA_DEFAULT_ENV $conda_env

EXPOSE 5015

# The code to run when container is started:
CMD ["python", "/app/temp_service.py"]
</pre>

Example file 2:

FROM conda/miniconda3
https://hub.docker.com/r/conda/miniconda3

Other helpful commands:

Activating environment (NOT working):
<pre>
RUN conda init bash
RUN conda activate my_env
</pre>

Check if Flask is installed:
<pre>
RUN echo "Make sure flask is installed:"
RUN python -c "import flask"
</pre>


Activating environment (working?) and run a code (NOT working) using SHELL & ENTRYPOINT:
<pre>
SHELL ["conda", "run", "-n", "my_env", "/bin/bash", "-c"]
ENTRYPOINT ["conda", "run", "-n", "my_env", "python3", "/app/temp_service.py"]
</pre>

Activating environment (working?) and run a code (NOT working) using SHELL & ENTRYPOINT:
<pre>
SHELL ["conda", "run", "-n", "my_env", "/bin/bash", "-c"]
ENTRYPOINT ["conda", "run", "-n", "my_env", "python3", "/app/temp_service.py"]
</pre>

### Python Docker - pip Route

Example file:
<pre>
FROM python:3.7.9

RUN mkdir /app
WORKDIR /app
ADD . /app/

RUN pip3 install --upgrade pip --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org
#RUN pip3 install -r requirements.txt
RUN pip3 install Flask flask-restplus --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org

EXPOSE 5005
CMD ["python", "/app/temp_service.py"]
</pre>

### Python Docker - Connecting to a SQL server

Key differentiating commands:


RUN ACCEPT_EULA=Y apt-get install -y msodbcsql17 mssql-tools


RUN ACCEPT_EULA=Y apt-get install -y msodbcsql-13.0.1.0-1 mssql-tools-14.0.2.0-1


https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-ver15
https://stackoverflow.com/questions/46405777/connect-docker-python-to-sql-server-with-pyodbc


FROM conda/miniconda3

RUN apt-get update \
        && apt-get install -y curl apt-transport-https gnupg2 \
        && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
        && curl https://packages.microsoft.com/config/debian/9/prod.list > /etc/apt/sources.list.d/mssql-release.list \
        && apt-get update

RUN ACCEPT_EULA=Y apt-get install -y msodbcsql17 mssql-tools

ARG conda_env=my_env

RUN mkdir -p /etc/xdg/pip
COPY /docker/pip.conf /etc/xdg/pip/pip.conf

RUN conda config --set ssl_verify False
RUN conda update conda

WORKDIR /app
COPY ./environment.yml ./
RUN conda env create -f environment.yml
RUN conda config --set ssl_verify True

ADD . /app/

ENV PATH /opt/conda/envs/$conda_env/bin:$PATH
ENV CONDA_DEFAULT_ENV $conda_env

EXPOSE 5005

CMD ["/usr/local/envs/myenv/bin/python3", "/app/service.py"]
