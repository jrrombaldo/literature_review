#!./venv/bin/python

import argparse
from pathlib import Path
import json
import rispy
import re


def write_file (content, file_name):
    with open(file_name, 'w') as out:
        out.write(content)

def write_json(content, file_name):
    write_file(json.dumps(content, indent=4, sort_keys=True), file_name)

def write_ris(content, file_name):
    write_file(rispy.dumps(content), file_name)

def adjust_rayyan_tags(notes):
    notes_new =[]
    for note in notes:
        if "RAYYAN-" in note:
            for part in note.split("RAYYAN-"): 
                if len(part.lstrip())>0:
                    notes_new.append(part.lstrip())
        else:
            notes_new.append(note)
        
    return notes_new


parser = argparse.ArgumentParser(description='various scripts supporting systematic literature review')
parser.add_argument('ris_file', metavar='RIS_file', type=str,
                    help='take an RIS file, split comments  RAYYAN-INCLUSION, \
                    RAYYAN-EXCLUSION-REASONS and RAYYAN-LABELS into dedicated entries. \
                    Results are saved into a file named "parsed"')
parser.add_argument('--json', action='store_true', help='Save JSON format instead of RIS')

args = parser.parse_args()


print (f'parsing {args.ris_file} ...')
ris_file_path = Path(args.ris_file).absolute()


# counters
inc_ct = exc_ct = lbl_ct = 0

with open(ris_file_path, 'r', ) as bibliography_file:
    ris_entries = rispy.load(bibliography_file, skip_unknown_tags=False)
    print (f'found {len(ris_entries)} bibliographies at {ris_file_path}')

    for ris_entry in ris_entries:
        print(f'processing title "{ris_entry["title"]}"')
        ris_entry['notes'] = adjust_rayyan_tags(ris_entry['notes'])

        # counting tags
        for note in ris_entry['notes']:
                    if note.startswith('INCLUSION:'):             inc_ct +=1
                    if note.startswith('EXCLUSION-REASONS:'):     exc_ct +=1
                    if note.startswith('LABELS:'):                lbl_ct +=1

    print (f'found \n\tINCLUSIONS={inc_ct}\n\tEXCLUSIONS={exc_ct}\n\tLABELS={lbl_ct}')



# adjusting inputed file name extension
result_file = f'{re.sub("[^.]+$","", args.ris_file)}parsed.{"json" if args.json else "ris"}'

result_path = Path(result_file).absolute()
print (f'saving {len(ris_entries)} entries at {result_file} ')
if args.json:
    write_json(ris_entries, result_path)
else:
    write_ris(ris_entries, result_path)







