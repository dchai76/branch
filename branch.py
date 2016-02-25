#!/usr/bin/env python

"""branch.py: main test logic

Divides user test data in training/test, builds the training model, then tests on the rest
"""

import numpy, re, sqlite3, sys, time, os
from load_training_features import save_training_features, feature_keys
from features import pull_features_for_user
from sklearn import linear_model
from sklearn.utils import check_X_y

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
    training_table = 'training_features'

    # Get a list of available users, split into 70% training, 30% testing
    user_ids = [int(user_id) for user_id in os.listdir(sys.argv[1])]
    split_index = int(0.7 * len(user_ids))
    training_user_ids = user_ids[:split_index]
    testing_user_ids = user_ids[split_index:]

    # Save training data
    save_training_features(sys.argv[1], training_user_ids, training_db, training_table)

    # Assemble the query. For the time fields, use difference in seconds from now to make ranges
    # more manageable. Also note the logs are in milliseconds
    selects = ', '.join(
        ["case when %s = 0 then cast(strftime('%%s','now') as int) else cast(strftime('%%s', 'now') as int) - (%s/1000) end as %s" % (x, x, x)
         if feature_keys[x] == 'timestamp' else x for x in feature_keys])

    conn = sqlite3.connect(training_db)
    with conn:
        cur = conn.execute('SELECT %s FROM %s' % (selects, training_table))
        cols = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
    conn.close()

    bad_loanees = get_bad_loanees_map(sys.argv[2])

    # assemble list of good/bad classifications in same order as rows
    classification = [bad_loanees.get(row[cols.index('user_id')], 0) for row in rows]

    # Train the model
    clf = linear_model.SGDClassifier(loss='log')
    clf.fit(rows, classification)

    # Go through the testing IDs and test our model
    num_correct = 0
    
    for test_user_id in testing_user_ids:
        pulled_features = pull_features_for_user(sys.argv[1], int(test_user_id))
        transformed_features = []
        for key in feature_keys:
            val = pulled_features.get(key, 0)
            if feature_keys[key] == 'timestamp':
                if not val:
                    val = int(time.time())
                else:
                    val = int(time.time()) - val/1000
            transformed_features.append(val)

        prediction = clf.predict([transformed_features])
        print "Predicted %d for %d" % (prediction, test_user_id)
        correct = bad_loanees.get(int(test_user_id), 0) == prediction
        if correct:
            num_correct += 1
        print "Prediction was %scorrect" % ('' if correct else 'not ')

    print "Model got %d/%d (%d) correct" % (num_correct, len(testing_user_ids), float(num_correct) / len(testing_user_ids))

if __name__ == "__main__":
    main()
