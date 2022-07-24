"""Anomaly detection using PCA.
Created on Fri Dec  6 11:12:02 2019
@author: amitabh.gunjan
Anomaly detection implementation from the paper:
http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.66.299&rep=rep1&type=pdf
Steps:
Perform PCA over the data.
Use the anomaly detection logic to get the anomalies after doing PCA.
Create a function to get the metrics related to the classification.
Conditions to be met to make the anomaly detection run:
All the classes of all the variables must have an example in the training dataset,
which is a dataset of normal examples.
But, suppose a new example arrives with an unknown class for one or more variables
then how do we plan to counter that?
Need an answer for this. More of a data engineering problem.
"""
import os
import json
import _pickle as cPickle
import numpy as np
import pandas as pd
from pandas import json_normalize
from sklearn.decomposition import PCA
from statsmodels.distributions.empirical_distribution import ECDF  

test_data_path = None

def get_dataframe(train_data):
    """Get pandas dataframe from loaded data."""
    train_data = json_normalize(train_data)
    train_data_df = pd.DataFrame(train_data)
    train_data_df = pd.get_dummies(train_data_df)
    return train_data_df

def save_cols_val(data, cols_data_path):
    """Save the columns values from the input pandas dataframe."""
    col_vals = {"train_X_cols":data.columns.values}
    with open(cols_data_path, 'wb') as cols_file:
        cPickle.dump(col_vals, cols_file)
        cols_file.close()

def reindex_cols(test_data, cols_val):
    """Reindex the columns from the test data using the cols vals from the training data."""
    cols_val_list = list(cols_val['train_X_cols'])
    data_reindexed = test_data.reindex(columns=cols_val_list, fill_value=0)
    return data_reindexed

def fit_pcc(train_data):
    """Fit the principal component classifier."""
    pca = PCA()
    fit = pca.fit(train_data)
    return fit

def get_standardized_scores(coordinates, evals):
    """Get the standardized scores for the transformed data."""
    with np.errstate(divide='ignore', invalid='ignore'):
        square_ratio = np.true_divide(coordinates, evals)
        square_ratio[square_ratio == np.inf] = 0
        square_ratio = np.nan_to_num(square_ratio)
        sum_squared_ratio = np.sum(square_ratio)
    return sum_squared_ratio

def get_empirical_distribution(train_data, fit):
    """ Get the empirical quantiles of the sum of ratio of principal component 
    scores and the eigenvalues using the observations from the training dataset."""
    evals = fit.explained_variance_
    # Workaround for the eigenvalue being quite near to zero.
    evals = [i if np.isclose(0, i) == False else 0 for i in evals]
    ss_standardized_prcomp_scores = []
    train_data = train_data.fillna(0)
    fit_transform = fit.transform(train_data)
    # Try and get the eigenvectors
    for i in fit_transform:
        coordinates_squared = np.square(i)
        ss_prcomp_scores = get_standardized_scores(coordinates_squared, evals)
        ss_standardized_prcomp_scores.append(ss_prcomp_scores)
    return ss_standardized_prcomp_scores

#########################
### Save and load objects
#########################

def write_ecdf(ecdf):
    """Write the ecdf to disk."""
    with open(ecdf_save_path, 'wb') as ecdf_file:
        cPickle.dump(ecdf, ecdf_file)
        ecdf_file.close()

def write_fit_object(fit):
    """Write the ecdf to disk."""
    with open(model_fit_save_path, 'wb') as model_file:
        cPickle.dump(fit, model_file)
        model_file.close()

def load_model_fit(model_fit_save_path):
    """Load the ecdf from disk."""
    with open(model_fit_save_path, 'rb') as model_file:
        model = cPickle.load(model_file)
        model_file.close()
    return model

def load_cols_data(cols_data_path):
    """Load the columns values from disk."""
    with open(cols_data_path, 'rb') as cols_file:
        cols_val = cPickle.load(cols_file)
        cols_file.close()
    return cols_val

