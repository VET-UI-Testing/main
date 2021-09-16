import os
import pickle
import sys
import json

ct_max_top_regions = 3
INPUT_DIR_NAME_TRACES = 'processed_traces'
INPUT_DIR_NAME_PARTITION = 'detect_partition'
INPUT_DIR_NAME_TRAPPED = 'detect_trapped'
OUTPUT_DIR_NAME = 'prevent_actions'

if len(sys.argv) < 3:
    print(
        'USAGE: python3 generate-actions.py OUTPUT_ID TRACE_ID [TRACE_ID...]')
    sys.exit(1)

os.system('mkdir -p ' + OUTPUT_DIR_NAME)
OUTPUT_FN = os.path.join(OUTPUT_DIR_NAME, '%s.json' % sys.argv[1])


def read_json(fp):
    with open(fp, 'r') as h:
        return json.load(h)


def find_most_freq_screen(trace_id, begin, end):
    global INPUT_DIR_NAME_TRACES
    fp = os.path.join(INPUT_DIR_NAME_TRACES, '%s.pickle' % trace_id)
    with open(fp, 'rb') as h:
        screens, _ = pickle.load(h)

    counts = {}
    first_ts = {}
    is_last_intv = True
    interp_layout = None
    for ts, is_interp, layout_hash in screens:
        # print(ts)
        if ts > end:
            is_last_intv = False
            break
        if is_interp:
            interp_layout = layout_hash
        if ts < begin:
            continue
        if layout_hash not in first_ts:
            first_ts[layout_hash] = ts
        ct = counts.get(layout_hash, 0)
        counts[layout_hash] = ct + 1

    if counts:
        most_freq_layout = max(counts, key=lambda key: counts[key])
        # print(counts[most_freq_layout])
        # Edge case: having only one screen by the end suggests that the app or tool is dead,
        # instead of having ineffective exploration behavior.
        if most_freq_layout == interp_layout and is_last_intv:
            return -100
        else:
            return first_ts[most_freq_layout]
    else:
        print('Trace %s seems to be empty' % trace_id)
        sys.exit(2)


action_jsons = []
total_region_ct = total_region_length = 0
for trace_id in sys.argv[2:]:
    regions_part = read_json(os.path.join(
        INPUT_DIR_NAME_PARTITION, '%s.json' % trace_id))
    action_ts = [(ts_begin - ts_end, ts_begin, ts_end, ts_action, False)
                 for ts_action, ts_begin, ts_end in regions_part]
    regions_trap = read_json(os.path.join(
        INPUT_DIR_NAME_TRAPPED, '%s.json' % trace_id))
    action_ts += [(ts_begin - ts_end, ts_begin, ts_end, ts_action, True)
                  for ts_action, ts_begin, ts_end in regions_trap]

    action_ts.sort()
    for _, ts_begin, ts_end, ts_action, do_remedy in action_ts[:ct_max_top_regions]:
        curr_actions = [os.path.join(trace_id, '%d.json' % ts_action)]
        if do_remedy:
            screen_kill = find_most_freq_screen(trace_id, ts_begin, ts_end)
            if screen_kill > 0:
                curr_actions.append(
                    '!' + os.path.join(trace_id, '%d.json' % screen_kill))
        action_jsons.append(curr_actions)

    regions_all = [(ts_begin, ts_end)
                   for _, ts_begin, ts_end in regions_part + regions_trap]
    regions_merged = []
    last_begin, last_end = -1, -1
    for curr_begin, curr_end in sorted(regions_all):
        if curr_begin > last_end:
            regions_merged.append((curr_begin, curr_end))
            last_begin, last_end = curr_begin, curr_end
        else:
            last_end = max(last_end, curr_end)
            regions_merged[-1] = (last_begin, last_end)
    total_region_ct += len(regions_merged)
    total_region_length += sum([e-b for b, e in regions_merged])

with open(OUTPUT_FN, 'w') as h:
    json.dump(action_jsons, h)

print('%d region(s) in total, avg length = %.2f min(s)' %
      (total_region_ct, total_region_length / total_region_ct / 1000 / 60))
