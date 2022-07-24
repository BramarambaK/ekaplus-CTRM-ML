library(plumber)
r <- plumb("recommendation.R")
r$run(host="0.0.0.0",port=4400)