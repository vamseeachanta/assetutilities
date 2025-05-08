## Introduction

Typically python enviornments and associated libraries is installed using a package manager like Conda. The following instructions will help install Miniconda, a minimal installer for conda.

### Installation Steps

- If reinstalling conda:
    - backup any conda environments you might be interested in. Export packages using conda env export. [https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html)
    - Uninstall the existing version of Anaconda/ Miniconda.

- Go to https://docs.conda.io/en/latest/miniconda.html
    - Pick the installer based on your Operating System, python version and processor type (32 bit vs 64 bit).  
        - recommend python version >= 3.7.x
        - Under Installation Type, select the "Just Me" option.

    - Keep the default options for the rest of the installation screens. 
    - In the final screen, the installation should complete usually within 5 minutes.


## Typical Errros

### SSL Errors

The following actions will resolve typical SSL errors encountered during package installations. These will also be helpful when inside typical corporate firewalls:

- For Conda SSL errors:
    - Open miniconda prompt:
        - Go to Start > Search for Miniconda
        - Open Miniconda Command Prompt
    -  Run following commands inside Miniconda shell to disable ssl and increase timeout to 30 mins     
    <pre> 
    conda config --set ssl_verify False   
    conda config --set remote_read_timeout_secs 1800
    </pre>
    - Close and reopen the shell for settings to take effect.
    - creating condarc file
        - https://stackoverflow.com/questions/29896309/how-to-create-a-condarc-file-for-anaconda

- For pip SSL errors:
    - Create directory C:\Users\<<user_network_id>>\pip 
    - copy pip.ini, see [py\ref\pip.ini](py\ref\pip.ini) to above created pip directory.
    - for unix/linux computers:
        - add pip.conf file in appropriate location
        - https://stackoverflow.com/questions/25981703/pip-install-fails-with-connection-error-ssl-certificate-verify-failed-certi
        - https://pip.pypa.io/en/stable/topics/configuration/
        - https://jhooq.com/pip-install-connection-error/
- For docker SSL Errors containers, different ways:
    - For pip based SSL errors, the following are examples: 
        - Reference: https://stackoverflow.com/questions/56131677/run-pip-install-there-was-a-problem-confirming-the-ssl-certificate-ssl-certi
        - For working examples of Docker images with SQL: refer py/odbcsql13_image and py/odbcsql17_image

<pre> 
    RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org --no-cache-dir -r /usr/src/app/requirements.txt
    RUN pip3 install Flask flask-restplus --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org

</pre>
    - Get latest certificates for docker OS: RUN apt-get install ca-certificates
    - conda ssl_verify false for conda environment.yml: 
        - See example code below.
        - Note, This still gives pip ssl verify errors for pip based pacakges in environment.yml

<pre> 
    RUN conda update conda
    RUN conda config --set ssl_verify False
</pre>
    - 

### Removing Corrupt Packages

Error:
<pre> 
    <UserName>\AppData\Local\Continuum\anaconda3\pkgs\pyqt-5.6.0-py35hd46907b_5 appears to be corrupted.
</pre>

<pre> 
    conda clean --packages --tarballs
</pre>


## References


https://conda.io/projects/conda/en/latest/user-guide/configuration/disable-ssl-verification.html 

https://medium.com/@iffi33/dealing-with-ssl-authentication-on-a-secure-corporate-network-pip-conda-git-npm-yarn-bower-73e5b93fd4b2