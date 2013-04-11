#!/usr/bin/env python
"""
Cortisol_PreProcessing.py
Created by Kirstie Whitaker
Contact information: kw401@cam.ac.uk

This script takes a tab delimited text file that has been
converted from an SPSS spreadsheet. It calculates the average
data across two days for waking, waking+30, evening measures of
cortisol. It also calculates (and then averages) the cortisol
awakening response, the maximum am value, daytime average and
daytime range.

The various selection criteria can be set in the
Cortisol_SelectionCriteria.py file that is currently hard coded
but will be passed as an argument!

TO BE DONE:
    Filter by various files
    Output data!

"""
#====================================================================
# IMPORTS
import numpy as np
import itertools as it
import sys
import matplotlib.pylab as plt
import numpy.lib.recfunctions as rec
#====================================================================

#====================================================================
# FUNCTIONS
#====================================================================
def usage():
    print ( 'USAGE: Cortisol_PreProcessing.py '
                + ' <data_filename>'
                + ' <selection_criteria_filename>' )
    print ( '<data_filename> is a TAB delineated file'
                + ' containing the cortisol data' )
    print ( '<selection_criteria_filename> is a python file that'
                + ' contains the answers (True or False) to'
                + ' selection criteria' )
                
def import_data(data_filename):
    '''
    Read in the data as a TAB separated file
    Correct some bonkers naming typos
    Define a couple of useful dictionaries
    INPUT:      tab separated filename
    RETURNS:    data (recarray)
                measure_dict
                minawake_dict
    '''
    data = np.genfromtxt('IMPACT_CortisolMeasure_KW.txt',
                            names=True, dtype=None,
                            delimiter='\t',
                            filling_values = 999)

    # Correct some bonkers naming typos:
    names = list(data.dtype.names)

    names = [ name if not name == 'bl_d130comment'
                        else 'bl_d130mcomment'
                        for name in names ]

    # Because I think it looks nicer insert an _ between
    # the day (eg: d1) and the time of measurement
    for i, name in enumerate(names):
        n_l = list(name)
        if len(n_l) > 5:
            if n_l[3] == 'd' and not n_l[5] == '_':
                n_l.insert(5, '_')
            name = ''.join(n_l)
        names[i] = name

    data.dtype.names = names

    # As another little clean up thing, if there is a 999
    # in the 'bl_d{day}_minawake' column then replace that
    # with a zero. It won't always mean that the measure was
    # taken right away, because the data might really be missing
    # but this was entered in a pretty bonkers way such that
    # if the data is "perfect" then there is no entry!
    mask = data['bl_d1_minawake']==999
    data['bl_d1_minawake'][mask] = 0
    mask = data['bl_d2_minawake']==999
    data['bl_d2_minawake'][mask] = 0
    
    for name in data.dtype.names:
        data[name][data[name]==99] = 999

    # Use the following dictionaries to identify the
    # various measures

    # These dictionaries are indexed by TIME of measurement
    # WITHIN a single day
    measure_dict = {    0: 'wake',
                        1: '30m',
                        2: 'eve',
                        3: 'CAR',
                        4: 'maxam',
                        5: 'dayAv',
                        6: 'dayRange' }

    # For now we're only interested in baseline (bl) data
    # Note that this is bl for b(ase)l(ine) not b'one'
    
    return data, measure_dict
#--------------------------------------------------------------------

def define_selection_column(data, in_column_name, out_column_name, criterion):
    '''
    Generic define selection column based on any criterion
    criterion is passed as a string
    '''
    if not criterion == '':
        eval_string = 'data[in_column_name]' + criterion
        mask = eval(eval_string)
        out_data = np.zeros(data[in_column_name].shape)
        out_data[mask] = 1
    else:
        out_data = np.ones(data[in_column_name].shape)
    
    # Add this column of numbers to the recarray
    data = rec.append_fields(base=data,
                        names=out_column_name,
                        data=out_data,
                        dtypes=int,
                        usemask=False,
                        asrecarray=True )
    return data
