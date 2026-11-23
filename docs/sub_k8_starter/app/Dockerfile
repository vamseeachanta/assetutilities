FROM python:3.7

RUN mkdir /app
WORKDIR /app
ADD . /app/
# RUN pip install --upgrade pip
# RUN pip install -r requirements.txt
RUN pip install --upgrade pip --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org
RUN pip install Flask --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org

EXPOSE 5000
CMD ["python", "/app/main.py"]