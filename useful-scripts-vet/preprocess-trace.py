import hashlib
import os
import pickle
import sys
import json
from zss import Node

EXPECTED_TRACE_LENGTH = 1 * 3600 * 1000 - 60 * 1000
ALLOWED_BOUNDARY_OUTAGE = 10 * 1000
OUTPUT_DIR_NAME = 'processed_traces'

def listfiles(d):
    return [f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))]

def parse_pos(pos):
	pos_c1 = pos.find(",")
	left = int(pos[1 : pos_c1])
	pos_b1 = pos.find("]")
	top = int(pos[pos_c1+1 : pos_b1])
	pos_c2 = pos.find(",", pos_b1)
	right = int(pos[pos_b1+2 : pos_c2])
	bottom = int(pos[pos_c2+1 : -1])
	return (top, left, bottom - top, right - left)

def get_source_pos(layout):
	def find_source_pos(layout):
		if "is_source" in layout:
			return layout["bound"]
		if "ch" in layout:
			for ch in layout["ch"]:
				ret = find_source_pos(ch)
				if ret:
					return ret
		return None
	ret = find_source_pos(layout)
	if ret:
		return parse_pos(ret)
	else:
		return (0, 0, 0, 0)

def hash_layout(layout):
	sanity_check_ok = True
	for field in ["bound", "act_id"]:
		if field not in layout:
			sanity_check_ok = False
			break
	if layout["act_id"] == "unknown" and not layout.get("focus", False):
		sanity_check_ok = False
	if not sanity_check_ok:
		print(layout)
		return None
	(s_t, s_l, s_h, s_w) = parse_pos(layout["bound"])
	check_elem_pos = s_h > 0 and s_w > 0
	if "vis" in layout:
		del layout["vis"]
	def traverse(layout, pool):
		if not layout:
			return None
		if "vis" in layout and layout["vis"] != 0:
			return None
		if "bound" not in layout:
			return None
		if check_elem_pos:
			(t, l, h, w) = parse_pos(layout["bound"])
			if t >= s_t + s_h or l >= s_l + s_w or s_t >= t + h or s_l >= l + w:
				return None
		pool.append("[")
		pool.append(str(layout.get("id", "-1")))
		pool.append(str(layout["class"]))
		if "ch" in layout:
			for ch in layout["ch"]:
				traverse(ch, pool)
		pool.append("]")
	ret = [layout.get("act_id", '?')]
	traverse(layout, ret)
	return hashlib.md5("".join(ret).encode()).hexdigest()

def convert_to_tree(layout):
	if "bound" not in layout:
		return None
	(s_t, s_l, s_h, s_w) = parse_pos(layout["bound"])
	# Top element sizes may be zero due to asynchronous capturing.
	# While this rarely happens, if it does we simply disable pos checks.
	check_elem_pos = s_h > 0 and s_w > 0
	# Drop visibility prop for root element.
	if "vis" in layout:
		del layout["vis"]
	def traverse(layout):
		if not layout:
			return None
		if "vis" in layout and layout["vis"] != 0:
			return None
		if "bound" not in layout:
			return None
		if check_elem_pos:
			(t, l, h, w) = parse_pos(layout["bound"])
			if t >= s_t + s_h or l >= s_l + s_w or s_t >= t + h or s_l >= l + w:
				return None
		nd = Node(str(layout.get("id", "-1")) + "/" + str(layout["class"]))
		if "ch" in layout:
			for ch in layout["ch"]:
				kd = traverse(ch)
				if kd: nd.addkid(kd)
		return nd
	return traverse(layout)

if len(sys.argv) < 2:
	print("folder?")
	sys.exit(1)

RET_FOLDER = sys.argv[1]
TEST_ID = os.path.basename(RET_FOLDER.rstrip('/'))

FILES = listfiles(RET_FOLDER)
FILES = [f for f in FILES if f[-4:] == ".jpg" or f[-5:] == ".json"]
FILES.sort()
# print(FILES)

prev_ts = None
ts_list = []
for f in FILES:
	ts = int(f[:f.index(".")])
	# print(ts)
	if ts != prev_ts:
		ts_list.append(ts)
	prev_ts = ts
ts_list.sort()
# print(ts_list)

if not ts_list:
	print("empty trace")
	sys.exit(2)

init_ts = ts_list[0]
ts_list = [t for t in ts_list if t - init_ts <= EXPECTED_TRACE_LENGTH + ALLOWED_BOUNDARY_OUTAGE]

print("|ts_list| = %d" % len(ts_list))
if len(ts_list) < 2:
	print("|ts_list| too small")
	sys.exit(3)

screens = []
trees = {}
for ts in ts_list:
	with open("%s/%d.json" % (RET_FOLDER, ts)) as f:
		layout = json.load(f)
		layout_hash = hash_layout(layout)
		if not layout_hash:
			continue
		if layout_hash not in trees:
			t = convert_to_tree(layout)
			if not t:
				print('tree == None for %d' % ts)
				sys.exit(-1)
			trees[layout_hash] = (t, layout['act_id'])
	screens.append((ts, None, layout_hash))

# Interpolate if trace length < EXPECTED_TRACE_LENGTH
last_ts = ts_list[-1]
expected_last_ts = init_ts + EXPECTED_TRACE_LENGTH
if last_ts < expected_last_ts:
	print("> off by %.2f sec(s)" % ((expected_last_ts - last_ts) / 1000.0))
	_, _, last_layout_hash = screens[-1]
	avg_action_latency = round((last_ts - init_ts) / float(len(ts_list) - 1))
	for ts in range(last_ts + avg_action_latency, expected_last_ts + ALLOWED_BOUNDARY_OUTAGE, avg_action_latency):
		screens.append((ts, True, last_layout_hash))

print("|ts_list_interp| = %d" % len(screens))

os.system('mkdir -p ' + OUTPUT_DIR_NAME)
with open(os.path.join(OUTPUT_DIR_NAME, '%s.pickle' % TEST_ID), 'wb') as handle:
	pickle.dump((screens, trees), handle)
