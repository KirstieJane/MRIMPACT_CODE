#!/usr/bin/env python

"""
This is your options file for RandomiseSetup.py

Basically, this is where you define your groups,
measures of interest, and covariates of no interest
"""
#----------------------------------------------------------
# Decision: Require all measures (and covars) for participant
# to be included in analyses?
#----------------------------------------------------------
# If you do require all measures then you limit the number
# of participants you can include BUT you simplify your
# demographics etc section of you paper because you aren't
# changing the population based on which test you do.
req_all_measures = False

#----------------------------------------------------------
# Measures of interest
#----------------------------------------------------------
# These will all be added into your various columns
# with +1 and -1 contrasts
# For any TTests there will also be interaction
# designs created
#measures = [ 'SMFQ', 'STAIS', 'STAIT', 'Age', 'Male', 'Meds' ]
measures = [ 'SMFQ', 'WakeCort' ]

#----------------------------------------------------------
# Covariates of no interest
#----------------------------------------------------------
# All combinations of these (including none) will be added
# to all your models, but not tested.
covars = [ 'Age', 'Male', 'Meds' ]

#----------------------------------------------------------
# Groups
#----------------------------------------------------------
# If you'd like to split on any variable, defining groups
# based, for example on gender, diagnosis, if they have
# a particular measure etc, then you need to fill in 
# the information here
split_vars = [ 'Depressed', 'UsableCort' ]

group_dict = dict()
group_dict['Depressed_0'] = 'Con'
group_dict['Depressed_1'] = 'Dep'
group_dict['Depressed_2'] = 'All'
group_dict['Meds_0'] = 'NoMed'
group_dict['Meds_1'] = 'Med'
group_dict['Meds_2'] = 'IgMed'
group_dict['UsableCort_0'] = 'NoCort'
group_dict['UsableCort_1'] = 'Cort'
group_dict['UsableCort_2'] = 'IgCort'
group_dict['Male_0'] = 'Female'
group_dict['Male_1'] = 'Male'
group_dict['Male_2'] = 'IgGender'

##########
# NOTE:
# Inputting this information could be explained better
# I'm just not sure how to!
##########
#------------------------------------------------
# Create the groups we're going to investigate
#
# All (every subject that meets the mask_all criteria)
# Dep and Con (splitting by group)
# Med (splitting by medication)
# Cort (splitting by whether or not we have usable cortisol data)
#
# EG: Dep_Med_Cort --> Depressed subjects who are on medication
#                      and have usable cortisol data
#     Con_IgMed_NoCort --> Control subjects who may or may not be
#                          on anti-depressant medication and do
#                          not have cortisol measures
#
# There will be a correlations directory and a t-test dir
# Because there are now loads more t-tests to run
# not just the comparisons of depressed vs non-depressed
# but also the med vs no med etc

# I'm going to use a dictionary to translate the names
# of the split vars (as named in the behaviour file)
# into the group names for the design files
