#!/usr/bin/env python
"""
Name: Cortisol_PreProcessing.py

Created by Kirstie Whitaker
Contact information: kw401@cam.ac.uk

This script takes a tab delimited text file that has been
converted from an SPSS spreadsheet. It calculates the average
data across two days for waking, waking+30, evening measures of
cortisol. It also calculates (and then averages) the cortisol
awakening response, the maximum am value, daytime average and
daytime range.

The various selection criteria can be set in the
Cortisol_SelectionCriteria.py file and is passed as an argument.

The output is a tab delineated text file and a png file
(with the same name but different endings)

TO BE DONE:
    Filter by medication
    Possibly only output some of the information?

"""
#====================================================================
# IMPORTS
import numpy as np
import itertools as it
import sys
import os
import matplotlib.pylab as plt
import numpy.lib.recfunctions as rec
from matplotlib.ticker import MaxNLocator
import platform
import string
import re

sys.path.insert(0, '/work/imagingA/mrimpact/workspaces/CORTISOL/SCRIPTS')
sys.path.insert(0, 'C:\\Users\\Kirstie\\Dropbox\\GitHub\\GENERAL_CODE')

# Import Kirstie's personal scripts
import MyCoolFunctions as mcf
#====================================================================

#====================================================================
# FUNCTIONS
#====================================================================
def usage():
    print ( 'USAGE: Cortisol_PreProcessing.py '
                + ' <data_filename>'
                + ' <selection_criteria_filename>'
                + ' <output_filename>' )
    print ''
    print ( '\t<data_filename> is a TAB delineated file'
                + ' containing the cortisol data' )
    print ( '\t<selection_criteria_filename> is a python file that'
                + ' contains the answers (True or False) to'
                + ' selection criteria' )
    print ( '\t<output_filename> is, as it says, the TAB'
                + ' delineated output file')
    print ( '\tFor example:')
    print ('\t\t ./Cortisol_Preprocessing.py'
                + ' IMPACT_Cortisol_data.txt'
                + ' selection_criteria.py'
                + ' cortisol_output_April2013.txt' )
                
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
    data = np.genfromtxt(data_filename,
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

    # There is a 99 typo. Lets fix that here:
    for name in names:
        x = data[name]
        if not np.issubdtype(x.dtype, str):
            x[x==99] = 999

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

    # Use the following dictionary to identify the
    # various measures.
    # They are indexed by TIME of measurement
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

def keep_filter_subs(data, inc_sublist_filename, excl_sublist_filename):
    if os.path.isfile(inc_sublist_filename):
        inc_sublist = np.loadtxt(inc_sublist_filename, dtype=int)
        keep_mask = np.in1d(data['ID'], inc_sublist)
    else:
        keep_mask = np.ones(data['ID'].shape)==1
    if os.path.isfile(excl_sublist_filename):
        excl_sublist = np.loadtxt(excl_sublist_filename, dtype=int)
        excl_mask = np.logical_not(np.in1d(data['ID'], excl_sublist))
    else:
        excl_mask = np.ones(data['ID'].shape)==1
    
    mask = keep_mask * excl_mask
    return data[mask]
#--------------------------------------------------------------------

def excl_med_subs(data, medlist_file, medlist_special_cases_file):
    # Read in the meds column
    meds = data['bl_med_name']

    # Read in the exclude_meds list
    with open(medlist_file) as f:
        exclude_meds = f.read().splitlines()
    # And make sure all the words are uppercase
    exclude_meds = [ string.upper(med) for med in exclude_meds ]
    exclude_meds = [ med.strip() for med in exclude_meds ]

    # Read in the special cases
    with open(medlist_special_cases_file) as f:
        special_cases = f.read().splitlines()
    # And make sure these special cases are all upper case
    # and don't have any leading or trailing whitespace
    special_cases = [ string.upper(case) for case in special_cases ]
    special_cases = [ case.strip('"') for case in special_cases ]
    special_cases = [ case.strip() for case in special_cases ]

    # Create a mask that is all True (to start off with)
    mask = np.ones(meds.shape)==1

    # Loop through and remove all the special cases
    for i, med in enumerate(meds):
        med = med.strip('"')
        med = med.strip()
        med = string.upper(med)
        mask[i] = False if med.strip('"') in special_cases else mask[i]
    
    # Now loop through and remove any subject that has any of the 
    # exclude meds words in their meds column
    for i, med in enumerate(meds):
        for med_word in re.sub(',|;|"|\.| ','_', med).split('_'):
            med_word = string.upper(med_word)
            mask[i] = False if med_word in exclude_meds else mask[i]
    
    return data[mask]
    
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
    use_names = [ name for name in names if (name.find(measure_name) > 1) & (name.find('Use') == 0) ]
    
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
    use_day_data = np.zeros(data['ID'].shape)
    
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
    data = rec.append_fields(base = data,
                        names = 'bl_useDay',
                        data = use_day_data,
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
        calc_max_data = np.ones(data['ID'].shape)
        
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
                data = define_selection_column(data, in_column_name, out_column_name, ' < 3.')
            else:
                data = define_selection_column(data, in_column_name, out_column_name, '')

            '''
            # CRITERION: All cortisol comments have to be '1000'
            '''
            in_column_name = 'bl_d{day}_{time}comment'.format(day=day, time=measure_dict[time])
            out_column_name = 'Use_bl_d{day}_{time}cortisol_comment1000'.format(day=day, time=measure_dict[time])
            if comment_1000:
                data = define_selection_column(data, in_column_name, out_column_name, ' == str(1000)')
            else:
                data = define_selection_column(data, in_column_name, out_column_name, '')
    
            '''
            # CRITERION: Wake cortisol has to be acquired within 10 minutes of waking
            '''
            if time == 0:
                in_column_name = 'bl_d{day}_minawake'.format(day=day)
                out_column_name = 'Use_bl_d{day}_{time}cortisol_minawakeLt10'.format(day=day, time=measure_dict[time])
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
                        
    # And also include a copy of the mask
    data = rec.append_fields(base=data,
                        names=name_combo + '_mask',
                        data=mask,
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

        usevalue_1_name = 'Use_bl_d{day}_wakecortisol_Overall'.format(day=day)
        usevalue_2_name = 'Use_bl_d{day}_30mcortisol_Overall'.format(day=day)
        
        usevalue_1 = data[usevalue_1_name]
        usevalue_2 = data[usevalue_2_name]
        
        # We can't calculate the difference if there is only 1 data point
        # usevalue column is only 0s and 3s
        usevalue = (usevalue_1 * usevalue_2) * 3

        data = compare_columns(data, name_1, name_2, name_diff, usevalue, 'diff')
        
        #------------------------------------------------------------
        # Replace values that are negative with 999 if excl_neg_CAR is True
        if excl_neg_CAR:
            mask_excl_neg = data[name_diff] < 0
            data[name_diff][mask_excl_neg] = 999
        #------------------------------------------------------------
        
        # Calculate the maximum morning cortisol measure
        # defined as the largest of the two morning measures
        # and uses the same input data as the CAR
        # INPUT: name_1, name_2 (from above)
        # OUTPUT name_max
        name_max = 'bl_d{day}_maxamcortisol'.format(day=day)

        # but a different mask for the values to use
        # combining usevalue_1 and usevalue_2 with 
        # the mask_calc_max column of 1s and 0s
        calc_max_name = 'bl_d{day}_calc_max'.format(day=day)
        usevalue_calc_max = data[calc_max_name]

        usevalue_xor_1 = np.logical_xor(usevalue_1==1, usevalue_2==1) * usevalue_1
        usevalue_xor_2 = np.logical_xor(usevalue_1==1, usevalue_2==1) * usevalue_2
        usevalue[usevalue_xor_1==1] = 1
        usevalue[usevalue_xor_2==1] = 2

        usevalue = usevalue_calc_max * usevalue

        data = compare_columns(data, name_1, name_2, name_max, usevalue, 'max')
        
        #------------------------------------------------------------
        # Calculate the daytime average cortisol measure
        # defined as the difference between the daytime max
        # and the evening value
        name_1 = 'bl_d{day}_maxamcortisol'.format(day=day)
        name_2 = 'bl_d{day}_evecortisol'.format(day=day)
        name_av = 'bl_d{day}_dayAvcortisol'.format(day=day)
        
        # For maxam use the usevalue mask from the previous calculation
        # but binarize it to just 1s and 0s
        usevalue_1 = usevalue
        usevalue_1[usevalue <> 0] = 1
        # And get the use eve cortisol overall column for usevalue_2
        usevalue_2_name = 'Use_bl_d{day}_evecortisol_Overall'.format(day=day)
        usevalue_2 = data[usevalue_2_name]
        
        # You can't calculate the average or range if you only have one
        # datapoint!
        usevalue = ( usevalue_1 * usevalue_2 ) * 3

        data = compare_columns(data, name_1, name_2, name_av, usevalue, 'average')
        # And also calculate the range in cortisol values
        # throughout the day
        name_diff = 'bl_d{day}_dayRangecortisol'.format(day=day)
        data = compare_columns(data, name_2, name_1, name_diff, usevalue, 'diff')
    
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
        
        # Now to create the mask
        # Our first step is to look for either the Overall column,
        # or the mask column
        usedata_name_1 = 'Use_bl_d1_{time}cortisol_Overall'.format(time=measure_dict[time])
        usedata_name_2 = 'Use_bl_d2_{time}cortisol_Overall'.format(time=measure_dict[time])
        
        if usedata_name_1 in list(data.dtype.names):
            usedata_1 = data[usedata_name_1]
            usedata_2 = data[usedata_name_2]
            usevalue = ( usedata_1 * usedata_2 ) * 3

        else:
            usedata_name_1 = 'bl_d1_{time}cortisol_mask'.format(time=measure_dict[time])
            usedata_name_2 = 'bl_d2_{time}cortisol_mask'.format(time=measure_dict[time])
            usedata_1 = np.copy(data[usedata_name_1])
            usedata_2 = np.copy(data[usedata_name_2])
            usedata_1[usedata_1 > 0] = 1
            usedata_2[usedata_2 > 0] = 1
            usevalue = ( usedata_1 * usedata_2 ) * 3

        usevalue_xor_1 = np.logical_xor(usedata_1, usedata_2) * usedata_1
        usevalue_xor_2 = np.logical_xor(usedata_1, usedata_2) * usedata_2
        
        usevalue[usevalue_xor_1==1] = 1
        usevalue[usevalue_xor_2==1] = 2
        
        useday = data['bl_useDay']

        # Combine your day masks:
        # I can't think of a better way of writing this!!!
        for i in xrange(usevalue.shape[0]):
            if useday[i] == 0:
                usevalue[i] = 0
            elif useday[i] == 1:
                if usevalue[i] == 2:
                    usevalue[i] = 0
                elif usevalue[i] == 3:
                    usevalue[i] = 1
            elif useday[i] == 2:
                if usevalue[i] == 1:
                    usevalue[i] = 0
                elif usevalue[i] == 3:
                    usevalue[i] = 2
        
        data = compare_columns(data, name_1, name_2, name_av, usevalue, 'average')
    
    return data
#--------------------------------------------------------------------

def data_report(data, criteria_title):
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
    names = [ name for name in names if not name.find('mask') > 0 ]
    av_names = [ name for name in names if name.find('av') > 0 ]
    d1_names = [ name for name in names if name.find('_d1_') > 0 ]
    d2_names = [ name for name in names if name.find('_d2_') > 0 ]
    
    fig, axarr = plt.subplots(nrows=7, ncols=3, figsize = (8, 12), sharex='col', sharey='row')
    
    xlabels = [ 'Day 1', 'Day 2', 'Average' ]
    ylabels = [ 'Wake', 'Wake + 30min', 'Evening', 'CAR', 'max AM', 'Day Average', 'Day Range' ]

    for j, name_list in enumerate( [ d1_names, d2_names, av_names ]):
        for i, name in enumerate(name_list):
            mask = data[name]<>999
            if 'Use_{name}_Overall'.format(name=name) in list(data.dtype.names):
                mask_use = data['Use_{name}_Overall'.format(name=name)]==1
                mask = mask * mask_use
            else:
                mask_use = data['{name}_mask'.format(name=name)] <> 0
                mask = mask * mask_use
            axarr[i,j].hist(data[name][mask], bins=10)
            axarr[i,j].set_xlabel('cortisol value\n' + xlabels[j])
            axarr[i,j].set_ylabel(ylabels[i])
            xmajorlocator = MaxNLocator(5)
            axarr[i,j].xaxis.set_major_locator(xmajorlocator)
            ymajorlocator = MaxNLocator(5)
            axarr[i,j].yaxis.set_major_locator(ymajorlocator)
            n = np.sum([mask])
            plt.text( 0.8, 0.9,
                    'N: {n}'.format(n=n) ,
                    horizontalalignment = 'center' ,
                    verticalalignment = 'center' ,
                    transform = axarr[i,j].transAxes ,
                    fontsize = 10 )
            axarr[i,j].set_title(xlabels[j])
    
    [a.set_ylabel(ylabel='') for a in axarr[:,1:].reshape(-1)]
    [a.set_xlabel(xlabel='') for a in axarr[:(-1),:].reshape(-1)]
    [a.set_title(label='') for a in axarr[1:,:].reshape(-1)]
    
    # Line up all the yaxis labels
    # (they can jump around because the number of digits on the axis change)
    [a.yaxis.set_label_coords(-0.25, 0.5) for a in axarr[:,0].reshape(-1)]
    
    fig.subplots_adjust(top=0.85)
    plt.suptitle(criteria_title)
    fig_filename = os.path.splitext(output_filename)[0] + '.png'
    
    plt.savefig(fig_filename, dpi=None, facecolor='w', edgecolor='w',
          orientation='portrait', papertype=None, format=None,
          transparent=True, bbox_inches=None, pad_inches=0.1)
#--------------------------------------------------------------------

def data_save(data, output_filename):
    # This isn't too hard, except we're going to put a copy of the
    # measures we actually care about at the beginning!
    names = list(data.dtype.names)
    
    # Find all the columns that have 'av' in their title and not
    # and not '_mask'
    drop_names = [ name for name in names if (name.find('_av_') == -1) | (name.find('_mask') > 0) ]
    drop_names.pop(0)

    important_data = rec.drop_fields(data, drop_names, usemask=False, asrecarray=True)
    
    names = list(important_data.dtype.names)
    names[0] = 'SubID'
    important_data.dtype.names = names

    # Create two temporaray output_filenames:
    temp_filename1 = output_filename + '_temp1'
    temp_filename2 = output_filename + '_temp2'
    
    plt.rec2csv(data, temp_filename1, delimiter='\t', formatd=None, withheader=True)
    plt.rec2csv(important_data, temp_filename2, delimiter='\t', formatd=None, withheader=True)
    
    mcf.KW_paste(temp_filename2, temp_filename1, output_filename)
    mcf.KW_rmforce(temp_filename1)
    mcf.KW_rmforce(temp_filename2)
#--------------------------------------------------------------------
    
#====================================================================
# MAIN CODE
#====================================================================
# Run the main body of the script

#--------------------------------------------------------------------
# Define some variables
try:
    data_filename = sys.argv[1]
    selection_criteria_name = sys.argv[2]
    output_filename = sys.argv[3]
except:
    print 'Check your input files'
    usage()
    sys.exit()

#--------------------------------------------------------------------
# Import data
data, measure_dict = import_data(data_filename)

#--------------------------------------------------------------------
# Run the CortisolSelectionCriteria.py script
# This will import your various selection criteria
execfile(selection_criteria_name)

# If you have a sublist filter on then keep only those subjects
if filter_subs:
    os.path.isfile(include_subs_list)
    try:
        include_subs_file = include_subs_list
    except:
        include_subs_file = ' '
    try:
        exclude_subs_file = exclude_subs_list
    except:
        exclude_subs_file = ' '
        
    data = keep_filter_subs(data, include_subs_file, exclude_subs_file)

if excl_med:
    data = excl_med_subs(data, medlist_file, medlist_special_cases_file)
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
data_report(data, criteria_title)

#--------------------------------------------------------------------
# Save the data
data_save(data, output_filename)

#--------------------------------------------------------------------

'''
Today is Lily Farris' 30th birthday! HAPPY BIRTHDAY LILY!
Miss you, love you
Kx
'''