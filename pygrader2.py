import argparse
import os, sys, subprocess, shutil, time


parser = argparse.ArgumentParser()
parser.add_argument('executable')
parser.add_argument('--tests_dir', default='tests/')
parser.add_argument('--basename')
parser.add_argument('--checker')
parser.add_argument('--stdio', action='store_true')
args = parser.parse_args()

executable = args.executable

if not os.path.isfile(executable):
	print "Executable does not exist"
	raise SystemExit

testsdir = os.path.join(os.path.dirname(os.path.abspath(executable)), args.tests_dir)
if not os.path.isdir(testsdir):
	print "Tests dir does not exist"
	raise SystemExit

print 'Tests dir =', testsdir

progname = args.basename or os.path.splitext(os.path.basename(executable))[0]

test_file_in = progname + '.in'
test_file_out = progname + '.out'

print 'In/out files =', test_file_in, '/', test_file_out

# Enumerate tests

tests = []

for fn in os.listdir(testsdir):
	if os.path.isfile(os.path.join(testsdir, fn)):
		filename, ext = os.path.splitext(os.path.basename(fn))
		if ext == '.in':
			solfile = os.path.join(testsdir, filename + '.sol')
			if os.path.isfile(solfile):
				tests.append(filename)

print "Found", len(tests), "test cases"

exec_path = os.path.dirname(os.path.abspath(executable))

def check_output(input_fn, output_fn, solution_fn):
	if args.checker:
		checker_output = subprocess.check_output([
				args.checker,
				'10',  # points
				input_fn,
				output_fn,
				solution_fn]).decode('utf-8').splitlines()
		return (checker_output[0] == '10', checker_output[1])
	else:
		output_contents = open(output_fn, "r").read()
		solution_contents = open(solution_fn, "r").read()
		if output_contents.strip() == solution_contents.strip():
			return (True, 'OK')
		else:
			return (False, 'Wrong Answer')

for test_name in tests:
	input_fn = os.path.join(testsdir, test_name + '.in')
	input_copy_fn = os.path.join(exec_path, test_file_in)
	output_fn = os.path.join(exec_path, test_file_out)
	solution_fn = os.path.join(testsdir, test_name + '.sol')
	
	print test_name,
	# Copy input file
	shutil.copy(input_fn, input_copy_fn)
	exec_args = {}
	
	if args.stdio:
		exec_args['stdin'] = open(input_copy_fn, 'r')
		exec_args['stdout'] = open(output_fn, 'w')
	
	# Execute program
	p = subprocess.Popen(executable, **exec_args)
	t1 = time.time()
	p.wait()
	t2 = time.time()
	print "%.3f secs" % (t2 - t1),
	if (t2-t1) > 2.0:
		print "(timeout)",
	
	if args.stdio:
		exec_args['stdin'].close()
		exec_args['stdout'].close()
	
	success, message = check_output(input_fn, output_fn, solution_fn)
	print message
	if success:
		os.remove(output_fn)
	else:
		new_name = os.path.join(exec_path, test_name + '.wrong.out')
		try: os.unlink(new_name)
		except: pass
		os.rename(output_fn, new_name)
	os.remove(input_copy_fn)

