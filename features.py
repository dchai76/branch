#!/usr/bin/env python

"""features.py: functions to pull features from user logs

Given a user directory, returns a map of features to use for classification
based on the call logs, contact lists, and sms logs
"""

import json, os, re, sys

# Given a user log directory, return map of features
def pull_features_for_user(basedir, user_id):
    features = { 'user_id': user_id }
    devices = os.listdir('%s/%d' % (basedir, user_id))
    # TODO - check if user has more than one device
    for device in devices:
        features.update(pull_call_log_features('users/%d/%s' % (user_id, device)))
        features.update(pull_contact_list_features('users/%d/%s' % (user_id, device)))
        features.update(pull_sms_log_features('users/%d/%s' % (user_id, device)))
    return features

def pull_call_log_features(basedir):
    if not os.path.exists('%s/call_log' % basedir):
        return {}
    call_logs = os.listdir('%s/call_log' % basedir)
    call_log_data = []
    for call_log in call_logs:
        with open('%s/call_log/%s' % (basedir, call_log)) as data_file:
            call_log_data += json.load(data_file)

    call_log_features = {}
    earliest_call = 0
    latest_call = 0
    unique_calls = {}
    for call in call_log_data:
        datetime = int(call['datetime'])
        if datetime < earliest_call or earliest_call == 0:
            earliest_call = datetime
        if datetime > latest_call:
            latest_call = datetime
        unique_calls[call['phone_number']] = 1

    return {
        'earliest_call': earliest_call,
        'latest_call': latest_call,
        'unique_calls': len(unique_calls),
        'total_calls': len(call_log_data),
        }

def pull_contact_list_features(basedir):
    if not os.path.exists('%s/contact_list' % basedir):
        return {}
    contact_lists = os.listdir('%s/contact_list' % basedir)
    contact_list_data = []
    for contact_list in contact_lists:
        with open('%s/contact_list/%s' % (basedir, contact_list)) as data_file:
            contact_list_data += json.load(data_file)

    last_time_contacted = 0
    max_times_contacted = 0
    unique_contacts_with_phone = 0
    for contact in contact_list_data:
        if contact['last_time_contacted'] > last_time_contacted:
            last_time_contacted = contact['last_time_contacted']
        if contact['times_contacted'] > max_times_contacted:
            max_times_contacted = contact['times_contacted']
        if contact['phone_numbers']:
            unique_contacts_with_phone += 1
        
    return {
        'last_time_contacted': last_time_contacted,
        'max_times_contacted': max_times_contacted,
        'unique_contacts': len(contact_list_data),
        'unique_contacts_with_phone': unique_contacts_with_phone,
        }

def pull_sms_log_features(basedir):
    if not os.path.exists('%s/sms_log' % basedir):
        return {}
    sms_logs = os.listdir('%s/sms_log' % basedir)
    sms_log_data = []
    for sms_log in sms_logs:
        with open('%s/sms_log/%s' % (basedir, sms_log)) as data_file:
            sms_log_data += json.load(data_file)

    sms_log_features = {}
    earliest_sms = 0
    latest_sms = 0
    unique_sms = {}
    probable_loaned_before = 0
    probable_max_loan = 0
    probable_credit_before = 0
    probable_max_credit = 0
    probable_missed_payment = 0

    for sms in sms_log_data:
        if sms['datetime'] < earliest_sms or earliest_sms == 0:
            earliest_sms = sms['datetime']
        if sms['datetime'] > latest_sms:
            latest_sms = sms['datetime']
        unique_sms[sms['sms_address']] = 1
        message = sms['message_body'].lower()

        # Look for money amount in the message. The different formats are tricky to
        # match with a single regex so look in order, with decimal and without, ksh after,
        # then with decimal and without, ksh before. Haven't seen a message that mixes
        # amount formats in the same message
        money_amounts = re.findall('([\d,]+)(?:\.\d{1,2})?(?:\s)?ksh', message)
        if not money_amounts:
            money_amounts = re.findall('ksh(?:s)?(?:\.)?(?:\s)*([\d,]+)(?:\.\d{1,2})?', message)

#        if 'ksh' in message and not money_amounts and sys.argv[2] == '1':
#            print sms
#            print money_amounts
#        if money_amounts and sys.argv[2] == '0':
#            print sms
#            print money_amounts

        if money_amounts:
            # int() doesn't like commas
            money_amounts = filter(None, [x.replace(',', '') for x in money_amounts])

        if money_amounts:
            max_val = max(map(int, money_amounts))

            # print money_amounts
            # print max_val
            if 'loan' in message:
                probable_loaned_before = 1
                if max_val > probable_max_loan:
                    probable_max_loan = max_val
            elif 'balance' in message:
                probable_credit_before = 1
                if max_val > probable_max_credit:
                    probable_max_credit = max_val
            if 'missed' in message or 'unpaid' in message:
                probable_missed_payment = 1

    return {
         'earliest_sms': earliest_sms,
         'latest_sms': latest_sms,
         'unique_sms': len(unique_sms),
         'total_sms': len(sms_log_data),
         'probable_loaned_before': probable_loaned_before,
         'probable_max_loan': probable_max_loan,
         'probable_credit_before': probable_credit_before,
         'probable_max_credit': probable_max_credit,
         'probable_missed_payment': probable_missed_payment,
        }

def main():
    user_features = pull_features_for_user(int(sys.argv[1]))
    print user_features

if __name__ == "__main__":
    main()

