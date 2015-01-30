import argparse
import os, sys, subprocess, shutil, time, glob, tempfile

if sys.version_info[:3] < (3, 4, 0):
	print('Requires Python >= 3.4.0')
	sys.exit(1)

parser = argparse.ArgumentParser()
parser.add_argument('executable')
parser.add_argument('--tests', default='tests')
parser.add_argument('--basename')
parser.add_argument('--checker')
parser.add_argument('--gen-solutions', action='store_true')
parser.add_argument('--stdio', action='store_true')
args = parser.parse_args()

executable = args.executable
if not os.path.isfile(executable):
	print("Executable '%s' does not exist" % os.path.abspath(executable))
	raise SystemExit

testsdir = os.path.abspath(args.tests)
if not os.path.isdir(testsdir):
	print("Tests directory '%s' does not exist" % testsdir)
	raise SystemExit

progname = args.basename or os.path.splitext(os.path.basename(executable))[0]

test_file_in = progname + '.in'
test_file_out = progname + '.out'

print('In/out files =', test_file_in, '/', test_file_out)


def check_output(input_fn, output_fn, solution_fn):
	if args.checker:
		with tempfile.TemporaryFile() as f_err:
			checker_output = subprocess.check_output([
				args.checker,
				input_fn,
				solution_fn,
				output_fn],
				stderr=f_err).decode('utf-8').splitlines()
			f_err.seek(0)
			err_msg = f_err.read().decode('utf-8').strip()
			return (checker_output[0] == '1', err_msg)
	else:
		output_contents = open(output_fn, "r").read()
		solution_contents = open(solution_fn, "r").read()
		if output_contents.strip() == solution_contents.strip():
			return (True, 'OK')
		else:
			return (False, 'Wrong Answer')


# Enumerate tests

tests = []
for fn in glob.glob(glob.escape(testsdir) + '/*.in'):
	if os.path.isfile(fn):
		filename, ext = os.path.splitext(os.path.basename(fn))
		if (not args.gen_solutions and
			not os.path.isfile(os.path.join(testsdir, filename + '.sol'))):
			continue
		tests.append(filename)

print("Found", len(tests), "test cases")

exec_path = os.path.dirname(os.path.abspath(executable))

for test_name in tests:
	input_fn = os.path.join(testsdir, test_name + '.in')
	input_copy_fn = os.path.join(exec_path, test_file_in)
	output_fn = os.path.join(exec_path, test_file_out)
	solution_fn = os.path.join(testsdir, test_name + '.sol')
	
	print(test_name, end=' ')
	# Copy input file
	shutil.copy(input_fn, input_copy_fn)
	exec_args = {}
	
	if args.stdio:
		exec_args['stdin'] = open(input_copy_fn, 'r')
		exec_args['stdout'] = open(output_fn, 'w')
	
	# Execute program
	p = subprocess.Popen(executable, **exec_args)
	t1 = time.time()
	killed = False
	try:
		p.wait(2)
	except subprocess.TimeoutExpired:
		p.kill()
		p.wait()
		killed = True
	t2 = time.time()
	print("%.3f secs" % (t2 - t1), end=' ')
	if killed:
		print("(killed)", end=' ')
	
	if args.stdio:
		exec_args['stdin'].close()
		exec_args['stdout'].close()
	
	os.remove(input_copy_fn)
	if not os.path.isfile(output_fn):
		print('Output file not found')
	else:
		success, message = check_output(input_fn, output_fn, solution_fn)
		print(message)
		if success:
			os.remove(output_fn)
		else:
			new_name = os.path.join(exec_path, test_name + '.wrong.out')
			try: os.unlink(new_name)
			except: pass
			os.rename(output_fn, new_name)