#--------------------------------------------------------------------

def create_overall_selection_data(data, measure_name):

    names = list(data.dtype.names)
    
    # Find all the columns that have the measure name in their title
    # and also start with the word "Use"
    use_names = [ name for name in names if name.find(measure_name) > 1 ]
    use_names = [ name for name in use_names if name.find('Use') == 0 ]
    
    # Now create a numpy array of these columns
    selection_data = data[use_names[0]]
    for name in use_names[1:]:
        selection_data = np.vstack([selection_data, data[name]])
    
    # If there are any zeros then you can't use that data
    overall_selection_data = np.zeros_like(data[name])
    overall_selection_data[np.all(selection_data, axis=0)] = 1

    overall_selection_name = 'Use_' + measure_name + '_Overall'
    
    # Add this column of numbers to the recarray
    data = rec.append_fields(base=data,
                        names=overall_selection_name,
                        data=overall_selection_data,
                        dtypes=int,
                        usemask=False,
                        asrecarray=True )
    return data
#--------------------------------------------------------------------

def define_use_day_column(data):
    '''
    # Criterion:
    ## Do you require a whole day's worth of data to consider it in the average?
    '''
    # We're going to create a column (called use_day) that codes whether you
    # should use no day's data (0), just day 1 (1), just day 2 (2) or 
    # both days (3)
    use_day_data = np.zeros_like(data['ID'])
    
    if require_whole_day:
        # This means that for each day separately we're going
        # to see if all three of the cortisol measures are there
        masks = np.vstack([[use_day_data==1], [use_day_data==1]])
        for day in range(1,3):
            name_1 = 'Use_bl_d{day}_wakecortisol_Overall'.format(day=day)
            name_2 = 'Use_bl_d{day}_30mcortisol_Overall'.format(day=day)
            name_3 = 'Use_bl_d{day}_evecortisol_Overall'.format(day=day)
            mask_1 = data[name_1] == 1
            mask_2 = data[name_2] == 1
            mask_3 = data[name_3] == 1
            masks[day-1] = mask_1 * mask_2 * mask_3

        day_1_mask = np.logical_xor(masks[0], masks[1]) * masks[0]
        day_2_mask = np.logical_xor(masks[0], masks[1]) * masks[1]
        both_days_mask = masks[0] * masks[1]
        use_day_data[day_1_mask] = 1
        use_day_data[day_2_mask] = 2
        use_day_data[both_days_mask] = 3
    
    else:
        use_day_data = use_day_data + 3
        
    # Add this column of numbers to the recarray
    data = rec.append_fields(base=data,
                        names='bl_useDay',
                        data=use_day_data,
                        dtypes=None,
                        usemask=False,
                        asrecarray=True )
    return data
#--------------------------------------------------------------------

def define_calc_max_column(data):
    '''
    # Criterion:
    ## Do you require two am values to calculate the maximum am value?
    '''
    # Dead easy, if there are two am values then you can calculate
    # the maximum :)
    for day in xrange(1,3):
        calc_max_data_name = 'bl_d{day}_calc_max'.format(day=day)
        calc_max_data = np.ones_like(data['ID'])
        
        if need_2_am:
            # Create two separate masks for measure 1 and measure 2:
            name_1 = 'Use_bl_d{day}_wakecortisol_Overall'.format(day=day)
            name_2 = 'Use_bl_d{day}_30mcortisol_Overall'.format(day=day)
            mask_1 = data[name_1] == 1
            mask_2 = data[name_2] == 1
            mask = mask_1 * mask_2
            calc_max_data[mask] = 1

        # Add this column of numbers to the recarray
        data = rec.append_fields(base=data,
                            names=calc_max_data_name,
                            data=calc_max_data,
                            dtypes=None,
                            usemask=False,
                            asrecarray=True )
    return data
#--------------------------------------------------------------------

