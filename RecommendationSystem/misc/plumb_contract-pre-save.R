library(plumber)
r <- plumb("D:/work/recommendation-system/rule-based/development/CTRM-ML/RecommendationSystem/src/contract-recommendation-pre-save.R")
r$run(host="0.0.0.0",port=4000)