def load_train_data(train_data_path):
    """Load the training data"""
    with open(train_data_path, encoding='utf-8') as data_file:
        train_data = json.loads(data_file.read())
    return train_data

def write_model_files(model_objects, path):
    """Write the model files of the PCA based anomaly detection."""
    with open(path, 'wb') as model_file:
        cPickle.dump(model_objects, model_file)
        model_file.close()

def model_and_cols_path(conf_contents):
    """Make the required directories for saving the model files."""
    model_dir = conf_contents['model_path']
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
    model_fit_save_path = model_dir + '/model_files.dat'
    cols_data_path = model_dir + '/cols_data.dat'
    return model_fit_save_path, cols_data_path

def remove_nested_str(input_data):
    """Augment data with the userId so that userid could be used as an independent variable. Also remove the empty dictionaries from the container"""
    input_data_new = []
    for data in input_data:
        data = {i:j for i,j in data.items() if isinstance(j,dict) != True}
        data = {i:j for i,j in data.items() if isinstance(j,list) != True}
        input_data_new.append(data)
    return input_data_new

#############################
### Train the model.
#############################

# def train_anomaly_detection_model(train_data, conf_contents):
#     """Train the anomaly detection model."""
#     model_fit_save_path, cols_data_path = model_and_cols_path(conf_contents)
#     train_data = remove_nested_str(train_data)
#     x_train = get_dataframe(train_data)
#     save_cols_val(x_train, cols_data_path)
#     x_train = pd.DataFrame.fillna(x_train, value=0)
#     fit = fit_pcc(train_data=x_train)
#     ecdf = get_empirical_distribution(train_data=x_train, fit=fit)
#     model_objects = {"ecdf":ecdf, "fit":fit}
#     write_model_files(model_objects=model_objects, path=model_fit_save_path)

def train_anomaly_detection_model(train_data):
    """Train the anomaly detection model."""
    train_data = remove_nested_str(train_data)
    x_train = get_dataframe(train_data)
    col_vals = {"train_X_cols":x_train.columns.values}
    x_train = pd.DataFrame.fillna(x_train, value=0)
    fit = fit_pcc(train_data=x_train)
    ecdf = get_empirical_distribution(train_data=x_train, fit=fit)
    model_objects = {"ecdf":ecdf, "fit":fit, 'cols_data':col_vals}
    return model_objects

############################################
### Load test data and perform anomaly check
############################################

# def load_test_data(cols_data_path, input_data=None):
#     """Load the test data for checking anomalies."""
#     if input_data is None:
#         with open(test_data_path, encoding='utf-8') as data_file:
#             test_data = json.loads(data_file.read())
#     else:
#         test_data = input_data
#     test_data = json_normalize(test_data)
#     test_data_df = pd.DataFrame(test_data)
#     test_data_dummies = pd.get_dummies(test_data_df)
#     cols_val = load_cols_data(cols_data_path)
#     test_data_dummies = reindex_cols(test_data=test_data_dummies, cols_val=cols_val)
#     return test_data_dummies, test_data_df

def load_test_data(cols_data, input_data=None):
    """Load the test data for checking anomalies."""
    if input_data is None:
        with open(test_data_path, encoding='utf-8') as data_file:
            test_data = json.loads(data_file.read())
    else:
        test_data = input_data
    test_data = json_normalize(test_data)
    test_data_df = pd.DataFrame(test_data)
    test_data_dummies = pd.get_dummies(test_data_df)
    test_data_dummies = reindex_cols(test_data=test_data_dummies, cols_val=cols_data)
    return test_data_dummies, test_data_df

