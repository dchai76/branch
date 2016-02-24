#!/usr/bin/env python

"""load_training_features.py: functions to load the features for training data and
store in SimpleDB

Given a user directory, returns a map of features to use for classification
based on the call logs, contact lists, and sms logs
"""

import re, sqlite3, sys
from features import pull_features_for_user
from pprint import pprint

# Returns dict where keys are bad loanee user ids
def get_bad_loanees_map(bad_loanees_filename):
    bad_loanees = {}
    with open(bad_loanees_filename) as f:
        bad_loan_data = f.readlines()
        for l in bad_loan_data:
            data = re.match('^#<(.*)>$', l)
            if data:
                for feature in data.group(1).split(","):
                    (k, v) = feature.split(": ")
                    if (k.strip() == 'User id'):
                        v = v.strip('\S"')
                        bad_loanees[int(v)] = 1

    return bad_loanees

def save_training_features(basedir, training_user_ids, bad_loanees_filename,
                           save_db, save_table='training_features'):
    features_by_user = {}
    bad_loanees = get_bad_loanees_map(bad_loanees_filename)

    # Augment feature map with whether the user is a bad loanee
    for user_id in training_user_ids:
        features_by_user[user_id] = pull_features_for_user(basedir, user_id)
        features_by_user[user_id]['bad'] = (1 if user_id in bad_loanees else 0)

    feature_keys = features_by_user[training_user_ids[0]].keys()

    # Assemble the table sql
    create_cols = ', '.join(["%s INT" % col for col in feature_keys])
    insert_cols = ', '.join(["?" for col in feature_keys])

    # convert map to sql insert list
    rows = []
    for user_id, features in features_by_user.iteritems():
        rows.append([features[key] for key in feature_keys])

    conn = sqlite3.connect(save_db)
    with conn:
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS %s" % save_table)
        cur.execute("CREATE TABLE %s(%s)" % (save_table, create_cols))
        cur.executemany("INSERT INTO %s VALUES(%s)" % (save_table, insert_cols), rows)
    conn.close()

# Convenience function to delete existing training table
def clear_table(save_db, save_table='training_features'):
    conn = sqlite3.connect(save_db)
    with conn:
        cur = conn.cursor() 
        cur.execute("DROP TABLE IF EXISTS %s" % save_table)
    conn.close()
    
def main():
    map = save_training_features(sys.argv[1], [1000,100,101,103], sys.argv[2], sys.argv[3])
    pprint(map)

if __name__ == "__main__":
    main()
