#!/usr/bin/env python

import cherrypy
import scheduler

scheduleFile = "textonly.txt"

import os.path
conf = os.path.join(os.path.dirname(__file__), 'config.conf')

s = scheduler.Scheduler(scheduleFile)

cherrypy.quickstart(s,config=conf)