def get_quantiles_from_ecdf(ss_prcomp_scores, test_prcomp_scores):
    """Compare an observation's sum of ratio of principal component scores
    and the eigenvalues using the observations from the training dataset
    to the empirical quantiles. """
    if len(ss_prcomp_scores) > 3:
        num_major_comps = len(ss_prcomp_scores)//3
    else:
        num_major_comps = 1
    # print(ss_prcomp_scores)
    major_comp_scores = ss_prcomp_scores[0:num_major_comps]
    minor_comp_scores = ss_prcomp_scores[num_major_comps:]
    # print(f"The major comp scores are : {major_comp_scores}")
    ecdf_major = ECDF(major_comp_scores)
    quantile_major = ecdf_major(test_prcomp_scores)
    ecdf_minor = ECDF(minor_comp_scores)
    quantile_minor = ecdf_minor(test_prcomp_scores)
    return quantile_major, quantile_minor

def get_anomalies_indices(test_prcomp_scores, saved_prcomp_scores):
    """Get the quantiles for the test observations."""
    quantile_major, quantile_minor = get_quantiles_from_ecdf(ss_prcomp_scores=saved_prcomp_scores, test_prcomp_scores=test_prcomp_scores)
    # print("The quantile scores -------------\n", quantile_major, quantile_minor)
    anomalies_major = [i > 0.9899 for i in quantile_major]
    anomalies_minor = [i > 0.9899 for i in quantile_minor]
    return anomalies_major, anomalies_minor

def get_quantiles_major_minor(test_prcomp_scores, saved_prcomp_scores):
    """Get the quantiles for the test observations."""
    quantile_major, quantile_minor = get_quantiles_from_ecdf(ss_prcomp_scores=saved_prcomp_scores, test_prcomp_scores=test_prcomp_scores)
    return quantile_major, quantile_minor

def most_variability_fields(model_fit):
    """Get the fields with the most variability.
    From fit.transform() the answer could be found for getting the 
    importance of the variables in the original data. 
    You have k eigenvectors - k is the number of data points on which 
    the model has been trained. So we have k eigenvalues and k eigen
    vectors. Now, each data point is multiplied by the k eigenvectors 
    to get the coordinates in the data space. Coordinates are k length 
    vectors in k-dimensional space.
    What can be done is:
    Sum the eigenvectors element-wise and get one vector. Find out the
    elements with highest magnitude from this vector and just pick the 
    variables that get multiplied to these eigenvectors from the input.
    These are the variables that will be responsible for the maximum
    variability in the data. Try this and see what happens and also go 
    through the paper which is implemented.
    Also look at the loadings. They are the regression coefficients 
    when doing multiple linear regression of data matrix on the eigenvectors."""
    fit = model_fit['fit']
    cols_val = model_fit['cols_data']
    eigenvectors = fit.components_
    eigenvalues = fit.explained_variance_
    # print(f"The eigenvalues :\n {eigenvalues}")
    max_ = max(eigenvalues)
    eval_sorted = sorted(eigenvalues)
    if len(eval_sorted) > 4:
        len_ = len(eigenvalues)//4
        val = eval_sorted[-len_]
    else:
        val = eval_sorted[-1]
    positive_evals = [i >= val for i in eigenvalues]
    # print(f"Positive evals:\n {positive_evals}")
    meaningful_evectors = eigenvectors[positive_evals]
    cols_val_list = list(cols_val['train_X_cols'])
    # print("Columns from training data :\n", cols_val_list)
    meaningful_evectors = [abs(i) for i in meaningful_evectors]
    max_indices = [list(i).index(max(i)) for i in meaningful_evectors]
    max_variance_vars = [cols_val_list[i] for i in max_indices]
    max_variance_vars = list(set([i.split("_")[0] for i in max_variance_vars]))
    # print(f"Max variance vars :\n {max_variance_vars}")
    return max_variance_vars

def check_for_anomaly(anomalies_major, anomalies_minor):
    """Check for anomalies."""
    anomalies_ = []
    for i in range(len(anomalies_major)):
        if anomalies_major[i]==True:
            anomalies_.append(True)
        elif anomalies_minor[i]==True:
            anomalies_.append(True)
        else:
            anomalies_.append(False)
    return anomalies_