def write_selection_columns(data, measure_dict):
    '''
    Loop through the various selection criteria
    '''
    # First one to consider are the criteria that affect individual
    # measures. First there are the criteria that affect all the cortisol
    # measures
    for day in xrange(1,3):
        for time in xrange(3):
            '''
            # CRITERION: Cortisol data is present
            # (This criterion is not in the selectioncriteria file because...well...
            # are we interested in data that doesn't exist??)
            '''
            in_column_name = 'bl_d{day}_{time}cortisol'.format(day=day, time=measure_dict[time])
            out_column_name = 'Use_bl_d{day}_{time}cortisol_HasData'.format(day=day, time=measure_dict[time])
            data = define_selection_column(data, in_column_name, out_column_name, ' < 99')
            
            '''
            # CRITERION: All cortisol values must be less than 3
            '''
            in_column_name = 'bl_d{day}_{time}cortisol'.format(day=day, time=measure_dict[time])
            out_column_name = 'Use_bl_d{day}_{time}cortisol_Lt3'.format(day=day, time=measure_dict[time])
            if cort_lt_3:
                data = define_selection_column(data, in_column_name, out_column_name, ' < 3')
            else:
                data = define_selection_column(data, in_column_name, out_column_name, '')

            '''
            # CRITERION: All cortisol comments have to be '1000'
            '''
            in_column_name = 'bl_d{day}_{time}comment'.format(day=day, time=measure_dict[time])
            out_column_name = 'Use_bl_d{day}_{time}comment_1000'.format(day=day, time=measure_dict[time])
            if comment_1000:
                data = define_selection_column(data, in_column_name, out_column_name, ' == str(1000)')
            else:
                data = define_selection_column(data, in_column_name, out_column_name, '')
    
            '''
            # CRITERION: Wake cortisol has to be acquired within 10 minutes of waking
            '''
            if time == 1:
                in_column_name = 'bl_d{day}_minawake'.format(day=day)
                out_column_name = 'Use_bl_d{day}_minawake_Lt10'.format(day=day)
                if minawake_lt10:
                    data = define_selection_column(data, in_column_name, out_column_name, ' < 10')
                else:
                    data = define_selection_column(data, in_column_name, out_column_name, '')
    
            # Having all these separately is fine, but we obviously need them together!
            # Create an overall yay or nay column for each measure
            measure_name = 'bl_d{day}_{time}cortisol'.format(day=day, time=measure_dict[time])
            data = create_overall_selection_data(data, measure_name)
    
    # Now let's turn to the criteria that affect the whole day
    '''
    # CRITERION: All measures must be present for day to be included in average
    '''
    data = define_use_day_column(data)
    
    '''
    # CRITERION: Must have two usable am data points to calculate maximum
    '''
    data = define_calc_max_column(data)
    
    '''
    # CRITERION: CAR can not be negative
    '''
    # This is dealt with later once we've calculated the CAR values!
    
    # And finally, data that affects the entire participant
    '''
    # CRITERION: Participant can not be on medication
    '''
    ############## TO BE DONE ################
    return data
#--------------------------------------------------------------------

