import time, subprocess, sys
beg = time.time()
try: subprocess.Popen(sys.argv[1:], shell=True).wait()
except: pass
dur = time.time() - beg
print >>sys.stderr, "Time: {0:.2f} sec".format(dur)
