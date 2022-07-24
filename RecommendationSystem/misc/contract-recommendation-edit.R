######################################################################
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


############################################################
### Extract the data for the general details of the contract
############################################################
  
extract_general_contract_details <- function(data, common_user_id, general_details_fields){
  commmon_extracted_field = list()
  
  for (i in general_details_fields){
    j = noquote(i)
    extracted_field <- sapply(data, function(x) x[[i]])
    commmon_extracted_field[[i]] <- unlist(extracted_field[common_user_id])
  }

  general_details_fields_df <- data.frame(sapply(commmon_extracted_field, "length<-", max(lengths(commmon_extracted_field))))
  return(general_details_fields_df)
}


order_data <- function(data, date_format, date_column, date_difference){
  # order the contract dataset by creation date.
  data_ordered <- data[order(data[,date_column], decreasing = TRUE),]
  diff <- 0
  for (i in 1:nrow(data_ordered)){
    diff <- difftime( data_ordered[1, 'issueDate'] , data_ordered[i, 'issueDate'] , units="days")
    if (!is.na(diff) == TRUE){
      if (diff >= date_difference){
        break
      }
      last <- i - 1
    } 
  }

  data_ordered <- data_ordered[1:last, ]
  return(data_ordered)
}

find_most_frequent <- function(data_frame, col_names, last_n){
    most_frequent <- rep(0, length(col_names))
    for (i in 1:length(col_names)){
        most_frequent[i] <- tail(names(sort(table(data_frame[, col_names[i]]), decreasing = FALSE, na.last = TRUE)), last_n)
    }
  return(most_frequent)
}


getDeliveryDates <- function(){
  today <- ymd(Sys.Date())
  Next_month <- today %m+% months(1)
  fromTo <- list(today, Next_month)
  return(fromTo)
}


first_time_user_defaults <- function(itemsection){

    if (itemsection == FALSE){
    recommendation_list = list("contractType" = "P", "cpProfileId" = NA, "applicableLawId" = NA, "arbitrationId" = NA, "incotermId" = 'CIF', "agentProfileId " = NA)
    } else {
      dates = getDeliveryDates()
      
        recommendation_list = list("productId" = NA, "quality" = NA, "itemQtyUnitId" = "QUM-M0-7497", "toleranceType" = "Percentage", "toleranceLevel" = "Buyer" , "tolerance" = NA, 'shipmentMode' = 'vessel', 'originationCountryId' = NA 
        	, 'loadingLocationGroupTypeId' = NA, 'destinationCountryId' = NA, 'destinationLocationGroupTypeId' = NA,  'profitCenterId' = NA, 'strategyAccId' = NA
          ,  pricing = list("priceType" = "Flat", "priceUnit" = "USD/Barrel", "price" = NA)
          , "deliveryFromDate" = dates[[1]], "deliveryToDate" = dates[[2]]
          , latePaymentInterestDetails = list("interestRateType " = "Absolute"))
    }
	return(recommendation_list)
}

########################################################################################
### Create a separate function for the three: law id, arbitration id and the incoterm id
###   Call the function with the relevant inputs based on the post body.
###   Another function for the CP profile and the contract type.
###   
#######################################################################################
first_two_general_defaults <- function(ordered_data, contract_type = NULL, counter_party = NULL){

  if(is.null(contract_type) == FALSE & is.null(counter_party) == TRUE){
        recommended_contract_type = contract_type
        last_contract_with_cp <- subset(ordered_data, contractType == recommended_contract_type , select = c(cpProfileId))
        recommended_counter_party <- find_most_frequent(last_contract_with_cp, 'cpProfileId', 1)


    } else if(is.null(contract_type) == TRUE & is.null(counter_party) == TRUE){
          recommended_contract_type <- find_most_frequent(ordered_data, 'contractType', 1)
          last_contract_with_cp <- subset(ordered_data, contractType == recommended_contract_type , select = c(cpProfileId))
          recommended_counter_party <- find_most_frequent(last_contract_with_cp, 'cpProfileId', 1)
    }


    # recommended_agent_profile <- find_most_frequent(ordered_data, 'agentProfileId', 1)
    # defaults <- list("contractType" = recommended_contract_type, "cpProfileId" = recommended_counter_party,  "agentProfileId" = recommended_agent_profile)
    defaults <- list("contractType" = recommended_contract_type, "cpProfileId" = recommended_counter_party)
    return(defaults)

}

