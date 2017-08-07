#!/usr/bin/env python3

import sys
import shutil
import argparse
import os
import json

try:
    from isatools.io import mtbls as MTBLS
except ImportError as e:
    raise RuntimeError("Could not import isatools.io.mtbls package")

help_text = """
ISA slicer - a wrapper for isatools.io.mtbls

Basic usage:
    run_mtblisa.py --command <command> --study <study_id> [--query <query>] [--outpath path]

To get ISA-Tab from MetaboLights:

    run_mtblisa.py --command GET --study <study_id>
eg. run_mtblisa.py --command GET --study MTBLS1
    # writes ISArchive to out.zip

To get ISA-JSON from MetaboLights:

    run_mtblisa.py --command GETJ --study <study_id>
eg. run_mtblisa.py --command GETJ --study MTBLS1
    # writes ISA JSON file to out.json

To get factor names from a study:

    run_mtblisa.py --command GET_FACTORS --study <study_id>
eg. run_mtblisa.py --command GET_FACTORS --study MTBLS1
    # writes result to out.json

To get factor values from a study:

    run_mtblisa.py --command GET_FVS --study <study_id> --query <factor_name>
eg. run_mtblisa.py --command GET_FVS --study MTBLS1 --query "Gender"
    # writes result to out.json

To get data file references from a study (take care to ensure escaping of double quotes):

    run_mtblisa.py --command GET_DATA_FILES --study <study_id> --query <factor_selection>
eg. run_mtblisa.py --command GET_DATA_FILES --study MTBLS1 --query /query.json '{"Gender":"Male"}'
    # writes result to out.json

To get variables summary from a study:

    run_mtblisa.py --command GET_SUMMARY --study <study_id>
eg. run_mtblisa.py --command GET_SUMMARY --study MTBLS1
    # writes result to out.json


"""

# FIXME: remove this temporary fix.
#        This is just to avoid some prints to the stderr stream
#        which cause that the Galaxy job is recognised as failed.
sys.stderr = sys.stdout


def main(args):
    parser = argparse.ArgumentParser(usage=help_text)
    parser.add_argument("--command", help="Command, one of GET GETJ GET_FACTORS GET_FVS GET_DATA_FILES")
    parser.add_argument("--study", help="MetaboLights study ID, e.g. MTBLS1")
    parser.add_argument("--query", help="Query on study")
    parser.add_argument("--outpath", help="Output path")
    parser.add_argument("--out-format", choices=('zip'), help="Output format", default=None)
    args = parser.parse_args(args)

    cmd = args.command if args.command else os.getcwd()
    study_id = args.study if args.study else ""
    query = args.query if args.query else "/query.json"
    outpath = args.outpath if args.outpath else os.getcwd()

    if cmd == 'GET':
        tmpdir = MTBLS.get(study_id)
        if tmpdir is not None:
            print(os.listdir(tmpdir))
            if args.out_format is None:
                # 'outpath' is used as the 'extra_files_path' of the ISA composite dataset
                shutil.move(tmpdir, args.outpath)
                print("Written dataset")
            else:
                os.chdir(outpath)
                shutil.make_archive('out', 'zip', tmpdir)
                shutil.rmtree(tmpdir)
                print("ISA-Tab written to out.zip")
        else:
            print("There was an i/o problem with the ISA-Tab.")
    elif cmd == 'GETJ':
        isajson = MTBLS.getj(study_id)
        if isajson is not None:
            with open("out.json", 'w') as outfile:
                json.dump(isajson, outfile, indent=4)
            print("ISA-JSON written to out.json")
        else:
            print("There was an i/o problem with the ISA-Tab.")
    elif cmd == 'GET_FACTORS':
        factor_names = MTBLS.get_factor_names(study_id)
        if factor_names is not None:
            with open("out.json", 'w') as outfile:
                json.dump(list(factor_names), outfile, indent=4)
            print("Factor names written to out.json")
        else:
            print("There was an i/o problem with the ISA-Tab.")
    elif cmd == 'GET_FVS':
        fvs = MTBLS.get_factor_values(study_id, query)
        if fvs is not None:
            with open("out.json", 'w') as outfile:
                json.dump(list(fvs), outfile, indent=4)
            print("Factor values written to out.json")
        else:
            print("There was an i/o problem with the ISA-Tab.")
    elif cmd == 'GET_DATA_FILES':
        if query is not None:
            with open(query, encoding='utf-8') as query_fp:
                json_query = json.load(query_fp)
                print("running with query: {}".format(json_query))
                data_files = MTBLS.get_data_files(study_id, json_query)
                print("Result data files list: {}".format(data_files))
                if data_files is not None:
                    with open("out.json", 'w') as outfile:
                        print("dumping data_files")
                        json.dump(list(data_files), outfile, indent=4)
                    print("Data files written to out.json")
                else:
                    print("There was an i/o problem with the ISA-Tab.")
        else:
            data_files = MTBLS.get_data_files(study_id)
            if data_files is not None:
                with open("out.json", 'w') as outfile:
                    json.dump(data_files, outfile, indent=4)
                print("Data files written to out.json")
            else:
                print("There was an i/o problem with the ISA-Tab.")
    elif cmd == 'GET_SUMMARY':
        summary = MTBLS.get_study_variable_summary(study_id)
        if summary is not None:
            with open("out.json", 'w') as outfile:
                json.dump(summary, outfile, indent=4)
    else:
        print(help_text)


if __name__ == "__main__":
    main(sys.argv)
