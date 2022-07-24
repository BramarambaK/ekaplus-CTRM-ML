library(plumber)
r <- plumb("recommendation-1.R")
r$run(host="0.0.0.0",port=5555)