last_three_general_defaults <- function(ordered_data, contract_type, counter_party){

        last_contract_with_cp <- subset(ordered_data, cpProfileId == counter_party , select = c(applicableLawId))
        most_frequent_law_id <- find_most_frequent(last_contract_with_cp, 'applicableLawId', 1)
        ### most_frequent_arbitration_id
        last_contract_with_cp <- subset(ordered_data, cpProfileId == counter_party  , select = c(arbitrationId))
        most_frequent_arbitration_id <- find_most_frequent(last_contract_with_cp, 'arbitrationId', 1)

        ### most_frequent_arbitration_id
        last_contract_with_cp <- subset(ordered_data, cpProfileId == counter_party & contractType == contract_type, select = c(incotermId))
        most_frequent_incoterm_id <- find_most_frequent(last_contract_with_cp, 'incotermId', 1)
        defaults <- list("applicableLawId" = most_frequent_law_id, "arbitrationId" = most_frequent_arbitration_id, "incotermId" = most_frequent_incoterm_id)
        return(defaults)

}

#################################################################################################
### Get the vector of logical values to be used as input for all the subset functions in the code
#################################################################################################
get_logical_vector <- function(input_data_element, input_fields, check_for_value = NULL, match_input = NULL){
  # Will be called for every element in the input data to get_item_details function. And, it will provide a vector of logical vbalues. 
  # The vector can be used in the get_item_details function's for loop to check the conditions. 

  # Arguments:
  #   The element in the list of input data -- input_data_element
  #   The subset vector for which to check for. 

keys <- names(input_fields)

if (is.null(check_for_value) == FALSE) {
	if(check_for_value == FALSE){
    vec <-  rep(NA, length(keys))
  for (i in 1:length(keys)){
    vec[i] <- any((names(input_data_element) == keys[i]) == TRUE)
  }
  return(vec)
  } else if(check_for_value == TRUE){
    vec <-  rep(NA, length(keys))
    for (i in 1:length(keys)){
      vec[i] <- (is.null(input_data_element[[keys[i]]]) == FALSE)
    } 
    return(vec)
    }
} else if (match_input == TRUE){
      vec <-  rep(NA, length(keys))
      for (i in 1:length(keys)){
      vec[i] <- (input_data_element[[keys[i]]] == input_fields[[keys[i]]])

    }
    return(vec)
	}
}

############################################
### Subset function for the itemdetails data 
############################################

get_item_details <- function(input_data,  subset_vec, fields_to_subset_and_select, fields_to_select_from_items){
  
  item_details_list <- list()
  counter <- 0
  #############################################################################
  ### keys for subset_vec and the values for it -- must come from the post body
  ###   Then the  input_fields can be replaced with names from subset_vec
  ###   That will make the vector fields_to_be_recommended redundant too!
  ###   To achieve all this need to parse the argument from the post body in a 
  ###   way that I don't have to hard code all that I want to parse.
  #############################################################################
  contract_fields_keys <- c("traderUserId", "cpProfileId", "contractType")
  contract_fields <- subset_vec[contract_fields_keys]
  
  for ( i in 1:length(input_data)){
    # Check for the keys in the dataset.
      if (all(get_logical_vector(input_data[[i]], input_fields = contract_fields, check_for_value = FALSE)) == TRUE){
          # Check if the keys contain null values.
          if (all(get_logical_vector(input_data[[i]], input_fields = contract_fields, check_for_value = TRUE)) == TRUE){
            if (all(get_logical_vector(input_data[[i]], input_fields = contract_fields, match_input = TRUE)) == TRUE){
              # print("***************************************************************Found item with matching values*************************************************************")
              counter <- counter + 1
              item_details_list[[i]] <- input_data[[i]][["itemDetails"]]
            } else {
              item_details_list[[i]] <- NULL
            }
      } else {
          item_details_list[[i]] <- NULL
      }
    }  else {
      item_details_list[[i]] <- NULL
    }
  }
  print("Total number of common itemdetails found is:")
  print(counter)
  if (counter == 0){
    message = list("error" = "No common item details found for the trader, counterparty and contract type.")
    return(message)
  } else{
    # Remove the NULL values from the item_details_list
    item_details_list <- item_details_list[lengths(item_details_list) != 0]
    return(item_details_list)
    
  }
}


