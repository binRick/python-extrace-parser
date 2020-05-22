#!/usr/bin/env python3
import os, sys, json, pprint, blessings, traceback, humanize, datetime, time, psutil
from ascii_art import Bar
from operator import attrgetter
from blessings import Terminal

BAR_CHAR_FORK_FREQUENCY_ROWS = 12
BAR_CHAR_EXECS_TIME_ROWS = 12
#print(humanize.naturaldelta(datetime.timedelta(seconds=1001)))
#sys.exit()

t = Terminal()
pp = pprint.PrettyPrinter(indent=4).pprint

if len(sys.argv) < 2:
	print(t.bold_red_on_black('\n\n       First Argument must be extrace output file     \n'))
	sys.exit(1)

FILE = sys.argv[1]
try:
    EXTRACE_PID = int(sys.argv[2])
except:
    EXTRACE_PID = None

FORKS = []
END_FORKS = {}
REPORTS = {}

CUR_PROCS_LIST = []
def check_pids():
    if EXTRACE_PID == None:
        return False
    try:
        p = psutil.Process(EXTRACE_PID)
    except:
        traceback.print_exc()
        return False
    children = []
    for c in p.children(recursive=True):
        try:
            for cc in c.children(recursive=True):
                if not cc.pid in children:
                    children.append(cc.pid)
            children.append(c.pid)
        except:
            pass
    m = f'extrace pid {EXTRACE_PID} has {len(children)} children\n'
    sys.stderr.write(m)
    return children


if EXTRACE_PID:
    check_pids()

def truncate_string(S, LENGTH=20):
	if len(S) > LENGTH:
		S = os.path.basename(S)

	return S[:LENGTH] + (S[LENGTH:] and '..')

def bar_chart(TITLE, DAT, KEY, VAL, LIMIT=100):
	PB = {}
	for i in DAT[:LIMIT]:
		PB[truncate_string(i[KEY])] = i[VAL]
	b = Bar(PB)
	print(TITLE)
	print(b.render())

def unique(list1):
	list_set = set(list1)
	return (list(list_set))

def getExtraceLines(FILE):
	if not FILE or not os.path.exists(FILE):
		print(t.bold_red_on_bright_black('First Argument must be extrace output file'))
		sys.exit(1)
	try:
		with open(FILE,'r') as f:
			DAT = f.read()
		return DAT.strip().split('\n')
	except Exception as e:
		print('Failed to open extrace output file')
		traceback.print_exc()


LINES = getExtraceLines(FILE)

for l in LINES:
	items = l.split(' ')
	if items[0].endswith('+'):
		NEW_FORK = {
			"pid": int(items[0].replace('+','')),
			"user": items[1].split('<')[1].split('>')[0],
			"cwd": items[2],
			"exec": items[4],
			"args": ' '.join(items[5:]).strip(),
		}
#		print(items)
		FORKS.append(NEW_FORK)
	elif items[0].endswith('-') and 'time=' in items[4]:

		END_FORK = {
			"pid": int(items[0].replace('-','')),
			"result": items[2],
			"code": items[3].split('=')[1],
			"time": items[4].split('=')[1],
		}
		if not END_FORK['time'].endswith('s'):
			raise Exception('Unable to handle time {} in fork {}'.format(END_FORK['time'], END_FORK))
		else:
			END_FORK['time'] = float(END_FORK['time'].replace('s',''))
			END_FORK['time_ms'] = int(END_FORK['time'] * 1000)

		MATCHED = False
		for F in FORKS:
			if F['pid'] == END_FORK['pid']:
				MATCHED = True
				for k in END_FORK.keys():
					F[k] = END_FORK[k]
				break

#		print(items, END_FORK, MATCHED)

		if not MATCHED:
			raise Exception('Unable to find ending fork', items, END_FORK)
		else:
			END_FORKS[END_FORK['pid']] = END_FORK
			pass
	else:
		print('[unhandled line] {}'.format(items))
		sys.exit(1)

INTERESTING_CMDS = ['ssh','ssh-add','ssh-agent','ansible','ansible-playbook','python','python3','pip','pip3','python3.6','sftp','scp','rsync','borg']
FOUND_INTERESTING_CMDS = {}
REQUIRED_KEYS = ['time_ms','code','result','exec','pid','cwd']
INVALID_FORKS = []
VALID_FORKS = []
REPORTS['EXEC_DURATIONS'] = {}
for F in FORKS:
	VALID = True
	for k in REQUIRED_KEYS:
		if not k in F:
			VALID = False
	if not VALID:
		INVALID_FORKS.append(F)
		FORKS.remove(F)
	else:
		VALID_FORKS.append(F)

for vf in VALID_FORKS:
    bn = os.path.basename(vf['exec'])
    if bn in INTERESTING_CMDS:
        r = {'name': bn, 'exec': vf['exec'],'time': vf['time'], 'result': vf['result'], 'code': vf['code'], 'pid':vf['pid'],'args':vf['args'], }
        if not bn in FOUND_INTERESTING_CMDS.keys():
            FOUND_INTERESTING_CMDS[bn] = []
        FOUND_INTERESTING_CMDS[bn].append(r)

print("\n")
pids = check_pids()
if pids:
    for _p in pids:
        try:
            p = psutil.Process(int(_p))
        except:
            continue
        D = p.as_dict()
        if D['name'] in FOUND_INTERESTING_CMDS.keys():
            T = int(p.as_dict()['create_time'])
            AGE = int(int(time.time()) - T)
            msg = f'{D["name"]} :: {AGE} secs old'
            print(msg)

