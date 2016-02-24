#!/usr/bin/env python

"""branch.py: functions to pull features from user logs

Given a user directory, returns a map of features to use for classification
based on the call logs, contact lists, and sms logs
"""

import sys, os
from load_training_features import save_training_features

def main():

    if len(sys.argv) < 2:
        print "usage: %s basedir delinquent_id_file" % sys.argv[0]
        print " - basedir is the directory contaning user logs"
        print " - delinquent_id_file is the file listing delinquent loanee ids"
        sys.exit(0)

    # Get a list of available users, split into 70% training, 30% testing
    user_ids = [int(user_id) for user_id in os.listdir(sys.argv[1])]
    split_index = int(0.7 * len(user_ids))
    training_user_ids = user_ids[:split_index]
    testing_user_ids = user_ids[split_index:]

    # Save training data
    save_training_features(sys.argv[1], training_user_ids, sys.argv[2], 'training_db')

if __name__ == "__main__":
    main()
