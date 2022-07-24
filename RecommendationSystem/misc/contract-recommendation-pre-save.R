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
suppressWarnings(suppressMessages(library(base64enc)))
suppressWarnings(suppressMessages(library(RCurl)))

############################################################
### Extract the data for the general details of the contract
############################################################
  
extract_general_contract_details <- function(data, common_user_id, general_details_fields){
  commmon_extracted_field = list()
  for (i in general_details_fields){
    j = noquote(i)
    extracted_field <- sapply(data, function(x) x[[i]])
    commmon_extracted_field[[i]] <- extracted_field
  }
  general_details_fields_df <- as.data.frame(sapply(commmon_extracted_field, "length<-", max(lengths(commmon_extracted_field))))
  return(general_details_fields_df)
}


order_data <- function(data, date_format, date_column, date_difference){
  data_ordered <- data[order(unlist(data[,date_column]), decreasing = TRUE),]
  diff <- 0
  for (i in 1:nrow(data_ordered)){
    diff <- difftime(as.POSIXct(strptime(data_ordered[1, 'issueDate'], format = date_format)) , as.POSIXct(strptime(data_ordered[i, 'issueDate'], format = date_format)), units="days")
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
        most_frequent[i] <- tail(names(sort(table(unlist(data_frame[, col_names[i]])), decreasing = FALSE, na.last = TRUE)), last_n)
    }
  return(most_frequent)
}


getDeliveryDates <- function(){
  today <- ymd(Sys.Date())
  Next_month <- today %m+% months(1)
  today <- strftime(as.POSIXlt(today, "UTC"), "%Y-%m-%dT%H:%M:%S%z")
  Next_month <- strftime(as.POSIXlt(Next_month, "UTC"), "%Y-%m-%dT%H:%M:%S%z")
  fromTo <- list(today, Next_month)
  return(fromTo)
}


