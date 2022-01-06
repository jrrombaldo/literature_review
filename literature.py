#!./venv/bin/python

import argparse
from pathlib import Path
import json
from dotenv import main
import rispy
import re
import timeit
import webbrowser
from scholarly import scholarly
from scholarly import ProxyGenerator
import logging 
from multiprocessing import Pool
import threading

logging.basicConfig(format='%(asctime)s  %(levelname)s  %(threadName)-40s   - %(message)s')
logging.getLogger().setLevel(logging.WARN) # disable imported module logs
log = logging.getLogger('literature_review')
log.setLevel(logging.DEBUG)


def write_file (content, file_name):
    with open(file_name, 'w') as out:
        out.write(content)

def write_json(content, file_name):
    write_file(json.dumps(content, indent=4, sort_keys=True), file_name)

def write_ris(content, file_name):
    write_file(rispy.dumps(content), file_name)

def list_titles_from_ris(ris_file):
    ris_entries = rispy.load(ris_file, skip_unknown_tags=False)
    return [ ris_entry["title"] for ris_entry in ris_entries]


def list_titles_without_pdf_from_ris(ris_file):
    ris_entries = rispy.load(ris_file, skip_unknown_tags=False)
    studies_with_pdf = []
    for ris_entry in ris_entries:
        for i in range(1,10):
            if f'file_attachments{i}' in ris_entry and 'pdf' in ris_entry[f'file_attachments{i}'].lower():
                studies_with_pdf.append(ris_entry['title'])

    studies_titles = [ ris_entry["title"] for ris_entry in ris_entries]
    return studies_titles.remove(studies_with_pdf)

def open_browser(article_url):
    chrome_path = "open -a /Applications/Chromium.app/ %s"
    webbrowser.get(chrome_path).open(article_url)



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
 

def find_study_url_on_google_scholar(study_title):
    # using proxies to avoid captchas and IP restrictions
    # paying a latency price ....
    proxy_gen = ProxyGenerator()
    proxy_gen.FreeProxies()
    scholarly.use_proxy(proxy_gen)

    search = scholarly.search_single_pub(study_title)

    if 'pub_url' in search: return search['pub_url']
    else: return None


def scholar_thread(study_title):
    threading.current_thread().name = study_title[:37]+"..."

    start = timeit.default_timer()
    log.info (f'searching url for {study_title}')
    title_url = find_study_url_on_google_scholar(study_title)

    if title_url:
        log.info(f'opening browser, found [{title_url}] for {study_title}')
        open_browser(title_url)
    else:
        log.error(f'UTL not found for study {study_title}')




def find_studies_url_and_open_browser(ris_file):
    titles = list_titles_from_ris(ris_file)

    chunk_size = 50
    for chunk_of_titles in [titles[offs:offs+chunk_size] for offs in range(0, len(titles), chunk_size)]:
        input(f"Press Enter to proccess a chunk of ({len(chunk_of_titles)}) studies")
        # log.debug(f'processing a chunk of studies, size {len(chunk_of_titles)}')

        with Pool(chunk_size) as scholar_pool:
            scholar_pool.map(scholar_thread, chunk_of_titles)


def parse_rayyan_metadata(ris_file, is_json):
    log.debug (f'parsing {ris_file.name} ...')

    # counters
    inc_ct = exc_ct = lbl_ct = 0

    ris_entries = rispy.load(ris_file, skip_unknown_tags=False)
    log.debug (f'found {len(ris_entries)} bibliographies at {ris_file.name}')

    for ris_entry in ris_entries:
        log.debug(f'processing study "{ris_entry["title"]}"')
        if 'notes' in ris_entry:
            ris_entry['notes'] = adjust_rayyan_tags(ris_entry['notes'])

            # counting tags
            for note in ris_entry['notes']:
                        if note.startswith('INCLUSION:'):             inc_ct +=1
                        if note.startswith('EXCLUSION-REASONS:'):     exc_ct +=1
                        if note.startswith('LABELS:'):                lbl_ct +=1
        else:
            log.debug(f'noteless study {ris_entry["title"]}')

    log.info (f'\n\nfound \n\tINCLUSIONS={inc_ct}\n\tEXCLUSIONS={exc_ct}\n\tLABELS={lbl_ct}')



    # adjusting inputed file name extension
    result_file = f'{re.sub("[^.]+$","", ris_file.name)}parsed.{"json" if is_json else "ris"}'

    result_path = Path(result_file).absolute()
    log.info (f'saving {len(ris_entries)} entries at {result_file} ')
    if is_json:
        write_json(ris_entries, result_path)
    else:
        write_ris(ris_entries, result_path)



def parse_cli_args():
    parser = argparse.ArgumentParser(
        description='various scripts to support a systematic literature review',
        epilog='happy research! :)')

    subparsers = parser.add_subparsers(dest="script", required=True, help="available scripts")
    
    #  RIS files
    ris_parser = subparsers.add_parser('ris', help='work with RIS files')
    ris_parser.add_argument('ris_file', 
        metavar='RIS_file', 
        type=argparse.FileType('r'),
        help='RIS file containing studies')


    #  Rayyan parsing
    rayyan_parser = subparsers.add_parser('rayyan', 
        help='take an RIS file, split comments  RAYYAN-INCLUSION, \
                RAYYAN-EXCLUSION-REASONS and RAYYAN-LABELS into dedicated entries. \
                Results are saved into a file named "-parsed"')
    rayyan_parser.add_argument('ris_file', 
        metavar='RIS_file', 
        type=argparse.FileType('r'),
        help='RIS file containing studies'
    )
    rayyan_parser.add_argument('--json', \
        action='store_true', 
        required=False, 
        help='Save JSON format instead of RIS')


    # google scholar
    scholar_parser = subparsers.add_parser('scholar', help='find titles URL from scholar and open on browser')
    scholar_parser.add_argument('ris_file', 
        metavar='RIS_file', 
        type=argparse.FileType('r'),
        help='RIS file containing studies')


    args = parser.parse_args()
    return args



if __name__ == "__main__":
    args = parse_cli_args()

    
    if args.script == "ris":
        [log.info(title) for title in list_titles_from_ris(args.ris_file)]

    if args.script =="rayyan":
        parse_rayyan_metadata(args.ris_file, args.json)

    if args.script =="scholar":
        find_studies_url_and_open_browser(args.ris_file)
        # [print (t) for t in list_titles_without_pdf_from_ris(args.ris_file)]












