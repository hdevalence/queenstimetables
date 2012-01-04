#!/usr/bin/env python

"""
A short script to parse the Queen's University Slot System times.
"""

__author__    = 'Henry de Valence'
__copyright__ = '(C) 2012 Henry de Valence'
__license__   = 'GPL'
__email__     = 'queenstimetables@hdevalence.ca'


import datetime

def loadFromFile(fname):
    with open(fname,'r') as f:
        ll = f.readlines()
    slotDict = {}
    for line in ll:
        if line == '\n': 
            continue
        slot,day,timerange = line.split('\t')
        if slot != '':
            lastSlot = slot
            slotDict[lastSlot] = []
        starttime,endtime = toTimes(timerange)
        slotDict[lastSlot].append( (weekdayOffsets[day.strip().lower()],starttime,endtime) )
    return slotDict

weekdayOffsets = {
        'mon':0,
        'tue':1,
        'wed':2,
        'thu':3,
        'fri':4
        }


def toTimes(rangestring):
    """ Convert a time range string to two time objects. """
    start,sep,end = rangestring.partition('-')
    if " pm" in end:
        startH = start
        endH = end[0:-3]
        startM, endM = 0,0
    else:
        startH,sep,startM = start.partition(':')
        endH,sep,endM = end.partition(':')
    #There are no classes in the input file that begin before 8am
    if int(startH) < 8:
        starttime = datetime.time(12 + int(startH), int(startM) )
        endtime = datetime.time(12 + int(endH), int(endM) )
    else:
        starttime = datetime.time(int(startH), int(startM) )
        endtime = datetime.time(int(endH), int(endM) )
    return (starttime, endtime)

    

