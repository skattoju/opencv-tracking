#! /usr/bin/env python

print "OpenCV Python version of lkdemo"

import sys
import time
import sched
import Queue
from threading import Timer

# import the necessary things for OpenCV
from opencv import cv
from opencv import highgui

#############################################################################
# some "constants"

win_size = 10
MAX_COUNT = 500

#############################################################################
# some "global" variables

image = None
pt = None
add_remove_pt = False
flags = 0
night_mode = False
need_to_init = False
# the default parameters
quality = 0.01
min_distance = 10
tevent = Queue.Queue()

#############################################################################
# the mouse callback

# the callback on the trackbar
def on_mouse (event, x, y, flags, param):

    # we will use the global pt and add_remove_pt
    global pt
    global add_remove_pt
    
    if image is None:
        # not initialized, so skip
        return

    if event == highgui.CV_EVENT_LBUTTONDOWN:
        # user has click, so memorize it
        pt = cv.cvPoint (x, y)
        add_remove_pt = True

def reinit():
  need_to_init = True
  tevent.put(s1.enter(1,1,reinit,()))
  print 'starting timer'
  
def stop():
  while not s1.empty:
    s1.cancel(tevent.get())
  print 'stopping timer'
  
# the timer that triggers feature refresh events
#t = Timer(1.0,reinit)
s1 = sched.scheduler(time.time,time.sleep)
tevent.put(s1.enter(1,1,reinit,()))
#############################################################################
# so, here is the main part of the program

