# NONE FUNCTIONAL!!!!
FROM conda/miniconda3

RUN apt-get update \
        && apt-get install -y curl apt-transport-https gnupg2 \
        && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
        && curl https://packages.microsoft.com/config/debian/9/prod.list > /etc/apt/sources.list.d/mssql-release.list \
        && apt-get update

# NOT Working
# RUN ACCEPT_EULA=Y apt-get install -y msodbcsql mssql-tools
# NOT Working
# RUN ACCEPT_EULA=Y apt-get install msodbcsql=13.0.1.0-1 mssql-tools=14.0.2.0-1

ARG conda_env=my_env

RUN mkdir -p /etc/xdg/pip
COPY /docker/pip.conf /etc/xdg/pip/pip.conf

RUN conda config --set ssl_verify False
RUN conda config --set remote_read_timeout_secs 2000
RUN conda update conda

WORKDIR /app
COPY ./environment.yml ./
RUN conda env create -f environment.yml
RUN conda config --set ssl_verify True

ADD . /app/

ENV PATH /usr/local/envs/$conda_env/bin:$PATH
ENV CONDA_DEFAULT_ENV $conda_env

EXPOSE 5005

CMD ["python3", "/app/temp_service.py"]
