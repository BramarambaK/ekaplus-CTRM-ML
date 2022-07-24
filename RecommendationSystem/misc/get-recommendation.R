
#####################################################################
### R code for recommending the values in the field to create contract
######################################################################

###########################
### Load required packages
###########################
suppressWarnings(suppressMessages(library(plumber)))
suppressWarnings(suppressMessages(library(jsonlite)))
suppressWarnings(suppressMessages(library(httr)))
suppressWarnings(suppressMessages(library(lubridate)))
suppressWarnings(suppressMessages(library(dplyr)))
suppressWarnings(suppressMessages(library(plyr)))
suppressWarnings(suppressMessages(library(qpcR)))
suppressWarnings(suppressMessages(library(rjson)))
suppressWarnings(suppressMessages(library(RJSONIO)))

############################################################
### Extract the data for the general details of the contract
############################################################
getDeliveryDates <- function(){
  today <- ymd(Sys.Date())
  Next_month <- today %m+% months(1)
  today <- strftime(as.POSIXlt(today, "UTC"), "%Y-%m-%dT%H:%M:%S%z")
  Next_month <- strftime(as.POSIXlt(Next_month, "UTC"), "%Y-%m-%dT%H:%M:%S%z")
  fromTo <- list(today, Next_month)
  return(fromTo)
}

extract_data_for_user <- function(data_for_userId, ObjectId, input_user_id) {

  app_data <- sapply(data_for_userId, function(x) x[ObjectId %in% x$sourceObjectId], simplify=F)
  data_for_userId <- sapply(app_data, function(x) x[input_user_id %in% x$userId], simplify=F)
  data_for_userId <- data_for_userId[lengths(data_for_userId)!= 0]
  return(data_for_userId)
}

recommend_general_details <- function(data_for_userId, ObjectId, input_user_id, traderUserId) {

  if (length(data_for_userId) == 0){
    return("Invalid user Id.")
  } else {
    recommendation_general_details <- data_for_userId[[1]][['data']][[traderUserId]][['generalDetails']]
    if (is.null(recommendation_general_details)){
      res = list("issueDate" = strftime(Sys.Date(), "%d-%m-%Y"), "dealType" = "Third_Party", "contractType" = NA,"cpProfileId"= NA,"applicableLawId" = NA, "arbitrationId" = NA, "incotermId" = NA)
      return(res)
      } else {
        recommendation_general_details[["issueDate"]] <- strftime(Sys.Date(), "%d-%m-%Y")
        return(recommendation_general_details)
      }
    }
}

create_recommendation_list <- function() {
  dates <- getDeliveryDates()
  recommendations <- list("productId" = NA, "quality" = NA, "itemQtyUnitId" = "QUM-17498", "toleranceType" = "Percentage", "toleranceLevel" = "Buyer" , "tolerance" = NA, 'shipmentMode' = 'Barge', 'originationCountryId' = NA 
          , 'loadingLocationGroupTypeId' = NA, 'destinationCountryId' = NA, 'destinationLocationGroupTypeId' = NA,  'profitCenterId' = NA, 'strategyAccId' = NA
          ,  pricing = list("priceType" = "Flat", "priceUnit" = "USD/Barrel", "price" = NA)
          , "deliveryFromDate" = dates[[1]], "deliveryToDate" = dates[[2]]
          , latePaymentInterestDetails = list("interestRateType " = "Absolute"))
  return(recommendations)
}

recommend_item_details <- function(data_for_userId, contract_fields, ObjectId) {

  traderUserId <- contract_fields[["traderUserId"]]
  contractType <- contract_fields[["contractType"]]
  cpProfileId <- contract_fields[["cpProfileId"]]
  input_user_id <- contract_fields[["userId"]]

  if (length(data_for_userId) == 0){
    return("Invalid user Id.")
  } else {
    recommendation_itemdetails <- data_for_userId[[1]][['data']][[traderUserId]][['itemDetails']][[contractType]][[cpProfileId]][["on_load"]]

    if ( (is.null(recommendation_itemdetails) == TRUE)){
      recommendation_list <- create_recommendation_list()
      return(recommendation_list)

      } else if (recommendation_itemdetails == "NA") {
        recommendation_list <- create_recommendation_list()
        return(recommendation_list)
      } else {
        return(recommendation_itemdetails)
      }
  }
  return(recommendation_itemdetails)
}