def compare_columns(data, name_1, name_2, name_combo, mask, function):
    '''
    Compare two columns and if there is data in both of them
    complete a particular function:
        Functions can be 'average', 'diff' or 'max'
    The mask is a column of 0, 1, 2 and 3 which tells you whether to
    use neither data point (999), only data['name_1'], only data['name_2']
    or carryout the function on both data.

    Returns: data
    '''

    # Define your data
    data_1 = data[ name_1 ]
    data_2 = data[ name_2 ]
    data_combo_name = name_combo
    
    # Fill in the data initally with 999s
    data_combo = np.ones_like(data_1) * 999.
    
    # Update the mask such that missing data is taken into 
    # consideration:
    mask_1 = data_1 == 999
    mask_2 = data_2 == 999
    
    # If data 1 is missing then you can't use both point
    # so you'll have to just use 2, and vice versa
    mask[(mask==3) * (mask_1)] = 2
    mask[(mask==3) * (mask_2)] = 1

    # If you weren't supposed to be using both data points
    # they you're SOL and now you can't use either!
    mask[(mask==1) * (mask_1)] = 0
    mask[(mask==2) * (mask_2)] = 0    

    # If there is only one data point fill that in
    data_combo[mask==1] = data_1[mask==1]
    data_combo[mask==2] = data_2[mask==2]

    # If there are two data points calculate:
    if function == 'average':
        data_combo[mask==3] = ( data_1[mask==3] + data_2[mask==3] ) / 2
    elif function == 'diff':
        data_combo[mask==3] = ( data_2[mask==3] - data_1[mask==3] )
    elif function == 'max':
        data_combo[mask==3] = np.maximum( data_2[mask==3], data_1[mask==3] )

    # Append this data to our recarray
    data = rec.append_fields(base=data,
                        names=name_combo,
                        data=data_combo,
                        dtypes=None,
                        usemask=False,
                        asrecarray=True )
    
    return data
#--------------------------------------------------------------------

def run_comparisons_within_day(data, measure_dict):
    '''
    Here we calculate the four additional measures of interest:
        maxam
        CAR
        dayAv
        dayRange
    
    If excl_wakemin_gt_10 is true then we will mask with the answer
    to the question:
        "Do you want to exclude waking measures that were collected
        more than 10 minutes after waking?
    '''
    for day in xrange(1,3):
        #------------------------------------------------------------
        # Calculate the cortisol awakening response
        # which is the difference between the morning measures
        name_1 = 'bl_d{day}_wakecortisol'.format(day=day)
        name_2 = 'bl_d{day}_30mcortisol'.format(day=day)
        name_diff = 'bl_d{day}_CARcortisol'.format(day=day)

        mask_1_name = 'Use_bl_d{day}_wakecortisol_Overall'.format(day=day)
        mask_2_name = 'Use_bl_d{day}_30mcortisol_Overall'.format(day=day)
        
        mask_1 = data[mask_1_name]
        mask_2 = data[mask_2_name]
        
        # We can't calculate the difference if there is only 1 data point
        mask = (mask_1 * mask_2) * 3

        data = compare_columns(data, name_1, name_2, name_diff, mask, 'diff')
        
        # Replace values that are negative with 999 if excl_neg_CAR is True
        if excl_neg_CAR:
            mask = data[name_diff] < 0
            data[name_diff][mask] = 999
        #------------------------------------------------------------
        
        # Calculate the maximum morning cortisol measure
        # defined as the largest of the two morning measures
        # and uses the same input data as the CAR
        name_max = 'bl_d{day}_maxamcortisol'.format(day=day)

        # but a different mask
        mask_max_name = 'bl_d{day}_calc_max'.format(day=day)
        mask_max = data[mask_max_name]

        mask_xor_1 = np.logical_xor(mask_1, mask_2) * mask_1
        mask_xor_2 = np.logical_xor(mask_1, mask_2) * mask_2
        mask[mask_xor_1] = 1
        mask[mask_xor_2] = 2
        mask * mask_max
        
        data = compare_columns(data, name_1, name_2, name_max, mask, 'max')
        #------------------------------------------------------------
        
        # Calculate the daytime average cortisol measure
        # defined as the difference between the daytime max
        # and the evening value
        name_1 = 'bl_d{day}_maxamcortisol'.format(day=day)
        name_2 = 'bl_d{day}_evecortisol'.format(day=day)
        name_av = 'bl_d{day}_dayAvcortisol'.format(day=day)
        
        mask_2_name = 'Use_bl_d{day}_evecortisol_Overall'.format(day=day)
        
        # For maxam use the mask from the previous calculation
        mask_1[mask > 0] = 1

        mask_2 = data[mask_2_name]

        mask = mask_1 * mask_2

        data = compare_columns(data, name_1, name_2, name_av, mask, 'average')
        # And also calculate the range in cortisol values
        # throughout the day
        name_diff = 'bl_d{day}_dayRangecortisol'.format(day=day)
        data = compare_columns(data, name_1, name_2, name_diff, mask, 'diff')
    
    return data
