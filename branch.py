#!/usr/bin/env python

"""branch.py: functions to pull features from user logs

Given a user directory, returns a map of features to use for classification
based on the call logs, contact lists, and sms logs
"""

import re, sqlite3, sys, os
from load_training_features import save_training_features
from sklearn import linear_model

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

def main():

    if len(sys.argv) < 2:
        print "usage: %s basedir delinquent_id_file" % sys.argv[0]
        print " - basedir is the directory contaning user logs"
        print " - delinquent_id_file is the file listing delinquent loanee ids"
        sys.exit(0)

    training_db = 'training_db'

    # Get a list of available users, split into 70% training, 30% testing
    user_ids = [int(user_id) for user_id in os.listdir(sys.argv[1])]
    split_index = int(0.7 * len(user_ids))
    training_user_ids = user_ids[:split_index]
    testing_user_ids = user_ids[split_index:]

    # Save training data
    save_training_features(sys.argv[1], training_user_ids, training_db)

    conn = sqlite3.connect(training_db)
    with conn:
        cur = conn.execute('SELECT * FROM %s' % 'training_features')
        cols = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
    conn.close()

    bad_loanees = get_bad_loanees_map(sys.argv[2])

    # assemble list of good/bad classifications in same order as rows
    classification = [bad_loanees.get(row[cols.index('user_id')], 0) for row in rows]

    clf = linear_model.SGDClassifier()
    clf.fit(rows, classification)

if __name__ == "__main__":
    main()
