from datetime import datetime

from Snackbar.Helper.Bimail import Bimail
from Snackbar.Helper.Database import settings_for


def send_reminder(curuser):
    if curuser.email and curuser.email != '':
        curn_bill_float = curuser.calculate_account_balance()
        minimum_balance = float(settings_for('minimumBalance'))
        if curn_bill_float <= minimum_balance:
            currbill = '{0:.2f}'.format(curuser.calculate_account_balance())
            # print(instance.firstName)
            # print(currbill)
            mymail = Bimail('SnackBar Reminder', ['{}'.format(curuser.email)])
            mymail.sendername = settings_for('mailSender')
            mymail.sender = settings_for('mailSender')
            mymail.servername = settings_for('mailServer')
            # start html body. Here we add a greeting.
            mymail.htmladd(
                'Hallo {} {},<br><br>du hast nur noch wenig Geld auf deinem SnackBar Konto ({} €). '
                'Zahle bitte ein bisschen Geld ein, damit wir wieder neue Snacks kaufen können!'
                '<br><br>Ciao,<br>SnackBar Team [{}]<br><br><br><br>---------<br><br><br><br>'
                'Hello {} {},<br><br>your SnackBar balance is very low ({} €). '
                'Please top it up with some money!<br><br>Ciao,<br>SnackBar Team [{}]'.format(
                    curuser.firstName, curuser.lastName, currbill, settings_for('snackAdmin'),
                    curuser.firstName,
                    curuser.lastName, currbill, settings_for('snackAdmin')))
            # Further things added to body are separated by a paragraph, so you do not need to
            # worry about newlines for new sentences here we add a line of text and an html table
            # previously stored in the variable
            # add image chart title
            # attach another file
            # mymail.htmladd('Ciao,<br>SnackBar Team [Clemens Putschli (C5-315)]')
            # mymail.addattach([os.path.join(fullpath, filename)])
            # send!
            # print(mymail.htmlbody)
            mymail.send()


def send_email(curuser, curitem):
    if curuser.email and curuser.email != '':
        if settings_for('instantMail') == 'true':
            currbill = '{0:.2f}'.format(curuser.calculate_account_balance())
            # print(instance.firstName)
            # print(currbill)
            mymail = Bimail('SnackBar++ ({} {})'.format(curuser.firstName, curuser.lastName),
                            ['{}'.format(curuser.email)])
            mymail.sendername = settings_for('mailSender')
            mymail.sender = settings_for('mailSender')
            mymail.servername = settings_for('mailServer')
            # start html body. Here we add a greeting.

            today = datetime.now().strftime('%Y-%m-%d %H:%M')
            mymail.htmladd(
                'Hallo {} {}, <br>SnackBar hat gerade "{}" ({} €) für dich GEBUCHT! '
                '<br><br> Dein Guthaben beträgt jetzt {} € <br><br>'.format(
                    curuser.firstName, curuser.lastName, curitem.name, curitem.price, currbill))
            mymail.htmladd('Ciao,<br>SnackBar Team [{}]'.format(settings_for('snackAdmin')))
            mymail.htmladd('<br><br>---------<br><br>')
            mymail.htmladd(
                'Hello {} {}, <br>SnackBar has just ORDERED {} ({} €) for you! '
                '<br><br> Your balance is now {} € <br><br> '.format(
                    curuser.firstName, curuser.lastName, curitem.name, curitem.price, currbill))
            # Further things added to body are separated by a paragraph, so you do not need to worry
            # about newlines for new sentences here we add a line of text and an html table previously
            # stored in the variable
            # add image chart title
            # attach another file
            mymail.htmladd('Ciao,<br>SnackBar Team [{}]'.format(settings_for('snackAdmin')))

            mymail.htmladd('<br><br>---------<br>Registered at: {}'.format(today))

            # mymail.addattach([os.path.join(fullpath, filename)])
            # send!
            # print(mymail.htmlbody)
            mymail.send()


def send_bill_to(user, total_cash, total_bill, users, bill_date):
    if user.email and user.email != '':

        today = bill_date.strftime('%Y-%m-%d')

        header = "Bill SnackBar: {}".format(today)

        toptable = """
            <table>
            <thead><tr><th colspan="2">Total</th></tr></thead>
            <tbody>
            <tr><td>Total Cash: </td><td>{:0.2f} €</td></tr>
            <tr><td>Total Open Bill: </td><td>{:0.2f} €</td></tr>
            <tr><td><b>Resulting Sum: </b></td><td><b>{:0.2f} €</b></td></tr>
            </tbody>
            </table><br/>
            """.format(total_cash, total_bill, (total_cash - total_bill))

        bottomtable = """
            <table>
            <thead><tr><th>Name</th><th>Bill</th></tr></thead>
            <tbody>
            """
        for aUser in users:
            bottomtable = bottomtable + "<tr><td>{}</td><td>{:0.2f} €</td></tr>".format(aUser['name'], aUser['bill'])

        bottomtable = bottomtable + """
            <tr></tr>
            <tr><td><b>SUM:</b></td><td><b>{:0.2f} €</b></td></tr>
            </tbody>
            </table><br/>
        """.format(total_bill)

        # print(instance.firstName)
        # print(currbill)
        mymail = Bimail(header, ['{}'.format(user.email)])
        mymail.sendername = settings_for('mailSender')
        mymail.sender = settings_for('mailSender')
        mymail.servername = settings_for('mailServer')
        # start html body. Here we add a greeting.
        mymail.htmladd("""
        <b>{}</b>
        <br/><br/>
        {}
        {}
        """.format(header, toptable, bottomtable))

        # Further things added to body are separated by a paragraph, so you do not need to
        # worry about newlines for new sentences here we add a line of text and an html table
        # previously stored in the variable
        # add image chart title
        # attach another file
        # mymail.htmladd('Ciao,<br>SnackBar Team [Clemens Putschli (C5-315)]')
        # mymail.addattach([os.path.join(fullpath, filename)])
        # send!
        # print(mymail.htmlbody)
        mymail.send()


def send_email_new_user(curuser):
    if curuser.email and curuser.email != '':
        mymail = Bimail('SnackBar User Created', ['{}'.format(curuser.email)])
        mymail.sendername = settings_for('mailSender')
        mymail.sender = settings_for('mailSender')
        mymail.servername = settings_for('mailServer')
        # start html body. Here we add a greeting.
        mymail.htmladd(
            'Hallo {} {},<br><br>ein neuer Benutzer wurde mit dieser E-Mail Adresse erstellt. Solltest du diesen '
            'Acocunt nicht erstellt habe, melde dich bitte bei {}.<br><br>Ciao,<br>SnackBar Team [{}]'
            '<br><br><br><br>---------<br><br><br><br>'
            'Hello {} {},<br><br>a new User has been created with this mail address. If you have not created this '
            'Acocunt, please contact {}.<br><br>Ciao,<br>SnackBar Team [{}]'.format(
                curuser.firstName, curuser.lastName, settings_for('snackAdmin'),
                settings_for('snackAdmin'),
                curuser.firstName,
                curuser.lastName, settings_for('snackAdmin'), settings_for('snackAdmin')))
        # Further things added to body are separated by a paragraph, so you do not need to worry about
        # newlines for new sentences here we add a line of text and an html table previously stored
        # in the variable
        # add image chart title
        # attach another file
        # mymail.htmladd('Ciao,<br>SnackBar Team [Clemens Putschli (C5-315)]')
        # mymail.addattach([os.path.join(fullpath, filename)])
        # send!
        # print(mymail.htmlbody)
        mymail.send()
