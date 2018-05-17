# coding: utf-8
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker, load_only
from sqlalchemy.sql import func
from datetime import datetime
from SnackBar import history, user, inpayment, item, db
from collections import Counter
import os
import csv
import flask
# from scipy.signal import savgol_filter
import json

def main():

    # get no of users

    #noUsers = db.session.query(user).count()
    #print('Number of users is: {}'.format(noUsers))
    content = dict()

    tagsHours = ['00:00', '00:30', '01:00', '01:30', '02:00', '02:30', '03:00', '03:30', '04:00', '04:30',
                       '05:00', '05:30', '06:00', '06:30', '07:00', '07:30', '08:00', '08:30', '09:00', '09:30',
                       '10:00', '10:30', '11:00', '11:30', '12:00', '12:30', '13:00', '13:30', '14:00', '14:30',
                       '15:00', '15:30', '16:00', '16:30', '17:00', '17:30', '18:00', '18:30', '19:00', '19:30',
                       '20:00', '20:30', '21:00', '21:30', '22:00', '22:30', '23:00', '23:30', '24:00']

    tagsHoursLabels = ['00:00', '', '01:00', '', '02:00', '', '03:00', '', '04:00', '', '05:00', '', '06:00', '',
                       '07:00', '', '08:00', '', '09:00', '', '10:00', '', '11:00', '', '12:00', '', '13:00', '',
                       '14:00', '', '15:00', '', '16:00', '', '17:00', '', '18:00', '', '19:00', '', '20:00', '',
                       '21:00', '', '22:00', '', '23:00', '', '24:00']
    minTag = len(tagsHours)
    maxTag = 0


    allItems = item.query.filter(item.name != None , item.name != '')
    allItemID = [int(instance.itemid) for instance in allItems]

    # Info for Coffee
    for itemID in allItemID:
        histogram = db.session.query(history.itemid, history.date, history.userid). \
            filter(history.itemid == itemID).all()

        # Info item on weekhours
        histogramHours = list()
        for x in histogram:
            if x[1] is not None:
                histogramHours.append(x[1].time().replace(minute=00, second=0, microsecond=0))

        bla = list(sorted(Counter(histogramHours).items()))
        timeStamp = [x[0].strftime('%H:%M') for x in bla]

        for j, elem in enumerate(timeStamp):
            index = tagsHours.index(elem)
            minTag = min(minTag, index)
            maxTag = max(maxTag, index)

    minTag = max(minTag -1 , 0)
    maxTag = min(maxTag + 2, len(tagsHours))

    minTag = min(minTag, 9)
    maxTag = max(maxTag, 17)

    if minTag < maxTag:
        tagsHours = tagsHours[minTag:maxTag]
        tagsHoursLabels = tagsHoursLabels[minTag:maxTag]


    # Info for Coffe
    for itemID in allItemID:
        # itemID = 4

        itemtmp = db.session.query(item.name).filter(item.itemid == itemID).one()
        itemName = itemtmp[0]


        content[itemName] = dict()
        histogram = db.session.query(history.itemid, history.date, history.userid).\
                                filter(history.itemid == itemID).all()
        #print("Total number of consumed {} is : {}".format(itemName,len(histogram)))
        content[itemName]['total'] = len(histogram)

        # print(len(histogram))
        # Info item on weekday

        histogramDays = list()
        for x in histogram:
            if x[1] is not None:
                histogramDays.append(x[1].isoweekday())

        bla = list(sorted(Counter(histogramDays).items()))
        amount = [0 for x in range(7)]
        for elem in bla:
            amount[elem[0]-1] = elem[1]

        # amount = [x[1] for x in bla]
        timeStamp = [x[0] for x in bla]
        timeStamp = [x+1 for x in range(7)]
        content[itemName]['tagsDays'] = ['Monday' ,'Tuesday','Wednesday' ,'Thursday' , 'Friday' ,'Saturday' , 'Sunday' ]
        content[itemName]['amountDays'] = amount

        # Info item on weekhours
        histogramHours = list()
        for x in histogram:
            if x[1] is not None:
                histogramHours.append(x[1].time().replace(minute=30, second=0, microsecond=0))

        bla = list(sorted(Counter(histogramHours).items()))
        amount = [x[1] for x in bla]
        timeStamp = [x[0].strftime('%H:%M') for x in bla]
        # amountFiltered = savgol_filter(amount,51,3).tolist() 
        # print(amountFiltered[0::2])
        # print(timeStamp[0::2])
        # print(timeStamp)
        # print(amount)

        amountRaw = ['-' for x in range(len(tagsHours))]

        for j,elem in enumerate(timeStamp):
            amountRaw[tagsHours.index(elem)] = amount[j]
        
        # print(tagsHours)
        # print(amountRaw)

        content[itemName]['amountHours'] = amountRaw
        content[itemName]['tagsHours'] = tagsHours

        # Info item on month

        histogramMonth = list()
        for x in histogram:
            if x[1] is not None:
                histogramMonth.append(x[1].month)
        bla = list(sorted(Counter(histogramMonth).items()))
        timeStamp = [x for x in range(12)]
        # print(timeStamp)
        amount = [0 for x in range(12)]
        for elem in bla:
            amount[elem[0]-1] = elem[1]
        content[itemName]['amountMonth'] = amount
        content[itemName]['tagsMonth'] = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    return (content, tagsHoursLabels)


if __name__ == "__main__":
    main()




