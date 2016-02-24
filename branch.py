#!/usr/bin/env python

"""branch.py: Sample Branch classifer."""

import math, re, sys, time
from dateutil import parser

# Features we care about as well as their type
relevant_features = {
    'auth_token': 'bool',
    'created_at': 'timestamp',
    'current_sign_in_at': 'bool',
    'current_sign_in_ip': 'bool',
    'dob': 'timestamp',
    'email': 'bool',        # TODO separate by provider
    'gender': 'gender',
    'image': 'bool',
    'last_phone_instance': 'int',
    'last_sign_in_at': 'timestamp',
    'last_sign_in_ip': 'bool',
    'legal_name': 'bool',   # TODO separate by count
    'permission': 'int',
    'primary_financial_account_id': 'bool',
    'push_notification_key': 'bool',
    'remember_created_at': 'timestamp',
    'reset_password_sent_at': 'bool',
    'reset_password_token': 'bool',
    'sign_in_count': 'int',
    'status': 'int',
    'updated_at': 'timestamp',
}

# Features we don't care about
# - encrypted_password
# - fb_friends (don't know the format, all nil)
# - first_name
# - last_name
# - locale (TODO consider)
# - nat_id_num
# - primary_sim_id
# - provider
# - timezone (TODO consider)
# - uid
# - username (redundant with email)
# - User id

# Return the appropriate feature value based on the type
def get_feature_value(feature_name, feature_map):
    type = relevant_features[feature_name]
    if type == 'int':
        value = int(feature_map[feature_name])
    elif type == 'bool':
        value = int(bool(feature_map[feature_name]))
    elif type == 'timestamp':
        value = time.mktime(parser.parse(feature_map[feature_name]).timetuple()) if feature_map[feature_name] else 0
    elif type == 'gender':
        value = 1 if feature_map[feature_name] == 'male' else 0
    else:
        value = 0

    return value

# Math functions for Gaussian Naive Bayes
#
# Most of the Bayes' related code comes from http://machinelearningmastery.com/naive-bayes-classifier-scratch-python/

def mean(numbers):
    return sum(numbers)/float(len(numbers))
 
def stdev(numbers):
    avg = mean(numbers)
    variance = sum([pow(x-avg,2) for x in numbers])/float(len(numbers)-1)
    return math.sqrt(variance)

# Given a feature value and the mean/stdev for the feature, return the probability
# that it belongs to the class
def calculate_probability(x, mean, stdev):
    if stdev == 0:
        return 1 if x == mean else 0
    exponent = math.exp(-(math.pow(x-mean,2)/(2*math.pow(stdev,2))))
    return (1 / (math.sqrt(2*math.pi) * stdev)) * exponent

# Given a list of feature maps, return the mean and stdev for each relevant feature
def calc_mean_stdev(instances):
    feature_stats = {}
    for feature, type in relevant_features.iteritems():
        attribute = [get_feature_value(feature, x) for x in instances]
        feature_stats[feature] = [mean(attribute), stdev(attribute)]

    return feature_stats

# Calculate the probability that it's good or bad, return 1 if more likely good
def classify_one_instance(good_feature_stats, bad_feature_stats, features_to_use, input_feature_map):
    good_probability = 1
    bad_probability = 1

    for feature in features_to_use:
        value = get_feature_value(feature, input_feature_map)
        (good_mean, good_stdev) = good_feature_stats[feature]
        (bad_mean, bad_stdev) = bad_feature_stats[feature]
        good_probability *= calculate_probability(value, good_mean, good_stdev)
        bad_probability *= calculate_probability(value, bad_mean, bad_stdev)

    return 1 if good_probability > bad_probability else 0

# Return percentage correctly classified
def classify_all(good_feature_stats, bad_feature_stats, features_to_use, test_instances):
    num_correct = 0
    for instance in test_instances:
        good = classify_one_instance(good_feature_stats, bad_feature_stats, features_to_use, instance)
        if eval(instance):
            if good:
                num_correct += 1
        else:
            if not good:
                num_correct += 1

    return num_correct / len(test_instances) * 100

# Evaluation function, returns 1 if good. Right now hacked to use gender until I learn
# what's good/bad lender in the test data
def eval(input_features):
    return int(input_features['gender'] == 'male')

# Use Sequential Forward Selection to get top n features
def seq_forward_select_features(good_feature_stats, bad_feature_stats, test_instances, max_n):
    top_n_features = []
    potential_feature_list = relevant_features.keys()

    while True:
        # Sequentially test using one additional feature, choose the one that returns the best
        # accuracy until we get n
        temp_next_features = top_n_features + [potential_feature_list[0]]
        best_percentage = classify_all(good_feature_stats, bad_feature_stats, temp_next_features, test_instances)
        best_feature = potential_feature_list[0]
        for x in potential_feature_list[1:]:
            temp_next_features = top_n_features + [x]
            percentage = classify_all(good_feature_stats, bad_feature_stats, temp_next_features, test_instances)
            if percentage > best_percentage:
                best_percentage = percentage
                best_feature = x

        top_n_features.append(best_feature)
        potential_feature_list.remove(best_feature)
        if len(top_n_features) == max_n:
            break

    return top_n_features

def main():
    if (len(sys.argv) < 2):
        print 'Specify file with training data'
        sys.exit(1)

    with open(sys.argv[1]) as f:
        content = f.readlines()

    if (len(sys.argv) < 3):
        sfs_max_n = 5
    else:
        sfs_max_n = int(sys.argv[2])

    # Load the test data into feature maps, separated by good and bad

    all_instances = []
    good_instances = []
    bad_instances = []

    for l in content:
        data = re.match('^#<(.*)>$', l)
        if data:
            features = {}
            for feature in data.group(1).split(","):
                (k, v) = feature.split(": ")
                k = k.strip()
                v = v.strip('\S"')
                features[k] = None if v == 'nil' else v

            if eval(features):
                good_instances.append(features)
            else:
                bad_instances.append(features)
            all_instances.append(features)

    # Calculate mean/stdev for good and bad buckets
    good_stats = calc_mean_stdev(good_instances)
    bad_stats = calc_mean_stdev(bad_instances)

    # Example classification, re-running on training data
    percent_correct = classify_all(good_stats, bad_stats, relevant_features.keys(), all_instances)
    print 'Classifer got %g%% correct' % percent_correct

    # Example of how I'd run SFS to select top N features
    top_features = seq_forward_select_features(good_stats, bad_stats, all_instances, sfs_max_n)
    sfs_percent_correct = classify_all(good_stats, bad_stats, top_features, all_instances)
    print 'SFS Classifer got %g%% correct choosing %d features' % (sfs_percent_correct, sfs_max_n)
    

main()
