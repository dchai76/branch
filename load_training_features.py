#!/usr/bin/env python

"""load_training_features.py: functions to load the features for training data and
store in SimpleDB

Given a user directory, returns a map of features to use for classification
based on the call logs, contact lists, and sms logs
"""

import re, sqlite3, sys
from features import pull_features_for_user

def save_training_features(basedir, training_user_ids,
                           save_db, save_table='training_features'):
    features_by_user = { user_id: pull_features_for_user(basedir, user_id) for user_id in training_user_ids }
    feature_keys = features_by_user[training_user_ids[0]].keys()

    # Assemble the table sql
    create_cols = ', '.join(["%s INT" % col for col in feature_keys])
    insert_cols = ', '.join(["?" for col in feature_keys])

    # convert map to sql insert list
    rows = []
    for user_id, features in features_by_user.iteritems():
        rows.append([features.get(key) for key in feature_keys])

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