get_item_dataFrame <- function(item_details_list, fields_to_select_from_items){
  
  ##############################################################################################################################################
  ### Create dataframe from the items details -- one for all the pricing entries in the items and one for all other entries in the items details 
  ##############################################################################################################################################
  
  df_list <- list()
  df <- list()
  pricing_df_list <- list()
  pricing_df <- list()
  pricing_names <- c("pricingFormulaId", "priceUnitId", "priceUnit", "fxRate", "priceDf", "priceTypeId", "differentialPriceUnit", "differentialPrice", "payInCurId")
  
  for (i in 1:length(item_details_list)){
    for (j in 1:length(item_details_list[[i]])){
      
      ### Create a list of dataframes. Using the do.call() function.
      names_ <- names(item_details_list[[i]][[j]]$pricing) 
      
      if ((all(pricing_names %in% names_) == TRUE)){
        items_pricing_list <- item_details_list[[i]][[j]]$pricing
        pricing_df_list[[j]] <- t(do.call(rbind, items_pricing_list))
      }
      #######################################################################################################
      ### Remove the pricing from the lists and then apply do.call() over the remaining elements in the list
      #######################################################################################################
      names_ <- names(item_details_list[[i]][[j]])
      
      if ((all(fields_to_select_from_items %in% names_) == TRUE)){

        item_details_list_wdout_pricing <- item_details_list[[i]][[j]][fields_to_select_from_items]
        df_list[[j]] <- t(do.call(rbind, item_details_list_wdout_pricing))
      }
    }
    df_list <- df_list[lengths(df_list) != 0]
    
    tryCatch(
              df[[i]] <- do.call(rbind, df_list)
              , error=function(error_message) { df[[i]] <- NULL }
              )

    tryCatch(pricing_df[[i]] <- do.call(rbind, pricing_df_list), error=function(error_message) { pricing_df[[i]] <- NULL })
  }
  # Remove the NULL values in the list of dataframes
  df <- df[lengths(df) != 0]
  pricing_df <- pricing_df[lengths(pricing_df) != 0]
  # Bind the dataframes in the list into one dataframe
  data_frame_all_items <- ldply(df, data.frame)
  data_frame_pricing <- ldply(pricing_df, data.frame)
  
  # Create a list of the two dataframes to return
  return_data <- list(data_frame_all_items, data_frame_pricing)
  return(return_data)
}



#######################################################################################################
### Create the vectors of fields that has to be recommended -- based on the user input through the API
#######################################################################################################

