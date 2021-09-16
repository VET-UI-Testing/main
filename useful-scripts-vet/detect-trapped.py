import math
import os
import pickle
import sys
import json
from zss import Node

tree_dist_thres = 3
ep = 10 * 60 * 1000
INPUT_DIR_NAME_TRACE = 'processed_traces'
INPUT_DIR_NAME_SIM = 'processed_sims'
OUTPUT_DIR_NAME = 'detect_trapped'


if len(sys.argv) < 2:
    print("Trace ID?")
    sys.exit(1)

RET_FOLDER = sys.argv[1]
REPORT_ID = os.path.basename(RET_FOLDER.rstrip('/'))
PREPROCESSED_TRACE_FN = "%s/%s.pickle" % (INPUT_DIR_NAME_TRACE, REPORT_ID)
PREPROCESSED_SIM_FN = "%s/%s.pickle" % (INPUT_DIR_NAME_SIM, REPORT_ID)
SCR_PREF = None
SCR_START = None
SCR_END = None

if len(sys.argv) > 2:
    SCR_START = int(sys.argv[2])

if len(sys.argv) > 3:
    opt_end = sys.argv[3]
    if opt_end[0] == '+':
        SCR_END = int(opt_end[1:]) * 1000 + SCR_START
    else:
        SCR_END = int(opt_end)
    if SCR_END < SCR_START:
        print("SCR_END < SCR_START")
        sys.exit(1)

with open(PREPROCESSED_SIM_FN, 'rb') as f:
    (uniq_screens, uniq_screen_dists) = pickle.load(f)
    # `uniq_screens` is already sorted by counts of nodes
    uniq_screen_idx = dict(zip(uniq_screens, range(len(uniq_screens))))

print("Load from preprocessed trace..")
with open(PREPROCESSED_TRACE_FN, "rb") as f:
    (screens, trees) = pickle.load(f)


def get_screen_dist(pos1, pos2):
    return uniq_screen_dists[pos1 * len(uniq_screens) + pos2]


def traverse_and_print(root):
    def trav(n, d):
        print(' ' * d + Node.get_label(n))
        for c in Node.get_children(n):
            trav(c, d+1)
    trav(root, 0)


ct_uniq_root = 0
idx_parent = [None] * len(uniq_screens)
for i in range(len(uniq_screens)):
    if idx_parent[i] is not None:
        continue
    idx_parent[i] = i
    ct_uniq_root += 1
    for j in range(i + 1, len(uniq_screens)):
        if idx_parent[j] is not None:
            continue
        tree_dist = get_screen_dist(i, j)
        if tree_dist <= tree_dist_thres and tree_dist >= 0:
            idx_parent[j] = i

print('> |{uniq_scr}| = %d, |{uniq_root}| = %d' %
      (len(uniq_screens), ct_uniq_root))

regions = []

queue = [screens]
while queue:
    curr_screens = queue[0]
    queue = queue[1:]
    ct_curr_screens = len(curr_screens)
    print("|curr_screens| = %d" % ct_curr_screens)

    min_score = 10
    siL = siR = None
    last_uniq_par_ct = 0

    for left in range(0, ct_curr_screens):
        curr_uniq_parents = {}
        for right in range(left, ct_curr_screens):
            (_, _, curr_layout_hash) = curr_screens[right]
            curr_idx_parent = idx_parent[uniq_screen_idx[curr_layout_hash]]
            curr_uniq_parents[curr_idx_parent] = curr_uniq_parents.get(
                curr_idx_parent, 0) + 1
            uniq_par_ct = len(curr_uniq_parents)
            curr_score = uniq_par_ct / (right - left + 1)
            if curr_score < min_score:
                min_score = curr_score
                siL, siR = left, right
                if last_uniq_par_ct != uniq_par_ct:
                    last_uniq_par_ct = uniq_par_ct
                    print('> %.5f <- %d / %d, %d - %d' % (curr_score, uniq_par_ct,
                                                          (right - left + 1), curr_screens[siL][0], curr_screens[siR][0]))

    tsL = curr_screens[siL][0]
    tsR = curr_screens[siR][0]

    if tsR - tsL >= ep:
        print(min_score, siL, siR)
        print("%d -> %d  delta = %.2f mins" %
              (tsL, tsR, (tsR - tsL) / 1000.0 / 60))

        if siL > 0:
            queue.append(curr_screens[:siL])
            regions.append((curr_screens[siL-1][0], tsL, tsR))
        else:
            regions.append((curr_screens[siL][0], tsL, tsR))
        if ct_curr_screens > siR + 1 + 0:
            queue.append(curr_screens[siR+1:])

os.system('mkdir -p ' + OUTPUT_DIR_NAME)
with open(os.path.join(OUTPUT_DIR_NAME, '%s.json' % REPORT_ID), 'w') as handle:
	json.dump(regions, handle)
