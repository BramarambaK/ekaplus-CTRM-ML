
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









    recommendation_for_an_user(contract_data_json, userId,  date_format, app_id , object_name, authToken,  contentType, xTenant, url)