def filter_anomalies(test_data, anomalies):
    """Filter anomalies from the test data using the indices from check for anomaly function."""
    anomalous_data = test_data.loc[anomalies]
    anomalous_data = anomalous_data.to_json(orient='records')
    anomalous_data = json.loads(anomalous_data)
    return anomalous_data

# def detect_anomaly(data, conf_contents):
#     """Check for anomalies from observed quantiles."""
#     model_fit_save_path, cols_data_path = model_and_cols_path(conf_contents)
#     # print(f"The model path {model_fit_save_path}, and data path {cols_data_path}")
#     test_data_dummies, test_data_df = load_test_data(input_data=data, cols_data_path=cols_data_path)
#     # print(f"The test data is : {test_data_df}")
#     model_fit = load_model_fit(model_fit_save_path)
#     # print(f"The model fir is : {model_fit}")
#     fit = model_fit['fit']
#     saved_prcomp_scores = model_fit['ecdf']
#     test_prcomp_scores = get_empirical_distribution(train_data=test_data_dummies, fit=fit)
#     anomalies_major, anomalies_minor = get_anomalies_indices(test_prcomp_scores=test_prcomp_scores, saved_prcomp_scores=saved_prcomp_scores)
#     # print("Tha anomalies scores ---------\n", anomalies_major, anomalies_minor)
#     anomalies = check_for_anomaly(anomalies_major=anomalies_major, anomalies_minor=anomalies_minor)
#     anomalous_data = filter_anomalies(test_data=test_data_df, anomalies=anomalies)
#     return anomalous_data


def detect_anomaly(data, model_fit):
    """Check for anomalies from observed quantiles."""
    fit = model_fit['fit']
    saved_prcomp_scores = model_fit['ecdf']
    cols_data = model_fit['cols_data']
    test_data_dummies, test_data_df = load_test_data(cols_data, input_data=data)
    test_prcomp_scores = get_empirical_distribution(train_data=test_data_dummies, fit=fit)
    anomalies_major, anomalies_minor = get_anomalies_indices(test_prcomp_scores=test_prcomp_scores, saved_prcomp_scores=saved_prcomp_scores)
    # print(f"The anomalies scores are:\n Major scores:\n {anomalies_major} \n Minor anomaly scores \n {anomalies_minor}")
    anomalies = check_for_anomaly(anomalies_major=anomalies_major, anomalies_minor=anomalies_minor)
    anomalous_data = filter_anomalies(test_data=test_data_df, anomalies=anomalies)
    return anomalous_data

def append_anomalies(test_data, major_anomaly_scores, minor_anomaly_scores):
    """Filter anomalies from the test data using the indices from check for anomaly function."""
    anomalous_data = test_data.assign(anomalies_major_score=pd.Series(major_anomaly_scores).values)
    anomalous_data = anomalous_data.assign(anomalies_minor_score=pd.Series(minor_anomaly_scores).values)
    anomalous_data = anomalous_data.to_json(orient='records')
    anomalous_data = json.loads(anomalous_data)
    return anomalous_data

# def attach_anomaly_scores(data, conf_contents):
#     """Attach the major and minor Quantile scores of a new observation 
#     to the input data and return the same."""
#     model_fit_save_path, cols_data_path = model_and_cols_path(conf_contents)
#     test_data_dummies, test_data_df = load_test_data(input_data=data, cols_data_path=cols_data_path)
#     model_fit = load_model_fit(model_fit_save_path)
#     fit = model_fit['fit']
#     saved_prcomp_scores = model_fit['ecdf']
#     test_prcomp_scores = get_empirical_distribution(train_data=test_data_dummies, fit=fit)
#     anomalies_major, anomalies_minor = get_quantiles_major_minor(test_prcomp_scores=test_prcomp_scores, saved_prcomp_scores=saved_prcomp_scores)
#     test_data_significant_vars = identify_significant_variables(test_prcomp_scores, saved_prcomp_scores, test_data_dummies, fit, test_data_df, cols_data_path)
#     augmented_data = append_anomalies(test_data=test_data_significant_vars, major_anomaly_scores=anomalies_major, minor_anomaly_scores=anomalies_minor)
#     return augmented_data

