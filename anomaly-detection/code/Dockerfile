FROM python:3.5.4
COPY requirements.txt ./
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
COPY / /
EXPOSE 5454
ENTRYPOINT [ "python", "./anomaly_api.py" ]