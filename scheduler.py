#!/usr/bin/env python

"""
A mini webapp to generate icalendar files for people's timetables.
"""

__author__    = 'Henry de Valence'
__copyright__ = '(C) 2012 Henry de Valence'
__license__   = 'GPL'
__email__     = 'queenstimetables@hdevalence.ca'

import cherrypy
import datetime
import vobject

import loadslots

class Scheduler:
    def __init__(self,slotfilename):
        self.slots = loadslots.loadFromFile(slotfilename)
    @cherrypy.expose
    def index(self):
        html =  """
        <!DOCTYPE html>
        <html>
        <head>
        <link rel="stylesheet" type="text/css" href="style.css" />
        <title>Queen's Course Calendar Generator</title>
        </head>
        <body>
            <div id="page">
            <h1>Queen's Timetable Generator</h1>
            <div id="intro">
            <p>
            Enter up to six courses below and hit submit to generate an ICalendar
            file of your class schedule for use with e.g. Google Calendar, Microsoft Outlook,
            Mozilla Thunderbird, &c.
            </p>
            <p>
            You can enter the time as either a slot number in the 
            <a href="http://www.queensu.ca/registrar/currentstudents/coursetimetable/slotcharts.html">
            pre-SOLUS slot numbering scheme</a>,
            or as 
            comma-seperated list of times, e.g., "Mon2:30-4:00,Tue9:00-10:00,Fri12:00-3:00".
            </p>
            </div>
            <form align="center" id="theform" name="input" action="calendar.ics" method="get">
                <table>
                <tr><td></td> <td>Course Name</td> <td>Location</td> <td>Slot Number</td></tr>
        """
        for i in range(1,7):
            html += """
                <tr>
                    <td>Course %(i)d</td>
                    <td><input type="text" name="course%(i)dname"/></td>
                    <td><input type="text" name="course%(i)dlocation"/></td>
                    <td><input type="text" name="course%(i)dslot"/></td>
                </tr>
                """ % {'i':i}
        html += """
                </table>
                <input type="submit" value="Generate Calendar"/>
            </form>
            </div>
        """ + self.footer() + """
        </body>
        </html>"""
        return html

    def footer(self):
        return """
        <div id="footer">
        Created by Henry de Valence (ArtSci '13). 
        <a href="mailto:queenstimetables@hdevalence.ca">Send feedback by email</a>.
        </div>"""

    @cherrypy.expose
    def calendar_ics(self,**kwargs):
        #Build list of courses.
        courses = []
        for i in range(1,7):
            if kwargs['course%dname' % i] == '':
                continue
            courses.append({
                'name':kwargs['course%dname' %i],
                'location':kwargs['course%dlocation' %i],
                'slot':kwargs['course%dslot' %i]
                })
        for course in courses:
            if course['slot'] not in self.slots:
                try:
                    self.parseTimes(course['slot'])
                except IOError:
                    return self.invalidSlot(course)
        cal = vobject.iCalendar()
        for course in courses:
            self.addToCalendar(cal,course)
        cherrypy.response.headers['Content-Type']= 'text/calendar'
        return cal.serialize()

    def parseTimes(self,inputString):
        times = [_.strip() for _ in inputString.split(',')]
        output = []
        for time in times:
            day = time[0:3].lower()
            starttime, endtime = loadslots.toTimes(time[3:])
            output.append( (loadslots.weekdayOffsets[day], starttime, endtime) )
        self.slots[inputString] = output

    def addToCalendar(self,cal,course):
        termStart = datetime.date(2012,1,9)
        week = datetime.timedelta(7)
        #Add holidays
        holidays = []
        #Reading week
        for i in range(5):
            holidays.append( datetime.date(2012,2,20) + datetime.timedelta(i) )
        #Good Friday
        holidays.append( datetime.date(2012,4,6) )
        lectureCounter = 1
        #It would be 12, but for reading week, we miss a week, so it's 13.
        for weekNum in range(13):
            classtimes = self.slots[course['slot']]
            for dayOffset, startTime, endTime in classtimes:
                day = termStart + weekNum*week + datetime.timedelta(dayOffset)
                if day in holidays:
                    continue
                start = datetime.datetime.combine( day, startTime )
                end = datetime.datetime.combine( day, endTime )
                self.addLecture(cal,course,lectureCounter,start,end)
                lectureCounter += 1
    
    def addLecture(self,cal,course,lectNum,start,end):
        ev = cal.add('vevent')
        ev.add('summary').value = u'%s Lecture \u2116%d' %(course['name'],lectNum)
        ev.add('description').value = course['location']
        ev.add('dtstart').value = start
        ev.add('dtend').value = end
        ev.add('uid').value = datetime.datetime.utcnow().isoformat().replace(':','') + "@queenstimetables.hdevalence.ca"

    def invalidSlot(self,course):
        html= """
        <!DOCTYPE html>
        <html>
        <head>
        <link rel="stylesheet" type="text/css" href="style.css" />
        <title>Error!</title>
        </head>
        <body><div id="page"><div id="errortext">
        Something has gone terribly wrong!  <br/>
        We can't find timetable data for your course %(name)s,
        which you said had slot "%(slot)s". <br/><br/>
        If you think this is a website error, try emailing
        <a href="mailto:queenstimetables@hdevalence.ca">queenstimetables@hdevalence.ca</a>. <br/>
        </div></div>""" %course
        html += self.footer() + """</body></html>""" 
        return html