first_time_user_defaults <- function(itemsection){
    if (itemsection == FALSE){
    # recommendation_list = list("contractType" = "P", "cpProfileId" = NA, "applicableLawId" = NA, "arbitrationId" = NA, "incotermId" = 'CIF', "agentProfileId " = NA)
    recommendation_list = list("contractType" = "P", "cpProfileId" = NA, "applicableLawId" = NA, "arbitrationId" = NA, "incotermId" = 'CIF', "optional_fields" = list("agentProfileId" = NA))
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
        ###################
        ### Optional fields 
        ###################
        agent_profile_id <- subset(ordered_data, cpProfileId == counter_party & contractType == contract_type, select = c(agentProfileId))
        most_frequent_agent_profile_id <- find_most_frequent(most_frequent_agent_profile_id, "agentProfileId")
        optional_fields <- list("agentProfileId" = most_frequent_agent_profile_id)
        defaults <- list("applicableLawId" = most_frequent_law_id, "arbitrationId" = most_frequent_arbitration_id, "incotermId" = most_frequent_incoterm_id, "optional" = optional_fields)
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

get_item_details <- function(input_data,  subset_vec, fields_to_select_from_items){
  
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
          if (all(get_logical_vector(input_data[[i]], input_fields = contract_fields, check_for_value = TRUE)) == TRUE){
            if (all(get_logical_vector(input_data[[i]], input_fields = contract_fields, match_input = TRUE)) == TRUE){
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
  if (counter == 0){
    message = list("error" = "No common item details found for the trader, counterparty and contract type.")
    return(item_details_list)
  } else if (length(item_details_list) == 0) {
    item_details_list <- NA
  } else{
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
  pricing_names <- c("priceUnitId", "priceDf", "priceTypeId", "payInCurId")
  
  for (i in 1:length(item_details_list)){
    for (j in 1:length(item_details_list[[i]])){
      ### Create a list of dataframes. Using the do.call() function.
      names_ <- names(item_details_list[[i]][[j]]$pricing) 
      names_items <- names(item_details_list[[i]][[j]])
      
      if ((all(pricing_names %in% names_) == TRUE) & (all(fields_to_select_from_items %in% names_items) == TRUE)){
        items_pricing_list <- item_details_list[[i]][[j]]$pricing

        item_details_list_wdout_pricing <- item_details_list[[i]][[j]][fields_to_select_from_items]

        items_pricing_list <- items_pricing_list[lengths(items_pricing_list) != 0]
        item_details_list_wdout_pricing <- item_details_list_wdout_pricing[lengths(item_details_list_wdout_pricing) != 0]

        pricing_names_reduced <- names(items_pricing_list)
        items_names_reduced <- names(item_details_list_wdout_pricing)

        if ((all(pricing_names %in% pricing_names_reduced) == TRUE) & (all(fields_to_select_from_items %in% items_names_reduced) == TRUE)) {

          tryCatch( pricing_df_list[[j]] <- t(do.call(rbind, items_pricing_list))
            , error=function(error_message){pricing_df_list[[j]] <- NA}
            )

          tryCatch(df_list[[j]] <- t(do.call(rbind, item_details_list_wdout_pricing))
            , error=function(error_message){df_list[[j]]  <- NA}
            )
    }
  }
}
    df_list <- df_list[lengths(df_list) != 0]
    pricing_df_list <- pricing_df_list[lengths(pricing_df_list) != 0]

    tryCatch( df[[i]] <- do.call(rbind, df_list)
              , error=function(error_message) { df[[i]] <- NULL})

    tryCatch( pricing_df[[i]] <- do.call(rbind, pricing_df_list)
              , error=function(error_message) { pricing_df[[i]] <- NULL })
  }
  df <- df[lengths(df) != 0]
  pricing_df <- pricing_df[lengths(pricing_df) != 0]

  ###########################################
  ### Have to get this part of the code right
  ###########################################

  ################################################################
  ### Logic for binding the data frames:
  ### Case 0:
  ###   The list is empty.
  ### Case 1:
  ###   There is one element/data frame in the list.
  ### Case 2:
  ###   There is more than one element in the list.

  empty_list_bool <- which(c((length(df) == 0), (length(pricing_df) == 0)))
  if(any(empty_list_bool == TRUE)) {
    return_data <- list(data_frame_all_items = NA, data_frame_pricing = NA)
    return(return_data)
  } else {
    data_frame_all_items <- ldply(df, data.frame)
    tryCatch({data_frame_pricing <- ldply(pricing_df, data.frame)}
      , error= function(error_message) {data_frame_pricing <- NA}
      )
    return_data <- list(data_frame_all_items, data_frame_pricing)
    return(return_data)
  }
}

###############################################################################################################################################################################################
### A function to get recommendation for all the traderUserIds. The recommendations should cover all the cases in the document.
###   Need to find out recommendtion for all the changes possible in product, loadinglocation etc. Is it feasible? 
###   
### Send out the recommendation to an API that will store it in MongoDB

get_general_details_recommendation <- function(contract_data_json, common_user_id, date_format) {

  # general_details_fields <- c("contractType", "traderUserId", "dealType", "cpProfileId", "paymentTermId", "applicableLawId", "arbitrationId", "incotermId", "issueDate")
  general_details_fields <- c("contractType", "traderUserId", "dealType", "cpProfileId", "paymentTermId", "applicableLawId", "arbitrationId", "incotermId", "issueDate", "agentProfileId")
    
  tryCatch(general_fields_df <- extract_general_contract_details(contract_data_json, common_user_id, general_details_fields)
               , error=function(error_message){msg_df <- list("error" = "General details not found.")}
               )
  if (nrow(general_fields_df) <= 1){
    return(unlist(general_fields_df[1,]))
  } else {
    # print('There is more than one general details row.')
    if (exists("general_fields_df")){
      ordered_data <- order_data(data = general_fields_df, date_format = date_format, date_column = 'issueDate', date_difference = 30)

      ########################################################################################################################################
      ### Write a function for getting the first two fields and then pass the returned field's value to last_three_general_defaults() function
      ### to get the last three. Then pass that as output. 
      ########################################################################################################################################
        
      if (exists("ordered_data") & (is.null(ordered_data) == FALSE)){
        if (nrow(ordered_data) < 2){
          # print('Number of rows in ordered data are less than 2.')
          result = c(list( 'dealType' = "Third_Party"
                                      , 'contractType' = unlist(ordered_data[1,'contractType'])
                                      , 'cpProfileId' = unlist(ordered_data[1,'cpProfileId'])
                                      , 'applicableLawId' =  unlist(ordered_data[1,'applicableLawId'])
                                      , 'incotermId' = unlist(ordered_data[1,'incotermId'])
                                      , 'arbitrationId' = unlist(ordered_data[1,'arbitrationId'])
                                      , 'optional_fields' = list('agentProfileId' = unlist(ordered_data[1,'agentProfileId']))))
          return(result)
        } else {
          defaults_ <- first_two_general_defaults(ordered_data)
          defaults_last_three <- last_three_general_defaults(ordered_data, contract_type = defaults_[[1]], counter_party = defaults_[[2]])
          deal_type <- list('dealType' = "Third_Party")
          result <- c(deal_type, defaults_, defaults_last_three)
          return(result)
        }
          } else {
            return(NULL)
        }
      } else {
        return(NULL)
      }
    }
}

###############################################
### Now, the item details page
###############################################

pricing_recommendation <- function(items_details_df, item_df, most_freq_prod, most_freq_quality, product_change) {

  tryCatch( price_df <- items_details_df[[2]], error = function(error_message) {price_df <<- data.frame() })
  if (nrow(price_df) == 0) {
      if (product_change == TRUE) {
        prod_change_recomm <- list("payInCurId" = NA, "priceUnitId" = NA)
        return(prod_change_recomm)
      } else {
        prod_change_recomm <-list("priceDf" = NA, "priceTypeId" = NA, "priceUnitId" = NA) 
        return(prod_change_recomm)
      }
  } else {
    data_frame_all <- qpcR:::cbind.na(price_df,item_df)
    price_names <- c("priceTypeId", "priceDf", "priceUnitId", "payInCurId")
    pricing_df_names <- colnames(price_df)

    if (all(price_names %in% pricing_df_names) == TRUE) {
      subsetted_data <- subset(data_frame_all, productId == most_freq_prod & quality == most_freq_quality, select = c("priceTypeId", "priceDf", "priceUnitId", "payInCurId"))
      most_freq_price_type <- find_most_frequent(data_frame = subsetted_data, col_names = "priceTypeId", last_n = 1)
      comtract_price_recomm <- find_most_frequent(data_frame = subsetted_data, col_names = "priceDf", last_n = 1)
      comtract_price_unit_recomm <- find_most_frequent(data_frame = subsetted_data, col_names = "priceUnitId", last_n = 1)
      comtract_pay_currency_recomm <- find_most_frequent(data_frame = subsetted_data, col_names = "payInCurId", last_n = 1)
      ################################
      ### Logic for pricing data frame
      ################################
      if (product_change == TRUE) {
        prod_change_recomm <- list("payInCurId" = comtract_pay_currency_recomm, "priceUnitId" = comtract_price_unit_recomm)
        return(prod_change_recomm)
      } else {
        if (most_freq_price_type[1] == "Flat") {
                on_load_recomm <- list("priceTypeId" = most_freq_price_type, "priceDf" = comtract_price_recomm, "priceUnitId" = comtract_price_unit_recomm)
                return(on_load_recomm)
        } else {
                return_list <- list("priceTypeId" = most_freq_price_type)
                return(return_list)
        }
      }
    } else {
      if (product_change == TRUE) {
        prod_change_recomm <- list("payInCurId" = NA, "priceUnitId" = NA)
        return(prod_change_recomm)
      } else {
        return_list <- list("priceDf" = NA, "priceTypeId" = NA, "priceUnitId" = NA)
        return(return_list)
      }
    }
  }
}


recommendation_for_all_items_on_load <- function(items_details_df, product_id = NA, origin_country_id = NA, destination_country_id = NA) {

    item_df <- items_details_df[[1]]
    names_df <- colnames(item_df)
    fields_to_be_recommended <- c('productId', 'quality', "itemQty", "itemQtyUnitId", "tolerance", "shipmentMode", "profitCenterId", "strategyAccId", "originationCountryId"
                                  , "loadingLocationGroupTypeId",  "destinationCountryId", "destinationLocationGroupTypeId", "originationCityId", "destinationCityId")

    if (all(fields_to_be_recommended %in% names_df)){
      recommend_based_on_product <- c("quality", "itemQty", "tolerance", "shipmentMode", "profitCenterId", "strategyAccId")
      recommend_based_on_quality <- c("itemQty", "tolerance",  "shipmentMode", "profitCenterId", "strategyAccId")
      recommend_based_on_shipment <- c("destinationCountryId", "originationCountryId")
      recommend_based_on_origination_countryId <- c("loadingLocationGroupTypeId", "originationCityId")
      recommend_based_on_destination_countryId <- c("destinationLocationGroupTypeId", "destinationCityId")

      ###################
      ### Optional fields
      ####################
      recommend_for_optional_fields <- c("inspectionCompany", "laycanEndDate", "laycanStartDate")
      ### Recommending most of the items details as the user lands on the items page.
      ########################
      ### On change of product 
      ########################
      if (is.na(product_id)) {
        most_freq_prod <- find_most_frequent(data_frame = item_df, col_names = 'productId', last_n = 1)
      } else {
        most_freq_prod <- product_id
      }
      quality_df_subset_on_product <- subset(item_df, productId == most_freq_prod, select = fields_to_be_recommended)
      most_freq_quality <- find_most_frequent(data_frame = quality_df_subset_on_product, col_names = 'quality', last_n = 1)

      ### items fields that need to be recommended based on product and quality -- find the most frequent of all of them.
      data_subset_on_qual_prod <- subset(quality_df_subset_on_product, quality == most_freq_quality, select = fields_to_be_recommended)
      recom_based_on_qual_prod <- find_most_frequent(data_subset_on_qual_prod, col_names = recommend_based_on_quality, last_n = 1)

      most_freq_shpmnt_md <- find_most_frequent(data_frame = data_subset_on_qual_prod, col_names = 'shipmentMode', last_n = 1)
      data_subset_on_prod_qual_shpMode <- subset(data_subset_on_qual_prod, shipmentMode == most_freq_shpmnt_md,  select = fields_to_be_recommended)
      recom_based_on_qual_prod_shpmnt <- find_most_frequent(data_subset_on_prod_qual_shpMode, col_names = recommend_based_on_shipment, last_n = 1)

      ##################################
      ### On change of origin country id
      ##################################
      if (is.na(origin_country_id)) {
        most_freq_country_id <- find_most_frequent(data_frame = data_subset_on_prod_qual_shpMode, col_names = 'originationCountryId', last_n = 1)
      } else {
        most_freq_country_id <- origin_country_id
      }
      data_subset_on_prod_qual_shpMode_country <- subset(data_subset_on_prod_qual_shpMode, originationCountryId == most_freq_country_id,  select = fields_to_be_recommended)
      recom_based_on_qual_prod_shpmnt_country <- find_most_frequent(data_subset_on_prod_qual_shpMode_country, col_names = recommend_based_on_origination_countryId, last_n = 1)

      #######################################
      ### On change of destination country id
      #######################################
      if (is.na(destination_country_id)) {
        most_freq_destination_country_id <- find_most_frequent(data_frame = data_subset_on_prod_qual_shpMode, col_names = 'destinationCountryId', last_n = 1)
      } else {
        most_freq_destination_country_id <- destination_country_id
      }
      data_subset_on_prod_qual_shpMode_destination_country <- subset(data_subset_on_prod_qual_shpMode, destinationCountryId == most_freq_destination_country_id,  select = fields_to_be_recommended)
      recom_based_on_qual_prod_shpmnt_destination_country <- find_most_frequent(data_subset_on_prod_qual_shpMode_destination_country, col_names = recommend_based_on_destination_countryId, last_n = 1)

      ###################################################################################################
      ### Return the recommendations based on the input i.e. product, origin country, destination country
      ###################################################################################################
      if (is.na(product_id)) {
        recommendations_ <- c(most_freq_prod, most_freq_quality
                              , recom_based_on_qual_prod
                              , recom_based_on_qual_prod_shpmnt
                              , recom_based_on_qual_prod_shpmnt_country
                              , recom_based_on_qual_prod_shpmnt_destination_country)

        names_recom <- c("productId", "quality"
                          , "itemQty", "tolerance",  "shipmentMode", "profitCenterId", "strategyAccId"
                          , "destinationCountryId", "originationCountryId"
                          ,  "loadingLocationGroupTypeId", "originationCityId"
                          , "destinationLocationGroupTypeId", "destinationCityId")

        return_list <- as.list(setNames(recommendations_, names_recom))
        return_list[["pricing"]] <- pricing_recommendation(items_details_df, item_df, most_freq_prod, most_freq_quality, product_change = FALSE)
        dates <- getDeliveryDates()
        return_list[['deliveryFromDate']] <- dates[[1]]
        return_list[['deliveryToDate']] <- dates[[2]]

        #######################
        ### The optional fields
        ###   inspectionCompany
        ###   laycanEndDate
        ###   latePaymentInterestDetails
        ###     variableType
        ###   optionalLoadingDetails
        ##########################
        tryCatch(recommend_inspection_company <- find_most_frequent(data_subset_on_prod_qual_shpMode_destination_country, col_names = 'inspectionCompany', last_n = 1)
          , error=function(error_message) { recommend_inspection_company <<- NA })
        return_list[["optional_fields"]] <- list("inspectionCompany" = recommend_inspection_company, "laycanEndDate" =  dates[[2]], "laycanStartDate" =  dates[[1]])
        return(return_list)

      } else if ( (is.na(product_id) == FALSE) & (is.na(origin_country_id) == FALSE)){

        recommendations_ <- c(recom_based_on_qual_prod_shpmnt_country)
        names_recom <- c( "loadingLocationGroupTypeId", "originationCityId")
        return_on_origin_change <- as.list(setNames(recommendations_, names_recom))
        return(return_on_origin_change)

      } else if ( (is.na(product_id) == FALSE) & (is.na(destination_country_id) == FALSE)){

        recommendations_ <- c(recom_based_on_qual_prod_shpmnt_destination_country)
        names_recom <- c("destinationLocationGroupTypeId", "destinationCityId")
        return_on_destination_change <- as.list(setNames(recommendations_, names_recom))
        return(return_on_destination_change)

    } else if (  (is.na(product_id) == FALSE) & (is.na(destination_country_id) == TRUE) & (is.na(origin_country_id) == TRUE) ){

      recommendations_ <- c(most_freq_prod, most_freq_quality, recom_based_on_qual_prod)
      names_recom <- c("productId", "quality", "itemQty", "tolerance",  "shipmentMode", "profitCenterId", "strategyAccId")
      return_on_prod_change <- as.list(setNames(recommendations_, names_recom))
      return_on_prod_change[["pricing"]] <- pricing_recommendation(items_details_df, item_df, most_freq_prod, most_freq_quality, product_change = TRUE)
      return(return_on_prod_change)

    } else {
      return_list <- list("productId" = NA, "quality" = NA, "itemQty" = NA, "tolerance" = NA,  "shipmentMode" = NA, "profitCenterId" = NA, "strategyAccId" = NA
        , "destinationCountryId" = NA, "destinationLocationGroupTypeId" = NA, "originationCountryId" = NA,  "loadingLocationGroupTypeId" = NA)
      dates <- getDeliveryDates()
      return_list[['deliveryFromDate']] <- dates[[1]]
      return_list[['deliveryToDate']] <- dates[[2]]
      ###################
      ### Optional fields
      ###################
      return_list[["optional_fields"]] <- list("inspectionCompany" = NA, "laycanEndDate" =  dates[[2]], "laycanStartDate" =  dates[[1]])
      return(return_list)
    }
  }
}

call_general_details_recommendation <- function(user_data, date_format, trader, trader_vec){

  #########################################################
  ### I had assumed that the trader user Id is the user Id.
  ### Now, I got to know that this assumption is not valid.
  ###   Need to use userId instead of traderUserId.
  ###   
  #########################################################
  general_defaults = list()
  user = trader
  users_contract = trader_vec
  idx <- which(user == users_contract)
  user_genereal_details <- list()
  user_data_json <- user_data[idx]

  if (length(user_data_json) ==1){
    user_genereal_details <- c(list('dealType' ="Third_Party", 'contractType' = user_data_json[[1]]$contractType
                                    , 'cpProfileId' = user_data_json[[1]]$cpProfileId
                                    , 'applicableLawId' = user_data_json[[1]]$applicableLawId
                                    , 'incotermId' = user_data_json[[1]]$incotermId
                                    , 'arbitrationId' = user_data_json[[1]]$arbitrationId
                                    , 'optional_fields' = list('agentProfileId' = user_data_json[[1]]$agentProfileId)))

    general_defaults[[user]] <- list(user_genereal_details)

    ######################################
    ### Exit point added here - new change
    ######################################
    return(user_genereal_details)

    } else {
      user_genereal_details <- get_general_details_recommendation(user_data_json, user, date_format)
      if (exists("user_genereal_details")){

        general_defaults[[user]] <- c(list(user_genereal_details))

        ######################################
        ### Exit point added here - new change
        ######################################
        return(user_genereal_details)
      }
    }
  # return(user_genereal_details)

}


create_inputs_for_item_recommendation <- function(user_data) {

  # Create all the combinations of traderUserId, contractType and cpProfileId for recommending the item details.
  tryCatch(users_contract <- sapply(user_data, function(x) x$traderUserId, simplify=F)
            , error=function(error_message){msg <<- "User id not found."}
            )
  unique_traders <- unique(users_contract[lengths(users_contract) != 0])

  tryCatch(cp_profile <- sapply(user_data, function(x) x$cpProfileId, simplify=F)
            , error=function(error_message){msg <<- "User id not found."}
            )
  unique_cp_profiles <- unique(cp_profile[lengths(cp_profile) != 0])
  contract_type <- sapply(user_data, function(x) x$contractType, simplify=F)
  unique_contract_type <- unique(contract_type[lengths(contract_type) != 0])

  ###############################################################################################################
  ### Product Ids for the users. 
  ### Based on the product Ids the recommendations when there is a change in the product can be given. 
  ### Need to configure the same function that computes recommendation for the normal item details case 
  ### Same has to be accomplished for the case when there is a change in the origin location and loading location.
  ################################################################################################################

  itemDetails_all <- sapply(user_data, function(x) x$itemDetails, simplify=T)
  unlist_item_details <- sapply(itemDetails_all, function(x) x[1], simplify=T)
  tryCatch(all_productid <- sapply(unlist_item_details, function(x) x$productId, simplify=F)
            , error=function(error_message){all_productid <<- NA}
            )

  unique_productid <- unique(all_productid[lengths(all_productid) != 0])

  tryCatch(all_origin_country_id <- sapply(unlist_item_details, function(x) x$originationCountryId, simplify=F)
            , error=function(error_message){all_origin_country_id <<- NA}
            )
  all_origin_country_id <- unique(all_origin_country_id[lengths(all_origin_country_id) != 0])
   
  tryCatch(all_destination_country_id <- sapply(unlist_item_details, function(x) x$destinationCountryId, simplify=F)
            , error=function(error_message){all_destination_country_id <<- NA}
            )
  all_destination_country_id <- unique(all_destination_country_id[lengths(all_destination_country_id) != 0])


  list_uniques <- list('traderUserId' = unique_traders, 'contractType' = unique_contract_type, 'cpProfileId' = unique_cp_profiles
                      , 'productId' = unique_productid, 'originationCountryId' = all_origin_country_id, 'destinationCountryId' = all_destination_country_id)

  return(list_uniques)

  # Do a expand.grid over the traderUserId, contract type and cpProfile. Will get a dataframe as a result. Pass that to the call function next.

}

call_item_details_recommendation <- function(user_data, inputs_list, date_format) {

  # Call the get_item_details and get_itemDataFrame on create_inputs_for_item_recommendation for recommending the item details.
  fields_to_select_from_items <- c('productId', 'quality', "itemQty", "itemQtyUnitId", "tolerance", "shipmentMode", "profitCenterId", "strategyAccId", "originationCountryId"
                                            , "loadingLocationGroupTypeId",  "destinationCountryId", "destinationLocationGroupTypeId",  "valuationFormula",  "originationCityId", "destinationCityId")
                                            
  items_recommendation_list <- list()
  items_recomm_list <- list()
  general_details_list <- list()

  unique_traders <- inputs_list[['traderUserId']]
  unique_contract_type <-  inputs_list[['contractType']]
  unique_cp_profiles <- inputs_list[['cpProfileId']]

  unique_prod_ids <- inputs_list[['productId']]
  unique_origin_country_ids <- inputs_list[['originationCountryId']]
  unique_destination_country_ids <- inputs_list[['destinationCountryId']]

  type_recommendation_list <- list()
  trader_recommendation_list <- list()
  cp_recommendation_list <- list()

  for (trader in unique_traders) {
    for (type in unique_contract_type) {
      for (cp in unique_cp_profiles) {
        
        list_uniques <- list('traderUserId' = trader, 'contractType' = type, 'cpProfileId' = cp)
        comb <- expand.grid(list_uniques)
        comb <- comb[1,]

        item_details = get_item_details(user_data, list_uniques, fields_to_select_from_items) 

        if (length(item_details) == 0){
          # cp_recommendation_list[[as.character(cp)]] <- NA
          cp_recommendation_list[[as.character(cp)]] <- list("on_load" = NA)
        } else {
          item_df = get_item_dataFrame(item_details, fields_to_select_from_items)

          item_df <- item_df[lengths(item_df) != 0]
          if (anyNA(item_df)){
            # cp_recommendation_list[[as.character(cp)]] <- NA
            cp_recommendation_list[[as.character(cp)]] <- list("on_load" = NA)
            } else {
              # cp_recommendation_list[[as.character(cp)]] <- recommendation_for_all_items_on_load(item_df)
              # cp_recommendation_list[[as.character(cp)]] <- list("on_load" = recommendation_for_all_items_on_load(item_df))
              #######################################################################################
              ### Try and put the recommendation calculation for the change of product in this block.
              #######################################################################################
              product_recommendation_list <- list()
              origin_country_recommendation_list <- list()
              destination_country_recommendation_list <- list()

              for (prod in unique_prod_ids) {

                for (origin_country in unique_origin_country_ids) {
                  origin_country_recommendation_list[[as.character(origin_country)]] <- recommendation_for_all_items_on_load(item_df, product_id = prod, origin_country_id = origin_country, destination_country_id = NA)
                }

                for (destination_country in unique_destination_country_ids) {
                  destination_country_recommendation_list[[as.character(destination_country)]] <- recommendation_for_all_items_on_load(item_df, product_id = prod, origin_country_id = NA, destination_country_id = destination_country)
                }
                # product_recommendation_list[[as.character(prod)]] <- recommendation_for_all_items_on_load(item_df, product_id = prod, origin_country_id = NA, destination_country_id = NA)
                product_recommendation_list[[as.character(prod)]] <- list("on_product_change" = recommendation_for_all_items_on_load(item_df, product_id = prod, origin_country_id = NA, destination_country_id = NA)
                                                                          , "on_origin_country_change" = origin_country_recommendation_list
                                                                          , "on_destination_country_change" = destination_country_recommendation_list)
              }
              cp_recommendation_list[[as.character(cp)]] <- list("on_load" = recommendation_for_all_items_on_load(item_df), "on_change" = product_recommendation_list)
            }
        }
      }
      type_recommendation_list[[as.character(type)]] <- cp_recommendation_list
    }
    items_recomm_list[['itemDetails']] <- type_recommendation_list
    general_details_recommendation <- call_general_details_recommendation(user_data = user_data, date_format = date_format, trader = trader, trader_vec = unique_traders)
    general_details_list[['generalDetails']] <- general_details_recommendation
    trader_recommendation_list[[as.character(trader)]] <- c(items_recomm_list, general_details_list)
  }
  return(trader_recommendation_list)
}


post_data_to_mongo <- function(refId, url, object, body, xTenant, contentType, authToken){

  ########################################################
  ### First do a GET call. Then see if the data is there. 
  ###   If there is data:
  ###     Do a PUT.
  ###   If data is there:
  ###     Doa POST.
  ########################################################

  # host_port = "http://192.168.1.225:8484/data/"
  recommendation_object = "recommendation" 
  # URL_get_data = paste0(host_port, refId, "/", recommendation_object)

  split_url = unlist(strsplit(url, "[/]"))
  last_two_removed = head(split_url, -2)
  URL_get_data <- paste0(last_two_removed[1], "//", last_two_removed[3], "/", last_two_removed[4], "/", refId, "/", recommendation_object)
  # url_post_data = paste0(host_port, refId, "/", recommendation_object)

  # "http://192.168.1.225:8484/data/5d907cd2-7785-4d34-bcda-aa84b2158415/contract"

  print(URL_get_data)
  raw.result <- GET(url = URL_get_data, add_headers("X-TenantID" = xTenant
                                  , "X-ObjectAction" = "READ"
                                  , "Content-Type" = contentType
                                  ,"Authorization" = authToken))
  general_details_recommendation <<- content(raw.result, "parsed")

  ################################################################################
  ### If there is no data in return of the GET API call:
  ###   Do a POST for all the userIds.
  ### If there is data in the API call then:
  ###   Look for the combination of the userId and the sourceObjectId:
  ###     If there already is a combination in the returned data from the API call
  ###       Do a PUT for that user.
  ###     If there is no combination of the userId and sourceObjectId in the data:
  ###       Do a POST for that user.
  #################################################################################

  ##############################################
  ### Extract the userIds and the sourceObjectId
  ##############################################
  userId_in_data <- sapply(general_details_recommendation, function(x) x$userId, simplify=F)
  sourceObjectId_in_data <- sapply(general_details_recommendation, function(x) x$sourceObjectId, simplify=F)
  Id_in_data <- sapply(general_details_recommendation, function(x) x$`_id`, simplify=F)
  log_vec <- sapply(general_details_recommendation, function(x) body['userId'] %in% x$userId, simplify=F)

  ###########################
  ### Do the condition checks
  ###########################
  # host_port = "http://192.168.1.225:8484/data/"
  # recommendation_object = "recommendation" 
  
  if(all((body['userId'] %in% userId_in_data) & (body['sourceObjectId'] %in% sourceObjectId_in_data))){
    data_common_object <- sapply(general_details_recommendation, function(x) x[body['sourceObjectId'] %in% x$sourceObjectId], simplify=F)
    data_common_user_id <- sapply(data_common_object, function(x) x[body['userId'] %in% x$userId], simplify=F)
    data_common_user_id <- data_common_user_id[lengths(data_common_user_id)!=0]
    Id_in_data <- sapply(data_common_user_id, function(x) x$`_id`, simplify=F)
    # PUT
    body[['_id']] <- unlist(Id_in_data)
    id_put <- body[['_id']]
    # URL_put_data = paste0(host_port, refId, "/",recommendation_object , "/" , id_put)
    URL_put_data = paste0(URL_get_data, "/" , id_put)

    result  <- rjson::toJSON(body, indent=0, method="C" )
    headers_put <- add_headers("X-TenantID" = xTenant
                            , "X-ObjectAction" = 'UPDATE'
                            , "Content-Type" = contentType
                            ,"Authorization" = authToken)

    res <- PUT(url = URL_put_data
              ,config = headers_put
              , body = result, verbose())
  } else {
    print("Posting data for the user:")
    # print()
    result  <- rjson::toJSON(body, indent=0, method="C" )
    # url_post_data = paste0(host_port, refId, "/",recommendation_object)
    url_post_data = URL_get_data
    res <- POST(url = url_post_data
              ,add_headers("X-TenantID" = xTenant
                            , "X-ObjectAction" = 'CREATE'
                            , "Content-Type" = contentType
                            ,"Authorization" = authToken)
              , body = result, verbose())
  }
}

recommendation_for_an_user <- function(contract_data_json, user, date_format, app_id, object_name, authToken, contentType, xTenant, data_url) {

  tryCatch(user_ids <- sapply(contract_data_json, function(x) x$userId, simplify=F)
            , error=function(error_message){msg <<- "User id not found."})

  unique_users_contract_data <- unique(user_ids[lengths(user_ids) != 0])
  print(user_ids)

  idx <- which(user == unique_users_contract_data)
  user_genereal_details <- list()
  user_data <- contract_data_json[idx]

  ########################################################
  ### get recommendations for the general and item details
  ########################################################

  input_data_comb <- create_inputs_for_item_recommendation(user_data)
  item_details <- call_item_details_recommendation(user_data, input_data_comb, date_format)
  ################################################################################################################################
  ### Another change:
  ###     Enable the code to run only for a particular userId instead running for all the userIds. Just parse data for one userId.
  ###       This can be achieved once I get a handle on getting the data right.
  ################################################################################################################################
  recommendations_user <- list("userId" = user, "sourceRefId" = app_id, "sourceObjectId" = object_name, "data" = item_details)
  # post_data_to_mongo(refId = app_id, url = data_url,  object = object_name, body = recommendations_user, xTenant = xTenant, contentType = contentType, authToken = authToken)
  # refId, url, object, body, xTenant, contentType, authToken
  post_data_to_mongo(refId = app_id, url = data_url,  object = object_name, body = recommendations_user, xTenant = xTenant, contentType = contentType, authToken = authToken)
  return(recommendations_user)
}

recommendation_for_all_users <- function(contract_data_json, date_format, app_id, object_name, authToken, contentType, xTenant, data_url){
  ####################################################################
  ### Have to call general details recommendation for all the user ids
  ####################################################################

  tryCatch(user_ids <- sapply(contract_data_json, function(x) x$userId, simplify=F)
            , error=function(error_message){msg <<- "User id not found."})
  unique_users_contract_data <- unique(user_ids[lengths(user_ids) != 0])
  print('The unique user Ids in the data.')
  print(unique_users_contract_data)
  recommendations_all_user <- list()
  recommendation_vec <- list()

  for (i in 1:length(unique_users_contract_data)){
    user <- unique_users_contract_data[[i]]
    idx <- which(user == user_ids)
    user_genereal_details <- list()
    user_data <- contract_data_json[idx]

    ########################################################
    ### get recommendations for the general and item details
    ########################################################

    input_data_comb <- create_inputs_for_item_recommendation(user_data)
    item_details <- call_item_details_recommendation(user_data, input_data_comb, date_format)
    ################################################################################################################################
    ### Another change:
    ###     Enable the code to run only for a particular userId instead running for all the userIds. Just parse data for one userId.
    ###       This can be achieved once I get a handle on getting the data right.
    ################################################################################################################################
    recommendations_user <- list("userId" = user, "sourceRefId" = app_id, "sourceObjectId" = object_name, "data" = item_details)
    # post_data_to_mongo(refId = app_id, url = data_url, object = object_name, body = recommendations_user, xTenant = xTenant, contentType = contentType, authToken = authToken)
    recommendations_all_user[[user]] <- recommendations_user
  }
  return(recommendations_all_user)
}

#################################
### Endpoint for getting the data
#################################

#' @post /calculate-recommendation

function(req){
  
    ####################################
    ### Parse contents from request body
    ####################################
    post_body <- req$postBody
    post_body_r <- jsonlite::fromJSON(post_body)
	
  	#########################################
  	### Parse the HTTP headers in the request
  	#########################################
    contentType = req$HTTP_CONTENT_TYPE
    xTenant = req$HTTP_X_TENANTID
    objectAction = req$HTTP_X_OBJECTACTION
    xLocale = req$HTTP_X_LOCALE
    authToken = req$HTTP_AUTHORIZATION
    app_id = req$HTTP_X_REFID  
    object_name = req$HTTP_X_OBJECTNAME
    print(app_id)
    print(object_name)
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
    tryCatch(obj <<- sapply(contract_data_json, function(x) x$objectName, simplify=F)
              , msg <<- "Data fetch successful."
              , error=function(error_message){msg <<- "Data fetch unsuccessful."})
    print(msg)
    date_format <- '%Y-%m-%dT%H:%M:%OS%z'
    index_dates <- sapply(contract_data_json, function(x) !all(is.na(as.POSIXct(strptime(x, format = date_format)))))
    contract_data_json <- contract_data_json[index_dates]
    userId <- post_body_r$userId
    # recommendation_for_all_users(contract_data_json, date_format, app_id, object_name,  authToken, contentType, xTenant)
    # recommendation_for_all_users(contract_data_json, date_format, app_id, object_name,  authToken, contentType, xTenant, url)
    recommendation_for_an_user(contract_data_json, userId,  date_format, app_id , object_name, authToken,  contentType, xTenant, url)
}