###############################################################
### Trigger the below function only when the object is contract
###############################################################
item_details_on_change <- function(data_for_userId, contract_fields, ObjectId, change) {

  traderUserId <- contract_fields[["traderUserId"]]
  contractType <- contract_fields[["contractType"]]
  cpProfileId <- contract_fields[["cpProfileId"]]
  input_user_id <- contract_fields[["userId"]]
  product_id <- contract_fields[['productId']]

  if (length(data_for_userId) == 0){
    return("Invalid user Id.")
  } else {
    if (change == 'product') {
      itemdetails_prod_change <- data_for_userId[[1]][['data']][[traderUserId]][['itemDetails']][[contractType]][[cpProfileId]][["on_change"]][[product_id]][['on_product_change']]
      
      if (is.null(itemdetails_prod_change)){
        dates <- getDeliveryDates()

        recommendation_list = list("productId" = NA, "quality" = NA, "itemQtyUnitId" = "QUM-17498", "toleranceType" = "Percentage", "toleranceLevel" = "Buyer" , "tolerance" = NA, 'shipmentMode' = 'Barge', 'originationCountryId' = NA 
          , 'loadingLocationGroupTypeId' = NA, 'destinationCountryId' = NA, 'destinationLocationGroupTypeId' = NA,  'profitCenterId' = NA, 'strategyAccId' = NA)
        return(recommendation_list)
        } else {
          return(itemdetails_prod_change)
        }

    } else if (change == "origin_country") {
      originationCountryId <- contract_fields[['originationCountryId']]
      itemdetails_origin_country_change <- data_for_userId[[1]][['data']][[traderUserId]][['itemDetails']][[contractType]][[cpProfileId]][["on_change"]][[product_id]][['on_origin_country_change']][[originationCountryId]]
      return(itemdetails_origin_country_change)

      } else if (change == "destination_country") {
        destinationCountryId <- contract_fields[['destinationCountryId']]
        itemdetails_destination_country_change <- data_for_userId[[1]][['data']][[traderUserId]][['itemDetails']][[contractType]][[cpProfileId]][["on_change"]][[product_id]][['on_destination_country_change']][[destinationCountryId]]
        return(itemdetails_destination_country_change)
      }
  }

}

#' @itemsection
#' @serializer unboxedJSON
#' @post /get-recommendation

function(itemsection, productChange, req){
  #########################
  ### Parsing the arguments
  #########################

  post_body <- req$postBody
  post_body_r <- jsonlite::fromJSON(post_body, flatten = TRUE)
  user_id <- post_body_r$userId
  trader_id <- post_body_r$traderUserId

  productChange <- post_body_r$productId
  originCountryChange <- post_body_r$originationCountryId
  destinationCountryChange <- post_body_r$destinationCountryId

  #########################################
  ### Parse the HTTP headers in the request
  #########################################
  contentType = req$HTTP_CONTENT_TYPE
  xTenant = req$HTTP_X_TENANTID
  objectAction = req$HTTP_X_OBJECTACTION
  xLocale = req$HTTP_X_LOCALE
  authToken = req$HTTP_AUTHORIZATION
  app_id = req$HTTP_X_REFID  
  ObjectId = req$HTTP_X_OBJECTNAME

  host_port = "http://192.168.1.225:8484/data/"
  recommendation_object = "recommendation" 
  URL_get_data = paste0(host_port, app_id, "/", recommendation_object, "?userId=", user_id, "&refType=", "app", "&sourceObjectId=", ObjectId)

  raw.result <- GET(url = URL_get_data, add_headers("X-TenantID" = xTenant
                                  , "X-ObjectAction" = objectAction
                                  , "Content-Type" = contentType
                                  ,"Authorization" = authToken))
  data_for_userId <- content(raw.result, "parsed")

  if (itemsection == TRUE){
    if ( ( is.null(productChange) == FALSE & is.null(originCountryChange) == TRUE & is.null(destinationCountryChange) == TRUE) ) {

      print('In the product change only block of code.')
      contract_fields_keys <- c("userId", "traderUserId", "cpProfileId", "contractType", "productId")
      change <- 'product'
      contract_fields <- post_body_r[contract_fields_keys]
      item_details_recommendation <- item_details_on_change(data_for_userId, contract_fields, ObjectId, change)
      return(item_details_recommendation)
      } else if ( ( is.null(productChange) == FALSE & is.null(originCountryChange) == FALSE & is.null(destinationCountryChange) == TRUE) ){

        print('In the product and origin country change block of code.')
        change <- "origin_country"

        contract_fields_keys <- c("userId", "traderUserId", "cpProfileId", "contractType", "productId", "originationCountryId")
        contract_fields <- post_body_r[contract_fields_keys]
        item_details_recommendation <- item_details_on_change(data_for_userId, contract_fields, ObjectId, change)
        return(item_details_recommendation)

        } else if (  ( is.null(productChange) == FALSE & is.null(originCountryChange) == TRUE & is.null(destinationCountryChange) == FALSE) ) {
          print('In the product and destination country change block of code.')
          change <- "destination_country"

          contract_fields_keys <- c("userId", "traderUserId", "cpProfileId", "contractType", "productId", "destinationCountryId")
          contract_fields <- post_body_r[contract_fields_keys]
          item_details_recommendation <- item_details_on_change(data_for_userId, contract_fields, ObjectId, change)
          return(item_details_recommendation)
        } else {
        contract_fields_keys <- c("userId", "traderUserId", "cpProfileId", "contractType")
        contract_fields <- post_body_r[contract_fields_keys]
        item_details_recommendation <- recommend_item_details(data_for_userId, contract_fields, ObjectId)
        return(item_details_recommendation)
      }
  } else {
    general_details_recommendation <- recommend_general_details(data_for_userId, ObjectId, user_id, trader_id)
    return(general_details_recommendation)
  }
}

