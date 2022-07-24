FROM rappdw/docker-java-python   
COPY requirements.txt ./
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install nltk
RUN python -m nltk.downloader punkt
COPY / /
EXPOSE 3131
ENTRYPOINT [ "python", "./fantastic_four.py"]
