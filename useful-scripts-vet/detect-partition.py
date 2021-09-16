import math
import os
import pickle
import sys
import json

ep = 10 * 60 * 1000
INPUT_DIR_NAME = 'processed_traces'
OUTPUT_DIR_NAME = 'detect_partition'


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


if len(sys.argv) < 2:
    print("Trace ID?")
    sys.exit(1)

RET_FOLDER = sys.argv[1]
REPORT_ID = os.path.basename(RET_FOLDER.rstrip('/'))
PREPROCESSED_FN = "%s/%s.pickle" % (INPUT_DIR_NAME, REPORT_ID)
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

print("Load from preprocessed trace..")
with open(PREPROCESSED_FN, "rb") as f:
    (screens, _) = pickle.load(f)

search_end = screens[-1][0] - ep
ind_search_end = None
ind_curr = 0
hash_stats = {}
hash_set_after_end = set()

for (ts, _, layout_hash) in screens:
    ind_curr += 1
    ct = hash_stats.get(layout_hash, 0)
    hash_stats[layout_hash] = ct + 1
    if ts >= search_end:
        if ind_search_end:
            ind_search_end = ind_curr
        else:
            hash_set_after_end.add(layout_hash)

screens_after = {}
screens_before = {}

ts_all_end = screens[-1][0]
ct_total_unique_hash = len(set(hash_stats))
print('ct_total_unique_hash', ct_total_unique_hash)
ct_unique_hash_at_end = len(hash_set_after_end)
print('ct_unique_hash_at_end', ct_unique_hash_at_end)
hash_stats_back = hash_stats
hash_set_fwd = set()
best_score = 100.0
best_score_components = None
worst_score = 0.0
ts_best_score = None
scores = []

for i in range(0, len(screens)):
    (ts, _, layout_hash) = screens[i]
    if ts > search_end:
        break
    hash_set_fwd.add(layout_hash)
    ct = hash_stats_back[layout_hash]
    if ct <= 1:
        del hash_stats_back[layout_hash]
    else:
        hash_stats_back[layout_hash] = ct - 1
    hash_set_back = set(hash_stats_back)
    hash_common = hash_set_back.intersection(hash_set_fwd)
    len_hash_common = float(sum([hash_stats_back[s] for s in hash_common]))
    len_hash_fwd = float(len(hash_set_fwd))
    len_hash_back = float(len(hash_set_back))
    c2 = len_hash_common / float(len(screens) - i - 1)
    c3 = len_hash_back / ct_unique_hash_at_end
    c3 = 2 * sigmoid(c3 - 1) - 1
    score = c2 + c3
    scores.append(score)
    if score > worst_score:
        worst_score = score
    if score < best_score:
        best_score = score
        ts_best_score = ts
        best_score_components = (c2, c3, len_hash_fwd, len_hash_back)
        print(ts, score, len_hash_common, len_hash_fwd, len_hash_back,
              ct_unique_hash_at_end, i + 1, len(screens) - i - 1)
        rev_ct = rev_ct_base = 0
        for s in hash_set_back:
            if s in hash_set_fwd:
                continue
            curr_scr_after = screens_after.get(s, None)
            if not curr_scr_after:
                continue
            for s2 in hash_set_fwd:
                if s2 in curr_scr_after:
                    rev_ct += 1.0 / (len(curr_scr_after) *
                                     len(screens_before[s2]))
                    rev_ct_base += 1
        if rev_ct:
            rev_ct /= rev_ct_base
            print("rev_ct = " + str(rev_ct))

print(ts_all_end - ts_best_score)
print(best_score_components)
print((best_score, ts_best_score))

regions = []

_, _, len_hash_fwd, len_hash_back = best_score_components
if len_hash_fwd > len_hash_back:
    regions.append((ts_best_score, ts_best_score, ts_all_end))

os.system('mkdir -p ' + OUTPUT_DIR_NAME)
with open(os.path.join(OUTPUT_DIR_NAME, '%s.json' % REPORT_ID), 'w') as handle:
	json.dump(regions, handle)
