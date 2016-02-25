#!/usr/bin/env python

"""load_training_features.py: functions to load the features for training data and
store in SimpleDB

Given a user directory, returns a map of features to use for classification
based on the call logs, contact lists, and sms logs
"""

import re, sqlite3, sys
from features import pull_features_for_user

# Map of feature keys to types
feature_keys = {
    'user_id': 'int',
    'earliest_call': 'timestamp',
    'earliest_sms': 'timestamp',
    'latest_call': 'timestamp',
    'latest_sms': 'timestamp',
    'max_times_contacted': 'int',
    'probable_credit_before': 'bool',
    'probable_loaned_before': 'bool',
    'probable_max_credit': 'int',
    'probable_max_loan': 'int',
    'probable_missed_payment': 'bool',
    'total_calls': 'int',
    'total_sms': 'int',
    'unique_calls': 'int',
    'unique_contacts': 'int',
    'unique_contacts_with_phone': 'int',
    'unique_sms': 'int',
}

def save_training_features(basedir, training_user_ids,
                           save_db, save_table='training_features'):
    features_by_user = {}
    for user_id in training_user_ids:
        features_by_user[user_id] = pull_features_for_user(basedir, user_id)
        # Filter out empty data (where only user ID set)
        if len(features_by_user[user_id]) == 1:
            features_by_user.pop(user_id)

    # Assemble the table sql
    create_cols = ', '.join(["%s INT" % col for col in feature_keys])
    insert_cols = ', '.join(["?" for col in feature_keys])

    # convert map to sql insert list
    rows = []
    for user_id, features in features_by_user.iteritems():
        rows.append([features.get(key, 0) for key in feature_keys])

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
    save_training_features(sys.argv[1], [1000,100,101,103], sys.argv[2])

if __name__ == "__main__":
    main()