print("\n")
for k in FOUND_INTERESTING_CMDS.keys():
    pids = [c['pid'] for c in FOUND_INTERESTING_CMDS[k]]
    qty = len([c for c in FOUND_INTERESTING_CMDS[k]])
    pids_failed = [c['pid'] for c in FOUND_INTERESTING_CMDS[k] if not c['pid'] in END_FORKS or int(END_FORKS[c['pid']]['code']) != 0]
    pids_ok = [c['pid'] for c in FOUND_INTERESTING_CMDS[k] if not c['pid'] in END_FORKS or int(END_FORKS[c['pid']]['code']) == 0]
    m = f'[{k}] {len(pids)} pids, {len(pids_failed)} failed, {len(pids_ok)} ok,'
    print(m)
    """
    if 'python' in k:
        print(FOUND_INTERESTING_CMDS[k])
        print("\n")
    if k == 'ssh':
        print(type(FOUND_INTERESTING_CMDS[k]))
        print("\n")
    """

print("\n")
#print(VALID_FORKS[0])
#print(END_FORKS)
#sys.exit()

USERS = []
USER_FREQS = {'total': {}, }
for f in FORKS:
    if 'user' in f.keys() and not f['user'] in USERS:
        USERS.append(f['user'])
    if not f['user'] in USER_FREQS['total'].keys():
        USER_FREQS['total'][f['user']] = 0
    else:
        USER_FREQS['total'][f['user']] += 1

print(USERS)
print(USER_FREQS)
#sys.exit()

VALID_FORKS_TXT = t.bold_black_on_bright_white('Valid Forks')

print('\n{} {} from {} extrace lines'.format(len(FORKS), VALID_FORKS_TXT, len(LINES)))
print('{} Invalid Forks'.format(len(INVALID_FORKS)))

REPORTS['UNIQUE_EXECS'] = unique([o['exec'].split(' ')[0] for o in VALID_FORKS])


try:
	REPORTS['TOP_FORK_DURATIONS'] = sorted(VALID_FORKS, key=lambda F: F['time_ms'], reverse=True)
except Exception as e:
	print('Unable to sort top fork durations')
	print(VALID_FORKS)
	traceback.print_exc()
	

for E in REPORTS['UNIQUE_EXECS']:
	if not E in REPORTS['EXEC_DURATIONS'].keys():
		REPORTS['EXEC_DURATIONS'][E] = {"time_ms": 0,"execs_qty": 0,"exec": E}

	for f in VALID_FORKS:
		if f['exec'].startswith(E) and 'time_ms' in f.keys():
			REPORTS['EXEC_DURATIONS'][E]['time_ms'] += f['time_ms']
			REPORTS['EXEC_DURATIONS'][E]['execs_qty'] +=1



REPORTS['TOP_EXECS'] = sorted(REPORTS['EXEC_DURATIONS'].keys(), key=lambda F: REPORTS['EXEC_DURATIONS'][F]['time_ms'], reverse=True)
REPORTS['TOP_EXECS_FREQUENCY'] = sorted(REPORTS['EXEC_DURATIONS'].keys(), key=lambda F: REPORTS['EXEC_DURATIONS'][F]['execs_qty'], reverse=True)
REPORTS['TOP_EXECS_TIME'] = sorted(REPORTS['EXEC_DURATIONS'].keys(), key=lambda F: REPORTS['EXEC_DURATIONS'][F]['time_ms'], reverse=True)

REPORTS['_TOP_EXECS_TIME'] = {}
REPORTS['__TOP_EXECS_TIME'] = []
REPORTS['_TOP_EXECS_FREQUENCY'] = {}
REPORTS['__TOP_EXECS_FREQUENCY'] = []

for E in REPORTS['TOP_EXECS_FREQUENCY']:
	if not E in REPORTS['_TOP_EXECS_FREQUENCY'].keys():
		REPORTS['_TOP_EXECS_FREQUENCY'][E] = {"time_ms": 0,"execs_qty": 0,"exec": E}
	for f in VALID_FORKS:
		if f['exec'].startswith(E) and 'time_ms' in f.keys():
			REPORTS['_TOP_EXECS_FREQUENCY'][E]['time_ms'] += f['time_ms']
			REPORTS['_TOP_EXECS_FREQUENCY'][E]['execs_qty'] +=1

for E in REPORTS['TOP_EXECS_FREQUENCY']:
	REPORTS['__TOP_EXECS_FREQUENCY'].append(REPORTS['_TOP_EXECS_FREQUENCY'][E])

for E in REPORTS['TOP_EXECS_TIME']:
	if not E in REPORTS['_TOP_EXECS_TIME'].keys():
		REPORTS['_TOP_EXECS_TIME'][E] = {"time_ms": 0,"execs_qty": 0,"exec": E}
	for f in VALID_FORKS:
		if f['exec'].startswith(E) and 'time_ms' in f.keys():
			REPORTS['_TOP_EXECS_TIME'][E]['time_ms'] += f['time_ms']
			REPORTS['_TOP_EXECS_TIME'][E]['execs_qty'] +=1

for E in REPORTS['TOP_EXECS_TIME']:
	REPORTS['__TOP_EXECS_TIME'].append(REPORTS['_TOP_EXECS_TIME'][E])

PB = {}
for i in REPORTS['__TOP_EXECS_FREQUENCY'][:5]:
	PB[i['exec']] = i['execs_qty']

print("\n\n")
bar_chart('Fork Frequency', REPORTS['__TOP_EXECS_FREQUENCY'], 'exec', 'execs_qty', BAR_CHAR_FORK_FREQUENCY_ROWS)
bar_chart('Fork Duration (ms)', REPORTS['__TOP_EXECS_TIME'], 'exec', 'time_ms', BAR_CHAR_EXECS_TIME_ROWS)

