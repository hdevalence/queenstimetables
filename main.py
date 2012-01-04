#!/usr/bin/env python

import cherrypy
import scheduler

scheduleFile = "textonly.txt"

cherrypy.server.socket_port = 80
cherrypy.server.socket_host = '0.0.0.0'
cherrypy.server.thread_pool_max = 10

s = scheduler.Scheduler(scheduleFile)

cherrypy.quickstart(s)

