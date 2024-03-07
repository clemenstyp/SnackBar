from collections import Counter
from datetime import timedelta

from Snackbar import db, app
from Snackbar.Models.History import History
from Snackbar.Models.Item import Item


def get_analysis():
    with app.app_context():
        # get no of users

        # noUsers = db.session.query(User).count()
        # print('Number of users is: {}'.format(noUsers))
        content = dict()

        tags_hours = ['00:00', '01:00', '02:00', '03:00', '04:00', '05:00', '06:00', '07:00', '08:00', '09:00', '10:00',
                      '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00',
                      '22:00', '23:00']
        min_tag = len(tags_hours)
        max_tag = 0

        all_items = Item.query.filter(Item.name is not None, Item.name != '')
        all_item_id = [int(instance.itemid) for instance in all_items]

        # Info for Coffee
        for itemID in all_item_id:
            histogram = db.session.query(History.itemid, History.date, History.userid). \
                filter(History.itemid == itemID).all()

            # Info Item on weekhours
            histogram_hours = list()
            for x in histogram:
                if x[1] is not None:
                    histogram_hours.append(x[1].time().replace(minute=0, second=0, microsecond=0))

            bla = list(sorted(Counter(histogram_hours).items()))
            time_stamp = [x[0].strftime('%H:%M') for x in bla]

            for j, elem in enumerate(time_stamp):
                index = tags_hours.index(elem)
                min_tag = min(min_tag, index)
                max_tag = max(max_tag, index)

        min_tag = max(min_tag - 1, 0)
        max_tag = min(max_tag + 2, len(tags_hours))

        min_tag = min(min_tag, 9)
        max_tag = max(max_tag, 17)

        if min_tag < max_tag:
            tags_hours = tags_hours[min_tag:max_tag]

        # Info for Coffe
        for itemID in all_item_id:
            # itemID = 4

            itemtmp = db.session.query(Item.name).filter(Item.itemid == itemID).one()
            item_name = itemtmp[0]

            content[item_name] = dict()
            histogram = db.session.query(History.itemid, History.date, History.userid). \
                filter(History.itemid == itemID).all()
            # print("Total number of consumed {} is : {}".format(itemName,len(histogram)))
            if len(histogram) > 1:
                oldest_date = histogram[0][1]
                newest_date = histogram[-1][1]
                histogram_delta = newest_date - oldest_date
                second_delta = histogram_delta.seconds
            else:
                second_delta = 3600.0
                histogram_delta = timedelta(hours=1)

            content[item_name]['total'] = len(histogram)

            # print(len(histogram))
            # Info Item on weekday

            histogram_days = list()
            for x in histogram:
                if x[1] is not None:
                    histogram_days.append(x[1].isoweekday())

            bla = list(sorted(Counter(histogram_days).items()))
            # noinspection PyUnusedLocal
            amount = [0 for x in range(7)]
            for elem in bla:
                amount[elem[0] - 1] = elem[1]

            hour_delta = second_delta / 3600
            day_delta = hour_delta / 24
            total_day_delta = day_delta + histogram_delta.days
            total_day_delta = max(total_day_delta, 1)
            week_delta = total_day_delta / 7

            # for i in range(len(amount)):
            #     amount[i] = amount[i] / week_delta

            # amount = [x[1] for x in bla]
            content[item_name]['tagsDays'] = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
                                              'Sunday']
            content[item_name]['amountDays'] = amount

            time_stamp = [x[0] for x in bla]
            time_stamp = [x + 1 for x in range(7)]

            # Info Item on weekhours
            histogram_minutes = list()
            for x in histogram:
                if x[1] is not None:
                    histogram_minutes.append(
                        x[1].replace(minute=30, second=0, microsecond=0, month=1, day=1, year=2000))

            histogram_minutes_sorted = list(sorted(Counter(histogram_minutes).items()))

            all_minute_coffee = list()
            hour_after = None

            for j, element in enumerate(histogram_minutes_sorted):
                time_stamp = element[0]
                before = time_stamp.replace(minute=0, second=0, microsecond=0, month=1, day=1, year=2000)
                after = time_stamp.replace(minute=0, second=0, microsecond=0, month=1, day=1, year=2000)
                after = after + timedelta(hours=1)

                if before != hour_after and hour_after is not None:
                    all_minute_coffee.append((hour_after, 0))
                    all_minute_coffee.append((before, 0))

                if hour_after is None:
                    all_minute_coffee.append((before, 0))

                hour_after = after
                all_minute_coffee.append((time_stamp, element[1]))

            if hour_after is not None:
                all_minute_coffee.append((hour_after, 0))

            amount_points = []
            for j, element in enumerate(all_minute_coffee):
                time_stamp = element[0]
                time_string = time_stamp.strftime('%H:%M')
                amount_points.append({'y': element[1], 'x': time_string})

            # print(amountPoints)
            # print(amountRaw)

            # for i in range(len(amount_points)):
            #     amount_points[i]['y'] = amount_points[i]['y'] / total_day_delta

            content[item_name]['amountPoints'] = amount_points

            # Info Item on month

            histogram_month = list()
            for x in histogram:
                if x[1] is not None:
                    histogram_month.append(x[1].month)
            bla = list(sorted(Counter(histogram_month).items()))
            time_stamp = [x for x in range(12)]
            amount_month = [0 for x in range(12)]
            for elem in bla:
                amount_month[elem[0] - 1] = elem[1]

            month_delta = total_day_delta / 30
            # for i in range(len(amount_month)):
            #     amount_month[i] = amount_month[i] / month_delta

            content[item_name]['amountMonth'] = amount_month
            content[item_name]['tagsMonth'] = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct',
                                               'Nov',
                                               'Dec']

        return content, tags_hours