#--------------------------------------------------------------------

def run_comparisons_across_day(data, measure_dict):        
    '''
    Here we calculate the average measure across the two days
    We mask with the results from the bl_useDay column that
    was created based on the selection criterion:
    "Do you require a whole day's worth of data to consider
    it in the average?"
    '''

    # Calculate the average across days for the various measures
    for time in xrange(7):
        name_1 = 'bl_d1_{time}cortisol'.format(time=measure_dict[time])
        name_2 = 'bl_d2_{time}cortisol'.format(time=measure_dict[time])
        name_av = 'bl_av_{time}cortisol'.format(time=measure_dict[time])
        
        mask = data['bl_useDay']
        
        data = compare_columns(data, name_1, name_2, name_av, mask, 'average')
    
    return data
#--------------------------------------------------------------------

def data_report(data):
    '''
    This function creates figures of the data and
    ---WILL---
    contain tables of Ns etc.
    This function creates a table of N's for each possible
    combination of exclusion criteria
    
    These critera include:
        Any cortisol level being > 3
        Min after waking > 10
    '''
    all_mask = np.ones_like(data['bl_av_evecortisol'])==1
    mask = all_mask
    
    names = list(data.dtype.names)
    names = [ name for name in names if name.find('cortisol') > 0 ]
    names = [ name for name in names if name.find('bl') == 0 ]
    av_names = [ name for name in names if name.find('av') > 0 ]
    d1_names = [ name for name in names if name.find('_d1_') > 0 ]
    d2_names = [ name for name in names if name.find('_d2_') > 0 ]
    
    fig, axarr = plt.subplots(nrows=7, ncols=3, figsize = (8, 15))
    
    for j, name_list in enumerate( [ d1_names, d2_names, av_names ]):
        for i, name in enumerate(name_list):
            axarr[i,j].hist(data[name][data[name] <> 999], bins=10)
            # axarr[i].set_xlabel(name)
            #plt.boxplot(data[name][data[name] <> 999])
        #plt.suptitle(name_list)
    plt.show()
#--------------------------------------------------------------------

#====================================================================
# MAIN CODE
#====================================================================
# Run the main body of the script

#--------------------------------------------------------------------
# Define some variables
try:
    data_filename = str(sys.argv[1])
    selection_criteria_name = str(sys.argv[2])
except:
    print 'Check your input files'
    usage()
    sys.exit()

#data_filename = '/work/imagingA/mrimpact/workspaces/CORTISOL/IMPACT_CortisolMeasure_KW.txt'
#selection_criteria_name = '/home/kw401/CAMBRIDGE_SCRIPTS/MRIMPACT_SCRIPTS/Cortisol_SelectionCriteria.py'

#--------------------------------------------------------------------
# Import data
data, measure_dict = import_data(data_filename)

#--------------------------------------------------------------------
# Run the CortisolSelectionCriteria.py script
# This will import your various selection criteria
execfile(selection_criteria_name)

#--------------------------------------------------------------------
# Write in the selection columns
data = write_selection_columns(data, measure_dict)

#--------------------------------------------------------------------
# Run the various compare columns:
#   Compare within day:
#       maxam cortisol measure for separate days
#       cortisol awakening response
#       dayav
#       dayrange
data = run_comparisons_within_day(data, measure_dict)
#   Compare across days:
#       regular measures across days (t1 + t2) / 2
#       maxan and cortisol across days (t1 + t2) / 2
#       dayav
#       dayrange
data = run_comparisons_across_day(data, measure_dict)

#--------------------------------------------------------------------
# Run the data reporting function
data_report(data)

'''
Today is Lily Farris' 30th birthday! HAPPY BIRTHDAY LILY!
Miss you, love you
Kx
'''