get_recommendation_for_items <- function(items_details_df, subset_vec){
  # print("********************** To get the items for recommendation ***********************************")
  item_df <- items_details_df[[1]]
  # str(item_df)
  fields_to_be_recommended <- c('productId', 'quality', "itemQty", "itemQtyUnitId", "tolerance", "shipmentMode", "profitCenterId", "strategyAccId", "originationCountryId", "loadingLocationGroupTypeId",  "destinationCountryId", "destinationLocationGroupTypeId")

####################################################################
### Checkpoints:
###   productId
###   quality
###   shipmentMode
###   originationCountryId
### Create fields to be recommended for each of these checkpoints
###################################################################

####################################################################################################################################################################################
### Regular user
###  - Scenario - 1

####################################################################################################################################################################################
# Item                  |       Value                 |      based on   (subset on these fields)                        |         previous or most frequent                        | 
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Product               |           Product           | Cp, contract type                                               |     last contract item from last contract captured
# Quality               |           Quality           | Cp, contract type, product                                      |     last contract item from last contract captured
# Item Quantity         |   Quantity unit value       | Cp, contract type, product, Quality                             |     last contract item from last contract captured
# Tolerance             |          Tolerance          | Cp, contract type, product, Quality                             |     last contract item from last contract captured
# Price Type            |          Price Type         | Cp, contract type, product, Quality                             |     last contract item from last contract captured
# Contract Price        |        Contract Price       | Cp, contract type, product, Quality,Price Type                  |     last contract item from last contract captured
# Transportation mode   |       Transportation mode   | Cp, contract type, product, Quality                             |     last contract item from last contract captured
# Loading Country       |       Loading Country       | Cp, contract type, product, Quality, Transport                  |     last contract item from last contract captured
# Loading Location      |       Loading Location      | Cp, contract type, product, Quality, Transport, Loading Country |     last contract item from last contract captured       
# Discharge Country     |     Discharge Country       | Cp, contract type, product, Quality, Transport                  |     last contract item from last contract captured
# Discharge Location    |      Discharge Location     | Cp, contract type, product, Quality, Transport                  |     last contract item from last contract captured
# Profit centre         |        Profit centre        | Cp, contract type, product, Quality                             |     last contract item from last contract captured
# Strategy              |          Strategy           | Cp, contract type, product, Quality                             |     last contract item from last contract captured
# Secondary Cost        |          null               | 
# 
####################################################################################################################################################################################

###################################################################################################
### Regular user 
###     - Scenario - 2
### Fields should be auto populated based on previous contract item being created with counterparty
### Karthik Aradhya would handle it. 

###################################################################################################
### Regular user 
###     - Scenario - 3
###     Autofill -- two cases:
###          If user changes defaulted Product
###          If user changes Loading Country
### User changes Product:
###   Combinations of below fields has to be provided:
###     Product, Quality, Item Qty Unit, Tolerance, Contract Price Unit, Pay In/Settlement currency, Transport mode, Profit centre Id, Strategy.
###       Even if we have two values each in the remaining 8 fields except productId -- then the number of combinations is 2^8 = 256. This is overwhelming for an user to look through.
### User changes origination country Id:
###   Combinations of below fields has to be provided:
###     Loading location, actual place
### UPDATE: Not to be coded now.
  
  
  # Product, Quality, Item Qty Unit, Tolerance, Contract Price Unit, Pay-In /Settlement Currency, Transportation mode, Profit Centre, Strategy

  recommend_based_on_product <- c("quality", "itemQty", "tolerance", "shipmentMode", "profitCenterId", "strategyAccId")
  recommend_based_on_quality <- c("itemQty", "tolerance",  "shipmentMode", "profitCenterId", "strategyAccId")
  recommend_based_on_shipment <- c("destinationCountryId", "destinationLocationGroupTypeId", "originationCountryId")
  recommend_based_on_originationCountryId <- c("loadingLocationGroupTypeId", "destinationCountryId", "destinationLocationGroupTypeId")

  if ((is.null(subset_vec$originationCountryId) == FALSE)){
      fields_to_select <- c("productId", "quality", "shipmentMode", "originationCountryId", "loadingLocationGroupTypeId")
      
      tryCatch(
                inp_prod <- subset_vec$productId
              , inp_quality <- subset_vec$quality
              , inp_shipment_mode <- subset_vec$shipmentMode
              , inp_origin_country <- subset_vec$originationCountryId

              , error = function(error_message){
                 result = list("error" = "Must pass all of these in input: product, quality, shipment mode, origin country id")
                 return(result)
               }
               )

      data_subset_on_qual_prod_shipment_mode_location <- subset(item_df, productId == inp_prod & quality == inp_quality & shipmentMode == inp_shipment_mode & loadingLocationGroupTypeId == inp_origin_country, select = recommend_based_on_originationCountryId)

      recommendations_based_on_prod_qual_shipment_mode_location <- find_most_frequent(data_frame = data_subset_on_qual_prod_shipment_mode_location, col_names = recommend_based_on_originationCountryId, last_n = 1)
      # recommendation  = data_subset_on_qual_prod_shipment_mode_location[1,]
      return_list <- as.list(setNames(recommendations_based_on_prod_qual_shipment_mode_location, recommend_based_on_originationCountryId))
      return(return_list)

  } else if (is.null(subset_vec$shipmentMode) == FALSE){
    # print("************************************* Shipment mode is provided *************************************")

            fields_to_select <- c("productId", "quality", "shipmentMode", "originationCountryId", "loadingLocationGroupTypeId",  "destinationCountryId", "destinationLocationGroupTypeId")
            most_freq_prod <- subset_vec$productId
            most_freq_quality <- subset_vec$quality
            most_freq_shipment_mode <- subset_vec$shipmentMode
            data_subset_on_qual_prod_shipment_mode <- subset(item_df, productId == most_freq_prod & quality == most_freq_quality & shipmentMode == most_freq_shipment_mode, select = recommend_based_on_shipment)

            recommendations_based_on_prod_qual_shipment_mode <- find_most_frequent(data_frame = data_subset_on_qual_prod_shipment_mode, col_names = recommend_based_on_shipment, last_n = 1)
            return_list <- as.list(setNames(recommendations_based_on_prod_qual_shipment_mode, recommend_based_on_shipment))
            return(return_list)

            } else if ((is.null(subset_vec$shipmentMode) == TRUE) & (is.null(subset_vec$originationCountryId) == TRUE)){

                    if ((is.null(subset_vec$productId) == FALSE) & (is.null(subset_vec$quality) == FALSE)){
                      
                        # print("************************************** Both product and quality are in input *************************************************")
                        fields_to_select <- c("productId", "quality","itemQty", "tolerance",  "shipmentMode", "profitCenterId", "strategyAccId")
                        most_freq_prod <- subset_vec$productId
                        most_freq_quality <- subset_vec$quality
                        recommendations_based_on_prod_qual <- find_most_frequent(data_frame = subset(item_df, quality == most_freq_quality & productId == most_freq_prod, select = recommend_based_on_quality), col_names = recommend_based_on_quality, last_n = 1)
                        return_list <- as.list(setNames(recommendations_based_on_prod_qual, recommend_based_on_quality))
                        return(return_list) 

                    } else if ((is.null(subset_vec$productId) == FALSE) & (is.null(subset_vec$quality) == TRUE)){
                              print("************************************** product is in input *************************************************")
                              # Recomendations should be updated on change of product.
                              ##############################################################################################################################################
                              ### Product, Quality, Item Qty Unit, Tolerance, Contract Price Unit, Pay-In /Settlement Currency, Transportation mode, Profit Centre, Strategy
                              ##############################################################################################################################################
                            
                              most_freq_prod <- subset_vec$productId
                              quality_df_subset_on_product <- subset(item_df, productId == most_freq_prod, select = c(quality))
                              most_freq_quality <- find_most_frequent(data_frame = quality_df_subset_on_product, col_names = 'quality', last_n = 1)
                              
                              data_subset_on_qual_prod <- subset(item_df, quality == most_freq_quality, select = recommend_based_on_product)
                              recommendation_product <- data_subset_on_qual_prod[1, ]
                              return_list <- as.list(setNames(recommendation_product, recommend_based_on_product))
                              return_list[["productId"]] <- subset_vec$productId
                              
                              ########################################
                              ### Pricing object in the recommendation
                              ########################################
                              price_df <- items_details_df[[2]]
                              if (nrow(price_df) == 0){

                                    return_list[["pricing"]] <- list("payInCurId" = NA, "priceUnit" = NA)
                                    return(return_list)

                              } else {

                                    data_frame_all <- qpcR:::cbind.na(price_df,item_df)

                                    subsetted_data <- subset(data_frame_all, productId == subset_vec$productId & quality == most_freq_quality, select = c("priceUnit", "payInCurId"))
                                    price_unit <- find_most_frequent(data_frame = subsetted_data, col_names = "priceUnit", last_n = 1)
                                    pay_in_currency <- find_most_frequent(data_frame = subsetted_data, col_names = "payInCurId", last_n = 1)
                                    
                                    return_list[["pricing"]] <- list("payInCurId" = pay_in_currency, "priceUnit" = price_unit)
                                    return(return_list)

                              }


                   } else if ((is.null(subset_vec$productId) == TRUE) & (is.null(subset_vec$quality) == TRUE)){
                              print('Entered the code block for no prod n quality')
                              # print(item_df)

                              if (all(fields_to_be_recommended %in% names(item_df))){

                                    ### Recommending most of the items details as the user lands on the items page.
                                    most_freq_prod <- find_most_frequent(data_frame = item_df, col_names = 'productId', last_n = 1)
                                    quality_df_subset_on_product <- subset(item_df, productId == most_freq_prod, select = fields_to_be_recommended)
                                    
                                    most_freq_quality <- find_most_frequent(data_frame = quality_df_subset_on_product, col_names = 'quality', last_n = 1)

                                    ### items fields that need to be recommended based on product and quality -- find the most frequent of all of them.
                                    data_subset_on_qual_prod <- subset(quality_df_subset_on_product, quality == most_freq_quality, select = fields_to_be_recommended)
                                    recom_based_on_qual_prod <- find_most_frequent(data_subset_on_qual_prod, col_names = recommend_based_on_quality, last_n = 1)

                                    most_freq_shpmnt_md <- find_most_frequent(data_frame = data_subset_on_qual_prod, col_names = 'shipmentMode', last_n = 1)
                                    data_subset_on_prod_qual_shpMode <- subset(data_subset_on_qual_prod, shipmentMode == most_freq_shpmnt_md,  select = fields_to_be_recommended)
                                    recom_based_on_qual_prod_shpmnt <- find_most_frequent(data_subset_on_prod_qual_shpMode, col_names = recommend_based_on_shipment, last_n = 1)

                                    most_freq_countryt_id <- find_most_frequent(data_frame = data_subset_on_prod_qual_shpMode, col_names = 'originationCountryId', last_n = 1)
                                    data_subset_on_prod_qual_shpMode_country <- subset(data_subset_on_prod_qual_shpMode, originationCountryId == most_freq_countryt_id,  select = fields_to_be_recommended)
                                    recom_based_on_qual_prod_shpmnt_country <- find_most_frequent(data_subset_on_prod_qual_shpMode_country, col_names = 'loadingLocationGroupTypeId', last_n = 1)

                                    recommendations_ <- c(most_freq_prod, most_freq_quality, recom_based_on_qual_prod, recom_based_on_qual_prod_shpmnt, recom_based_on_qual_prod_shpmnt_country)
                                    names_recom <- c("productId", "quality", "itemQty", "tolerance",  "shipmentMode", "profitCenterId", "strategyAccId", "destinationCountryId", "destinationLocationGroupTypeId", "originationCountryId",  "loadingLocationGroupTypeId")
                                    return_list <- as.list(setNames(recommendations_, names_recom))


                                    ########################################
                                    ### Pricing object in the recommendation
                                    ########################################
                                    price_df <- items_details_df[[2]]
                                    # print(price_df)

                                    if (nrow(price_df) == 0) {
                                        return_list[["pricing"]] <- list("priceUnit" = NA, "priceTypeId" = NA, "priceUnitId" = NA)
                                        
                                        ##################
                                        ### Delivery dates
                                        ##################
                                        dates <- getDeliveryDates()
                                        return_list[['deliveryFromDate']] <- dates[[1]]
                                        return_list[['deliveryToDate']] <- dates[[2]]

                                        return(return_list)

                                    } else {
                                              data_frame_all <- qpcR:::cbind.na(price_df,item_df)

                                              subsetted_data <- subset(data_frame_all, productId == most_freq_prod & quality == most_freq_quality, select = c("priceTypeId", "priceUnit", "priceUnitId"))
                                              most_freq_price_type <- find_most_frequent(data_frame = subsetted_data, col_names = "priceTypeId", last_n = 1)
                                              comtract_price_recomm <- find_most_frequent(data_frame = subsetted_data, col_names = "priceUnit", last_n = 1)
                                              comtract_price_unit_recomm <- find_most_frequent(data_frame = subsetted_data, col_names = "priceUnitId", last_n = 1)

                                              return_list[["pricing"]] <- list("priceUnit" = comtract_price_recomm, "priceTypeId" = most_freq_price_type, "priceUnitId" = comtract_price_unit_recomm)

                                              ##################
                                              ### Delivery dates
                                              ##################
                                              dates <- getDeliveryDates()
                                              return_list[['deliveryFromDate']] <- dates[[1]]
                                              return_list[['deliveryToDate']] <- dates[[2]]
                                              return(return_list)

                                    }

                                    } else {

                                      result = list("error" = "Not all items were found in the dataset")


                                    }

                }
        }
}