def attach_anomaly_scores(data, model_fit):
    """Attach the major and minor Quantile scores of a new observation 
    to the input data and return the same."""
    fit = model_fit['fit']
    saved_prcomp_scores = model_fit['ecdf']
    cols_data = model_fit['cols_data']
    test_data_dummies, test_data_df = load_test_data(cols_data, input_data=data)
    test_prcomp_scores = get_empirical_distribution(train_data=test_data_dummies, fit=fit)
    anomalies_major, anomalies_minor = get_quantiles_major_minor(test_prcomp_scores=test_prcomp_scores, saved_prcomp_scores=saved_prcomp_scores)
    test_data_significant_vars = identify_significant_variables(test_prcomp_scores, saved_prcomp_scores, test_data_dummies, fit, test_data_df, model_fit)
    augmented_data = append_anomalies(test_data=test_data_significant_vars, major_anomaly_scores=anomalies_major, minor_anomaly_scores=anomalies_minor)
    # print(f"The augmented data is {augmented_data}")
    return augmented_data

def append_significant_vars(test_data):
    """Filter anomalies from the test data using the indices from check for anomaly function."""
    anomalous_data = test_data.assign(significant_variables=pd.Series(major_anomaly_scores).values)
    anomalous_data = anomalous_data.to_json(orient='records')
    anomalous_data = json.loads(anomalous_data)
    return anomalous_data

