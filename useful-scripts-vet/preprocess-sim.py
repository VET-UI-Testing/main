import os
import pickle
import sys
from zss import Node

tree_dist_thres = 10
INPUT_DIR_NAME = 'processed_traces'
OUTPUT_DIR_NAME = 'processed_sims'

if len(sys.argv) < 2:
    print("Trace ID?")
    sys.exit(1)

RET_FOLDER = sys.argv[1]
REPORT_ID = os.path.basename(RET_FOLDER.rstrip('/'))
PREPROCESSED_FN = "%s/%s.pickle" % (INPUT_DIR_NAME, REPORT_ID)

# print("Load from preprocessed trace..")
with open(PREPROCESSED_FN, "rb") as f:
    (screens, trees) = pickle.load(f)

# Only outputing when `a` is a subseq of `b`
# Derived from: https://rosettacode.org/wiki/Longest_common_subsequence#Python
def get_subseq_mapping(a, b):
    lenA, lenB = len(a), len(b)
    lengths = [[0] * (lenB+1) for _ in range(lenA+1)]
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            if x == y:
                lengths[i+1][j+1] = lengths[i][j] + 1
            else:
                lengths[i+1][j+1] = max(lengths[i+1][j], lengths[i][j+1])
        if lengths[i+1][lenB] < i+1:
            return None
    ret = []
    for j in range(0, lenB):
        if lengths[lenA][j+1] != lengths[lenA][j]:
            ret.append(j)
    return ret


def traverse_for_depth(root):
    ret = []
    def trav(n, d):
        ret.append((Node.get_label(n), d))
        for c in Node.get_children(n):
            trav(c, d+1)
    trav(root, 0)
    return ret

# O(M*N)
def fast_insertion_distance(hash1, hash2):
    tree1, *_ = trees[hash1]
    tree2, *_ = trees[hash2]
    nodes1, nodes2 = traverse_for_depth(tree1), traverse_for_depth(tree2)
    mapping = get_subseq_mapping(nodes1, nodes2)
    if mapping:
        return len(nodes2) - len(nodes1)
    return len(nodes1) + len(nodes2)


def count_nodes(tree):
    return sum(1 for x in tree.iter())


os.system('mkdir -p ' + OUTPUT_DIR_NAME)
handle = open('./%s/%s.pickle' % (OUTPUT_DIR_NAME, REPORT_ID), 'wb')

total_ct = 0
lst_scr_set = []
for h in trees:
    t, *act = trees[h]
    if act:
        act = act[0]
    if not t:
        print(h)
        for (ts, _, hh) in screens:
            if h == hh:
                print(ts)
                break
        continue
    lst_scr_set.append((count_nodes(t), act, h))
lst_scr_set.sort()

len_lst_scr_set = len(lst_scr_set)
scr_sim_mat = [-1] * (len_lst_scr_set * len_lst_scr_set)
print('|{screens}| = %d' % len_lst_scr_set)

last_progress_pct = -1
for i in range(0, len_lst_scr_set):
    n1, act1, hash1 = lst_scr_set[i]
    for j in range(i + 1, len_lst_scr_set):
        n2, act2, hash2 = lst_scr_set[j]
        if act1 != act2 or n2 <= n1 or n2 - n1 > tree_dist_thres:
            continue
        scr_sim_mat[i * len_lst_scr_set + j] = fast_insertion_distance(hash1, hash2)
        total_ct += 1
    curr_progress_pct = 100 * i // len_lst_scr_set // 5 * 5
    if curr_progress_pct > last_progress_pct:
        last_progress_pct = curr_progress_pct
        print('%d%%' % curr_progress_pct, end=' ', flush=True)
print('\n|comp| = %d' % total_ct)

pickle.dump(([h for (_, _, h) in lst_scr_set], scr_sim_mat), handle)
