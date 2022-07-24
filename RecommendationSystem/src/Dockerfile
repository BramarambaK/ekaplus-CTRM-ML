# start from the rocker/r-ver:3.5.3 image
FROM rocker/r-ver:3.5.3

# install the linux libraries needed for plumber
RUN apt-get update -qq && apt-get install -y \
      libssl-dev \
      libcurl4-gnutls-dev 
	  
RUN R -e "install.packages(c('plumber', 'jsonlite', 'httr', 'lubridate', 'dplyr', 'plyr', 'rjson', 'RJSONIO', 'base64enc', 'RCurl'), repos='https://CRAN.R-project.org/')"
# copy everything from the current directory into the container
COPY / /

EXPOSE 4400
ENTRYPOINT ["Rscript", "plumb-recommendation.R"]