#################################
### Endpoint for getting the data
#################################

#' @post /fetchData

function(req){
  
    ####################################
    ### Parse contents from request body
    ####################################
    post_body <- req$postBody
    post_body_r <- fromJSON(post_body, flatten = TRUE)
	
  	#########################################
  	### Parse the HTTP headers in the request
  	#########################################
    contentType = req$HTTP_CONTENT_TYPE
    xTenant = req$HTTP_X_TENANTID
    objectAction = req$HTTP_X_OBJECTACTION
    xLocale = req$HTTP_X_LOCALE
    authToken = req$HTTP_AUTHORIZATION

    #####################################################################
    ### Get the url, auth_token etc. from the API call and parse the data
    #####################################################################
    url  <- post_body_r$URL
    raw.result <- GET(url = url, add_headers("X-TenantID" = xTenant
                                    , "X-ObjectAction" = objectAction
                                    , "X-Locale" = xLocale
                                    , "Content-Type" = contentType
                                    ,"Authorization" = authToken))
    contract_data_json <<- content(raw.result, "parsed")
    # str(contract_data_json)
    tryCatch(
              obj <<- sapply(contract_data_json, function(x) x$objectName, simplify=F)
              , msg <<- "Data fetch successful."
              , error=function(error_message){msg <<- "Data fetch unsuccessful."}
              )

    return(msg)
}

