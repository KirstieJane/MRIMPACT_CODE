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

Note that you can enter ' ' as a filename if you don't want to use that
particular filter. For example, if you want to *exclude* a couple of subjects
but don't have a filelist of subjects to *include* then you can set:

    filter_subs = True
    include_subs_list = ' '
    exclude_subs_list = '/work/imagingA/mrimpact/workspaces/CORTISOL/exclude_subjects.txt'

'''

#------------------------------------------------------------------------------
# DO NOT EDIT ABOVE THIS LINE
#------------------------------------------------------------------------------

# Do you require all cortisol values to be < 3?
cort_lt_3 = True

# Do you require the comment for each cortisol value to be '1000'
# (signifiying there isn't a problem, although not necessarily
# signifying that there _is_ a problem)
comment_1000 = True

# Do you want to exclude waking measures that were collected more than
# 10 minutes after waking?
minawake_lt10 = True

# Do you require a whole day's worth of data to consider it in the average?
require_whole_day = True

# Do you require two am values on the same day to calculate that day's maximum am value?
need_2_am = False

# Do you wish to exclude the CAR value if it is negative?
# (implying that this participant does not meet your model of cortisol
# awakening response and therefore you can't accurately interpret it?)
excl_neg_CAR = False

#------------------------------------------------------------------------------
# Would you like to exclude participants who are taking medication on 
# this list:
excl_med = True
medlist_file = '/work/imagingA/mrimpact/workspaces/CORTISOL/Cortisol_ExcludeMedications.txt'
medlist_special_cases_file = '/work/imagingA/mrimpact/workspaces/CORTISOL/Cortisol_ExcludeMedications_SpecialCases.txt'

# Would you like to filter the list according to another list of subjects?
# (for example, a list of subIDs representing participants who have usable
# mri data)
filter_subs = False
include_subs_list = '/work/imagingA/mrimpact/workspaces/CORTISOL/MRIMPACT_subs.txt'
exclude_subs_list = ' '

#------------------------------------------------------------------------------
# DO NOT EDIT BEYOND THIS LINE
#------------------------------------------------------------------------------

# Create a nice useful title:
check_dict = {  0: r'$\times$',
                1: r'$\checkmark$' }

                
criteria_title = ( 'DISTRIBUTIONS OF CORTISOL MEASURES\n'
                    + 'USING THESE FILTERS:\n'
                    + 'Cort measures less than 3 ' + check_dict[cort_lt_3] + '\t'
                    + 'Comment must be "1000" ' + check_dict[comment_1000] + '\n'
                    + 'Mins awake less than 10 ' + check_dict[minawake_lt10] + '\t'
                    + 'Require whole day\'s worth of data ' + check_dict[require_whole_day] + '\n'
                    + 'Require two measures in the morning to calc max ' + check_dict[need_2_am] + '\n'
                    + 'Exclude medicated subjects ' + check_dict[excl_med] + '\n'
                    + 'Filter subjects by external list ' + check_dict[filter_subs] )

'''
Template created to be used with Cortisol_PreProcessing.py script
    by Kirstie Whitaker
    in April 2013
    for IMPACT cortisol data
    Contact info: kw401@cam.ac.uk
Version 1

I hope this youtube video is still around when you read this.
It's AMAZING.
http://youtu.be/o8TssbmY-GM
'''