if __name__ == '__main__':

    try:
        # try to get the device number from the command line
        device = int (sys.argv [1])

        # got it ! so remove it from the arguments
        del sys.argv [1]
    except (IndexError, ValueError):
        # no device number on the command line, assume we want the 1st device
        device = 0

    if len (sys.argv) == 1:
        # no argument on the command line, try to use the camera
        capture = highgui.cvCreateCameraCapture (device)

    else:
        # we have an argument on the command line,
        # we can assume this is a file name, so open it
        capture = highgui.cvCreateFileCapture (sys.argv [1])            

    # check that capture device is OK
    if not capture:
        print "Error opening capture device"
        sys.exit (1)
        
    # display a small howto use it
    print "Hot keys: \n" \
          "\tESC - quit the program\n" \
          "\tr - auto-initialize tracking\n" \
          "\tc - delete all the points\n" \
          "\tn - switch the \"night\" mode on/off\n" \
          "To add/remove a feature point click it\n"

    # first, create the necessary windows
    highgui.cvNamedWindow ('LkDemo', highgui.CV_WINDOW_AUTOSIZE)

    # register the mouse callback
    highgui.cvSetMouseCallback ('LkDemo', on_mouse, None)

    # run reinit every 1 second.
    # s1.run()
    t2 = time.time()
    
    while 1:
        # do forever

        #time stamp for current frame
        t1 = time.time()

        #reinit features every 5 seconds 
        if(t1 - t2 > 5):
	  need_to_init = True
	  t2 = t1
        
        # 1. capture the current image
        frame = highgui.cvQueryFrame (capture)
        if frame is None:
            # no image captured... end the processing
            break

        if image is None:
            # create the images we need
            image = cv.cvCreateImage (cv.cvGetSize (frame), 8, 3)
            grey = cv.cvCreateImage (cv.cvGetSize (frame), 8, 1)
            prev_grey = cv.cvCreateImage (cv.cvGetSize (frame), 8, 1)
            pyramid = cv.cvCreateImage (cv.cvGetSize (frame), 8, 1)
            prev_pyramid = cv.cvCreateImage (cv.cvGetSize (frame), 8, 1)
            eig = cv.cvCreateImage (cv.cvGetSize (frame), cv.IPL_DEPTH_32F, 1)
            temp = cv.cvCreateImage (cv.cvGetSize (frame), cv.IPL_DEPTH_32F, 1)
            points = [[], []]

        # copy the frame, so we can draw on it
        cv.cvCopy (frame, image)

        # create a grey version of the image
        cv.cvCvtColor (image, grey, cv.CV_BGR2GRAY)

        if night_mode:
            # night mode: only display the points
            cv.cvSetZero (image)

        if need_to_init:
            # we want to search all the good points
            # create the wanted images
            
            # search the good points
            points [1] = cv.cvGoodFeaturesToTrack (
                grey, eig, temp,
                MAX_COUNT,
                quality, min_distance, None, 3, 0, 0.04)
            
            # refine the corner locations
            cv.cvFindCornerSubPix (
                grey,
                points [1],
                cv.cvSize (win_size, win_size), cv.cvSize (-1, -1),
                cv.cvTermCriteria (cv.CV_TERMCRIT_ITER | cv.CV_TERMCRIT_EPS,
                                   20, 0.03))
                                               
        elif len (points [0]) > 0:
            # we have points, so display them

            # calculate the optical flow
	    # documentation is in the opencv reference manual
	    # points[0] --> features in previous frame
	    # points[1] --> features in current frame

            [points [1], status], tracking_error = cv.cvCalcOpticalFlowPyrLK (
                prev_grey, grey, prev_pyramid, pyramid,
                points [0], 			#previous_features
		len (points [0]),
                (win_size, win_size),
		3,
                len (points [0]),
                None,			     
                cv.cvTermCriteria (cv.CV_TERMCRIT_ITER|cv.CV_TERMCRIT_EPS,
                                   20, 0.03), 	#criteria
                flags)
            
            # initializations
            point_counter = -1
            new_points = []
            velocities = [[],[]]
            old_points = points[0]
            for the_point in points[1]:
                # go through all the points

                # increment the counter
                point_counter += 1
                
                if add_remove_pt:
                    # we have a point to add, so see if it is close to
                    # another one. If yes, don't use it
                    dx = pt.x - the_point.x
                    dy = pt.y - the_point.y
                    if dx * dx + dy * dy <= 25:
                        # too close
                        add_remove_pt = 0
                        continue

                if not status [point_counter]:
                    # we will disable this point
                    continue

                # this point is a correct point
                new_points.append (the_point)

                # draw the current point
                cv.cvCircle (image,
                             cv.cvPointFrom32f(the_point),
                             3, cv.cvScalar (0, 255, 0, 0),
                             -1, 8, 0)

		# draw the flow vector
		if status[point_counter]:
			dx1 = old_points[point_counter].x - the_point.x
			dy1 = old_points[point_counter].y - the_point.y
			
			if dx1 * dx1 + dy1 * dy1 <= 500:
				cv.cvLine(image, 
					cv.cvPointFrom32f(old_points[point_counter]),
					cv.cvPointFrom32f(the_point),
					cv.cvScalar(0,255,0,0), 2)
					
				#print 'velocity: ',dx1/(time.time()-t1),dy1/(time.time()-t1)
				velocities[0].append(dx1/(time.time()-t1))
				velocities[1].append(dy1/(time.time()-t1))

				
            # set back the points we keep
            points [1] = new_points
            if len(velocities[0]) != 0 and len(velocities[1]) != 0:
		vavgx = sum(velocities[0])/len(velocities[0])
		vavgy = sum(velocities[1])/len(velocities[1])
	    else:
		vavgx = 0
		vavgy = 0
            print "velocity",vavgx,vavgy
            
        if add_remove_pt:
            # we want to add a point
            points [1].append (cv.cvPointTo32f (pt))

            # refine the corner locations
            points [1][-1] = cv.cvFindCornerSubPix (
                grey,
                [points [1][-1]],
                cv.cvSize (win_size, win_size), cv.cvSize (-1, -1),
                cv.cvTermCriteria (cv.CV_TERMCRIT_ITER | cv.CV_TERMCRIT_EPS,
                                   20, 0.03))[0]

            # we are no more in "add_remove_pt" mode
            add_remove_pt = False

        # swapping
        prev_grey, grey = grey, prev_grey
        prev_pyramid, pyramid = pyramid, prev_pyramid
        points [0], points [1] = points [1], points [0]
        need_to_init = False
        
        # we can now display the image
        highgui.cvShowImage ('LkDemo', image)

        # handle events
        c = highgui.cvWaitKey (10)

        if c == '\x1b':
            # user has press the ESC key, so exit
	    # stop()
            exit()
            break

        # processing depending on the character
        if c in ['r', 'R']:
            need_to_init = True
        elif c in ['c', 'C']:
            points = [[], []]
        elif c in ['n', 'N']:
            night_mode = not night_mode