#' @itemsection
#' @serializer unboxedJSON
#' @post /recommendation

function(itemsection, req){

    #########################
    ### Parsing the arguments
    #########################

    post_body <- req$postBody
    post_body_r <- fromJSON(post_body, flatten = TRUE)
    user_id <- post_body_r$traderUserId
    
    #############################################
    ### Order the data according to the issueDate
    #############################################
    date_format <- '%Y-%m-%dT%H:%M:%OS%z'
    index_dates <- sapply(contract_data_json, function(x) !all(is.na(as.POSIXct(strptime(x, format = date_format)))))
    # print(index_dates)
    contract_data_json <- contract_data_json[index_dates]
    # length(contract_data_json)
    
    tryCatch(users_contract <- sapply(contract_data_json, function(x) x$traderUserId, simplify=F)
              , error=function(error_message){msg <<- "User id not found."}
              )
    common_user_id <- which(user_id == users_contract)
    # print(unique(users_contract))
    # print('The common users.')
    # print(common_user_id)
    
    itemsection <- noquote(itemsection)
    contract_data_json <- contract_data_json[common_user_id]

    agent_profile <- sapply(contract_data_json, function(x) x$agentProfileId, simplify=F)
    # print("Agent profile Id is :")
    # print(agent_profile)

    if (any(common_user_id, na.rm = TRUE) == TRUE ){
      
      if (itemsection == TRUE){
          print("-----------------------------------------------------items section -----------------------------------------------------------------")
          fields_to_select_from_items <- c('productId', 'quality', "itemQty", "itemQtyUnitId", "tolerance", "shipmentMode", "profitCenterId", "strategyAccId", "originationCountryId"
                                           , "loadingLocationGroupTypeId",  "destinationCountryId", "destinationLocationGroupTypeId",  "valuationFormula")

        
          contract_fields_keys <- c("traderUserId", "cpProfileId", "contractType")
          contract_fields <- post_body_r[contract_fields_keys]
          # print(contract_fields)

          if (NA %in% names(contract_fields)){

              res = list("error" = "Invalid input. Input must contain traderUserId, cpProfileId, contractType")
              return(res)

            } else if (length(unlist(contract_fields)) < 3) {
                      res = list("error" = "Invalid input. Input must contain traderUserId, cpProfileId, contractType")
                      return(res)

              }  else {

                item_details <- get_item_details(contract_data_json, post_body_r, fields_to_subset_and_select, fields_to_select_from_items)
                if ("error" %in% names(item_details)){
                    return(item_details)

                } else{
                  
                    item_df = get_item_dataFrame(item_details, fields_to_select_from_items)
                    get_recommendation_for_items(item_df, post_body_r)
                }

            }

    } else {
          print("--------------------------------------------------general section ----------------------------------------------------------------")
          if (any(common_user_id, na.rm = TRUE) == TRUE){

              general_details_fields <- c("contractType", "traderUserId", "dealType", "cpProfileId", "paymentTermId", "applicableLawId", "arbitrationId", "incotermId", "issueDate", "agentProfileId")
            
              tryCatch(
                        general_fields_df <<- as.data.frame(extract_general_contract_details(contract_data_json, common_user_id, general_details_fields))
                       , error=function(error_message){msg_df <<- list("error" = "General details not found.")}
                       )
            
            print(general_fields_df)
            
            if (exists("general_fields_df")){
                tryCatch(
                          ordered_data <<- order_data(data = general_fields_df, date_format = date_format, date_column = 'issueDate', date_difference = 30)
                         , error=function(error_message){msg_ord <<- list("error" = "General details not found.")}
                         )
              
            } else{
              return(msg_df)
            }

            if ((is.null(post_body_r$contractType) == TRUE) & is.null(post_body_r$cpProfileId) == TRUE){
              ########################################################################################################################################
              ### Write a function for getting the first two fields and then pass the returned field's value to last_three_general_defaults() function
              ### to get the last three. Then pass that as output. 
              ########################################################################################################################################
              
              if (exists("ordered_data")){
                # print(ordered_data)
                defaults_ <- first_two_general_defaults(ordered_data)
                # print(defaults_)
                defaults_last_three <- last_three_general_defaults(ordered_data, contract_type = defaults_[[1]], counter_party = defaults_[[2]])
                c(defaults_, defaults_last_three)
              } else {
                return(msg_ord)
              }

              } else if ((is.null(post_body_r$contractType) == FALSE) & is.null(post_body_r$cpProfileId) == FALSE){
                
                if (exists("ordered_data")){
                  
                  defaults_last_three <- last_three_general_defaults(ordered_data, contract_type = post_body_r$contractType, counter_party = post_body_r$cpProfileId)
                  c(defaults_last_three)
                  
                } else {
                  
                  return(msg_ord)
                }
                
                } else if((is.null(post_body_r$contractType) == FALSE) & is.null(post_body_r$cpProfileId) == TRUE) {

                  defaults_ <- first_two_general_defaults(ordered_data, contract_type = post_body_r$contractType)
                  defaults_last_three <- last_three_general_defaults(ordered_data, contract_type = defaults_[[1]], counter_party = defaults_[[2]])
                  c("cpProfileId" = defaults_[[2]], defaults_last_three)

              }
      } 
    } 
      
  } else {
        print("first time user")
        first_time_user_defaults(itemsection)
    }
}