def identify_significant_variables(test_prcomp_scores, saved_prcomp_scores, test_data_dummies, fit, test_data_df, model_fit):
    """Identify the variables in the sole data point that makes the data point anomaly."""
    _major_indicator, _minor_indicator = get_anomalies_indices(test_prcomp_scores, saved_prcomp_scores)
    major_anomaly_data = test_data_dummies[_major_indicator]
    minor_anomaly_data = test_data_dummies[_minor_indicator]
    eigen_vectors = fit.components_
    eigen_vals = fit.explained_variance_
    eigen_vals = [ i if i > 1.0 else 0 for i in eigen_vals ]
    # eigen_vals = eigen_vals[eigen_vals_indices]
    # print("The eigen values -----------------\n", eigen_vals)
    list_of_major_multiples = [np.multiply(major_anomaly_data, evectors) for evectors in eigen_vectors]
    list_of_minor_multiples = [np.multiply(minor_anomaly_data, evectors) for evectors in eigen_vectors]
    """
    From the test prcomp scores I get to figure out the the anomalies major and anomalies minor.
    Then based on the anomalies major minor score, one gets to know the kind of anomaly they are dealing with.
    Based on the kind of anomaly one needs to check the fit.transform(test data) method, and the values that are
    generated when multiplying the eigenvectors with the test data row. From here, out of the total variables
    that possibly could cause an anomaly based on the training data I can narrow down the ones that actually caused
    the data to be an anomaly.
    Must look into the elements of fit.transform() after multiplication and before addition. Basically look at the mid-dot-product.
    Used np.multiply() -- returns an element wise multiplication.
    Must inspect the elements of fit.transform(test data) result.
    I also need to look into the other variables that could have caused an anomaly even when it was not in the possible
    variables that could have caused an anomaly based on training data solely.

    Significant variables that render the data as major anomaly
    Significant variables that render the data as minor anomaly
    
    List of multiples ------------ list_of_major_multiples
    [          amount       amount2  userId  Period_  _id_id  contactName_  ...  sys__createdOn_  sys__data__state_  sys__updatedBy_  sys__updatedOn_  sys__version_  toPeriod_2019-11-16T05:30:00.000+05:30
    0      -0.726007 -7.699770e+01     0.0      0.0     0.0           0.0  ...              0.0                0.0              0.0              0.0            0.0                                     0.0
    1 -695113.439549 -7.996761e+03     0.0      0.0     0.0           0.0  ...              0.0                0.0              0.0              0.0            0.0                                     0.0
    2      -7.646248 -6.999862e+06     0.0      0.0     0.0           0.0  ...              0.0                0.0              0.0              0.0            0.0                                     0.0
    3      -0.718284 -1.127666e+04     0.0      0.0     0.0           0.0  ...              0.0                0.0              0.0              0.0            0.0                                     0.0
    4      -5.174734 -1.209734e+05     0.0      0.0     0.0           0.0  ...              0.0                0.0              0.0              0.0            0.0                                     0.0
    5     -52.442451 -1.747648e+04     0.0      0.0     0.0           0.0  ...              0.0                0.0              0.0              0.0            0.0                                     0.0
    6    -524.424514 -7.699770e+01     0.0      0.0     0.0           0.0  ...              0.0                0.0              0.0              0.0            0.0                                     0.0
    7     -86.503013 -7.699770e+01     0.0      0.0     0.0           0.0  ...              0.0                0.0              0.0              0.0            0.0                                     0.0

    Sum of all the elements in the rows corresponds to one coordinate in the space spanned by the eigenvectors. So, one thumb rule/heuristic
    that can be used to pin point the major/significant variable that renders this data as anomaly could be the proportion contributed to the 
    sum (sum is basically the corrdinate along that eigenvector) by the variable. Only look at the eigenvectors corresponding to the largest 
    eigenvalues or eigenvalues greater than zero.

    What can be gleaned?
        Significant fields contributing to anomalies major score and minor score.

    A list of n data frames where n is the number of eigenvectors.
    For each data frame:
        Take the same row out from the data frame
        Add element-wise and get one row/array of element-wise sums.
        Find the element that contributes most to the total sum of the array.
        Point out the column name that corresponds to the element with most contribution to the sum.
        Use that variable as the main contributor to the major/minor anomaly score.
    """
    def get_row(df, i):
        """Get the nth row from all the data frames."""
        arr_i = abs(df.iloc[i].values)
        return arr_i

    def get_sum_rows(arr_list):
        """Get the sum of numpy arrays from the list of arrays."""
        arr_sum = np.sum(arr_list, axis=0)
        return arr_sum

    def get_significant_contributor(arr, key):
        """"Get the variable that contributes to more than half to the sum of the array."""
        ratio_array_ = arr/sum(arr)
        if key=="major":
            significant_var_ = [i > 0.5 for i in ratio_array_]
        else:
            significant_var_ = [i > 0.1 for i in ratio_array_]
        return significant_var_

    major_minor_multiples_dict_ = {"major":list_of_major_multiples, "minor":list_of_minor_multiples}
    for key, list_of_dfs in major_minor_multiples_dict_.items():
        list_of_dfs_weighted = [df.div(eigen_vals[i]) for i,df in enumerate(list_of_dfs) if eigen_vals[i] != 0]
        nth_rows_dataframes = []
        if key == "major":
            indices =  major_anomaly_data.index
            for i in range(sum(_major_indicator)):
                nth_rows_dataframes.append([get_row(df, i) for df in list_of_dfs_weighted])
        else:
            indices =  minor_anomaly_data.index
            for i in range(sum(_minor_indicator)):
                nth_rows_dataframes.append([get_row(df, i) for df in list_of_dfs_weighted])
        list_of_array_sum = [get_sum_rows(arr_list) for arr_list in nth_rows_dataframes]
        list_of_significant_vars_array_ = [get_significant_contributor(arr, key) for arr in list_of_array_sum]
        if len(list_of_significant_vars_array_) > 0:
            vars_in_data = test_data_dummies.columns.values
            list_of_significant_vars = [vars_in_data[arrs] for arrs in list_of_significant_vars_array_]
            col_name = str(key) + "_anomaly_significant_variables"
            # print(f"The cols vars are: {vars_in_data}")
            # print(f"The list of significant  vars are: {list_of_significant_vars}")
            test_data_df.assign(col_name=np.nan)
            test_data_df.loc[indices,col_name] = list_of_significant_vars
    return test_data_df
