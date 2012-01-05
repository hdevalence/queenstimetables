#!/usr/bin/env python
#coding:utf8

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

MAX_COURSES = 8

class Scheduler:
    def __init__(self,slotfilename):
        self.slots = loadslots.loadFromFile(slotfilename)
    def header(self):
        return u"""
        <!DOCTYPE html>
        <html>
        <head>
        <link rel="stylesheet" type="text/css" href="style.css" />
        <link href='http://fonts.googleapis.com/css?family=Open+Sans:400,300&subset=latin' rel='stylesheet' type='text/css'>
        <title>Queen’s Course Calendar Generator</title>
        <script type="text/javascript">
            var _gaq = _gaq || []; _gaq.push(['_setAccount', 'UA-28106132-1']); _gaq.push(['_trackPageview']); 
            (function() {
            var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
            ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
            var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
            })();
        </script>
        </head>
        """
    @cherrypy.expose
    def index(self):
        html = self.header() + u"""
        <body onload="addCourse()">
            <script type="text/javascript">
            var courseId = 0;
            function addCourse() 
            {
                courseId++;
                var li = document.getElementById("courserow" + courseId);
                li.style.display="inline";
            }
            </script>
            <div id="page">
            <h1>Queen’s Timetable Generator</h1>
            <div id="intro" >
                <div class="step">
                    <h2>Step 1</h2>
                    Add the names of your courses, e.g., “MATH-414”, or “Galois Theory”.
                    Leave fields blank to omit them.
                </div>
                <div class="step">
                    <h2>Step 2</h2>
                    Add their times and locations. Times can be either
                    a 
                    <a href="http://www.queensu.ca/registrar/currentstudents/coursetimetable/slotcharts.html">
            pre-SOLUS slot number</a>, or a list like “Mon 2:30-4:00, Tue 9:00-10:00”.
                </div>
                <div class="step">
                    <h2>Step 3</h2>
                    Click “Generate” to get a file to import into
                    your favorite calendar program.
                </div>
            </div>
            <div id="theform">
            <form align="center" name="input" action="calendar.ics" method="get">
            <ul id="courselist">
        """
        for i in range(1,MAX_COURSES +1):
            html += """
            <li class="courserow" id="courserow%(i)d">
            <ul>
                <li class="subrow" id="course%(i)d">
                <input class="courseitem" type="text"
                    name="course%(i)dslot" placeholder="Lecture Slot/Time">
                <input class="courseitem" type="text" 
                    name="course%(i)dlocation" placeholder="Lecture Location">
                <input class="courseitem" type="text" 
                    name="course%(i)dname" placeholder="Course Name">
                <br style="clear:both;">
                </li>
                <li class="subrow" id="tutorial%(i)d">
                <input class="courseitem" type="text"
                    name="tutorial%(i)dslot" placeholder="Tutorial Slot/Time">
                <input class="courseitem" type="text"
                    name="tutorial%(i)dlocation" placeholder="Tutorial Location">
                <br style="clear:both;">
                </li>
            </ul>
            </li>
            """ % {'i':i}
        html += """
                </ul>
                <button id="addcourse" type="button" onclick="addCourse()">Add Course</button>
                <input id="engage" type="submit" value="Generate Calendar"/>
            </form>
            </div>
            </div>
        """ + self.footer()
        return html

    def footer(self):
        return """
        <div id="footer">
        Created by Henry de Valence (ArtSci '13). 
        <a href="mailto:queenstimetables@hdevalence.ca">Send feedback by email</a>.
        </div>
        </body>
        </html>
        """

    @cherrypy.expose
    def calendar_ics(self,**kwargs):
        #Build list of courses.
        courses = []
        for i in range(1,MAX_COURSES +1):
            if kwargs['course%dname' % i] == '':
                continue
            courses.append({
                'name':kwargs['course%dname' %i],
                'location':kwargs['course%dlocation' %i],
                'slot':kwargs['course%dslot' %i],
                'tutlocation':kwargs['tutorial%dlocation' %i],
                'tutslot':kwargs['tutorial%dslot' %i]
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
        tutorialCounter = 1
        #It would be 12, but for reading week, we miss a week, so it's 13.
        for weekNum in range(13):
            classtimes = self.slots[course['slot']]
            for dayOffset, startTime, endTime in classtimes:
                day = termStart + weekNum*week + datetime.timedelta(dayOffset)
                if day not in holidays:
                    summary = u'%s Lecture \u2116%d' %(course['name'],lectureCounter)
                    self.addEvent(cal,summary,course['location'],day, startTime, endTime)
                    lectureCounter += 1
            if course['tutslot'] != '':
                tuttimes = self.slots[course['tutslot']]
                for dayOffset, startTime, endTime in tuttimes:
                    day = termStart + weekNum*week + datetime.timedelta(dayOffset)
                    if day not in holidays:
                        summary = u'%s Tutorial \u2116%d' %(course['name'],tutorialCounter)
                        self.addEvent(cal,summary,course['tutlocation'],day, startTime, endTime)
                        tutorialCounter += 1
    
    def addEvent(self,cal,summary,location,day,startTime,endTime):
        start = datetime.datetime.combine( day, startTime )
        end = datetime.datetime.combine( day, endTime )
        ev = cal.add('vevent')
        ev.add('summary').value = summary
        ev.add('description').value = location
        ev.add('dtstart').value = start
        ev.add('dtend').value = end
        ev.add('uid').value = datetime.datetime.utcnow().isoformat().replace(':','') + "@queenstimetables.hdevalence.ca"

    def invalidSlot(self,course):
        html= self.header() + u"""
        <body><div id="page"><div id="errortext">
        Something has gone terribly wrong!  <br/>
        We can't find timetable data for your course %(name)s,
        which you said had slot "%(slot)s". <br/><br/>
        If you think this is a website error, try emailing
        <a href="mailto:queenstimetables@hdevalence.ca">queenstimetables@hdevalence.ca</a>. <br/>
        </div></div>""" %course
        html += self.footer() 
        return html




