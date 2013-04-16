#!/usr/bin/env python

'''
Please fill in the following questions with the words True or False
True always means yes, and False always means no.
Please make sure to capitalize True and False

For example:
    need_2_am = True
    require_whole_day = False
    excl_wakemin_gt_10 = True
    
If you choose True for either of the questions about filtering according
to what's in an external file, please make sure that you have access to 
that file, and that it contains the information you need. If it doesn't you'll
have to update the path and file to fit your needs.

Remember to keep these file names between ' ' quotes.
'''

#------------------------------------------------------------------------------
# DO NOT EDIT ABOVE THIS LINE
#------------------------------------------------------------------------------

# Do you require all cortisol values to be < 3?
cort_lt_3 = False

# Do you require the comment for each cortisol value to be '1000'
# (signifiying there isn't a problem, although not necessarily
# signifying that there _is_ a problem)
comment_1000 = False

# Do you want to exclude waking measures that were collected more than
# 10 minutes after waking?
minawake_lt10 = False

# Do you require a whole day's worth of data to consider it in the average?
require_whole_day = False

# Do you require two am values to calculate the maximum am value?
need_2_am = False

# Do you wish to exclude the CAR value if it is negative?
# (implying that this participant does not meet your model of cortisol
# awakening response and therefore you can't accurately interpret it?)
excl_neg_CAR = False

#------------------------------------------------------------------------------
# Would you like to exclude participants who are taking medication on 
# this list:
excl_med = False
medication_list = '/work/imagingA/mrimpact/workspaces/CORTISOL/MedicationList.txt'

# Would you like to filter the list according to another list of subjects?
# (for example, a list of subIDs representing participants who have usable
# mri data)
filter_subs = True
include_subs_list = '/work/imagingA/mrimpact/workspaces/CORTISOL/MRIMPACT_subs.txt'

#------------------------------------------------------------------------------
# DO NOT EDIT BEYOND THIS LINE
#------------------------------------------------------------------------------

'''
Template created to be used with Cortisol_PreProcessing.py script
    by Kirstie Whitaker
    in April 2013
    for MRIMPACT cortisol data
    Contact info: kw401@cam.ac.uk
Version 0.1
'''
