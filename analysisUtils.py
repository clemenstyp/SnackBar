from sqlalchemy import *
from sqlalchemy.orm import sessionmaker, load_only
from sqlalchemy.sql import func
from datetime import datetime
from CoffeeList import history, user, inpayment, item
from collections import Counter
import os
import csv
import flask
# from scipy.signal import savgol_filter
import json

def main():
    dbuser = 'coffee'
    password = 'ilikecoffee'
    database = 'coffeelist'
    host = 'localhost'
    port = 5432

    #url = 'sqlite:///TestDB.db'
    url = 'postgresql://{}:{}@{}:{}/{}'
    url = url.format(dbuser, password, host, port, database)

    engine = create_engine(url)
    Session = sessionmaker(bind=engine)
    session = Session()

    itemid = 1

    # get user information for front page 

    userList = session.query(user.firstName, user.lastName, user.userid).all()

    # get rank by userid 
    userid = 37 
    itemid = 3 
    tmpQuery = session.query(user.userid, func.count(history.price)).\
                       outerjoin(history, and_(user.userid == history.userid,\
                                                history.itemid == itemid,\
                                                extract('month', history.date) == 4)).\
                       group_by(user.userid).\
                       order_by(func.count(history.price).desc()).all()

    # tmpQuery = session.query(history.userid, func.count(history.price)).\
    #               outerjoin(history, user, user.userid == history.userid).\
    #               filter(history.itemid == itemid).\
    #               filter(extract('month', history.date) == 4).\
    #               group_by(history.userid).\
    #               order_by(func.count(history.price).desc()).all()

    # print(tmpQuery)
    # print(len(tmpQuery))
    userID = [x[0] for x in tmpQuery]
    itemSUM = [x[1] for x in tmpQuery]

    # print(userID)
    # print(itemSUM)

    rank = userID.index(userid)+1
    idx = userID.index(userid)

    # get first by itemid
    # itemid = 1 

    itemList = session.query(item.itemid).order_by(item.itemid).all()
    leaderID = list()

    # print(itemList)
    for itemid in itemList:
        tmpQuery = session.query(history.userid, func.count(history.price)).\
                        filter(history.itemid == itemid).\
                        filter(extract('month', history.date) == 4).\
                        group_by(history.userid).\
                        order_by(func.count(history.price).desc()).first()

        leaderID.append(tmpQuery[0])

    # print(leaderID)


    # get no of users 
    noUsers = session.query(user).count()
    print('Number of users is: {}'.format(noUsers))
    content = dict()

    # Info for Coffe 
    for itemID, t in enumerate(range(4),1):
        # itemID = 4

        itemtmp = session.query(item.name).filter(item.itemid == itemID).one()
        itemName = itemtmp[0]


        content[itemName] = dict()
        histogram = session.query(history.itemid, history.date, history.userid).\
                                filter(history.itemid == itemID).all()
        print("Total number of consumed {} is : {}".format(itemName,len(histogram)))
        content[itemName]['total'] = len(histogram)

        # print(len(histogram))
        # Info item on weekday
        histogramDays = [x[1].isoweekday() for x in histogram]
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
        histogramHours = [x[1].time().replace(minute = 0,second=0,microsecond = 0) for x in histogram]
        bla = list(sorted(Counter(histogramHours).items()))
        amount = [x[1] for x in bla]
        timeStamp = [x[0].strftime('%H:%M') for x in bla]
        # amountFiltered = savgol_filter(amount,51,3).tolist() 
        # print(amountFiltered[0::2])
        # print(timeStamp[0::2])
        # print(timeStamp)
        # print(amount)

        tagsHours = ['00:00','01:00','02:00','03:00','04:00','05:00','06:00','07:00','08:00','09:00','10:00','11:00','12:00','13:00','14:00','15:00','16:00','17:00','18:00','19:00','20:00','21:00','22:00','23:00','24:00'] 
        amountRaw = [0 for x in range(len(tagsHours))]

        for j,elem in enumerate(timeStamp):
            amountRaw[tagsHours.index(elem)] = amount[j] 
        
        # print(tagsHours)
        # print(amountRaw)
        
        content[itemName]['amountHours'] = amountRaw
        content[itemName]['tagsHours'] = tagsHours

        # Info item on month
        histogramMonth = [x[1].month for x in histogram]
        bla = list(sorted(Counter(histogramMonth).items()))
        timeStamp = [x for x in range(12)]
        # print(timeStamp)
        amount = [0 for x in range(12)]
        for elem in bla:
            amount[elem[0]-1] = elem[1]
        content[itemName]['amountMonth'] = amount
        content[itemName]['tagsMonth'] = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    return (content)


if __name__ == "__main__":
    main()




