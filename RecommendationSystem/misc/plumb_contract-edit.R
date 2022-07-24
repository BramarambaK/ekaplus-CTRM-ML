library(plumber)
r <- plumb("D:/work/CTRM-ML/RecommendationSystem/src/contract-recommendation-edit.R")
r$run(host="0.0.0.0",port=3000)
