"""
generate indri queries for TS track queries
"""

import lxml.etree as ET
from string import Template

def get_queries(query_file):
    tree = ET.parse(query_file)
    root = tree.getroot()
    queries = {}
    for event in root.iter("event"):
        qid = event.find("id").text
        word_string =event.find("title").text
        all_words = re.findall("\w+",word_string)
        query_string = " ".join(all_words)
        queries[qid] = query_string
    return queries


def main():
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument("--query_file","-q",default="/lustre/scratch/lukuang/Temporal_Summerization/streamcorpus-2014-v0_3_0-ts-filtered/TS14-data/trec2014-ts-topics-test.xml")
    parser.add_argument("--output_file","-o",default="ts2014_query")
    args = parser.parse_args()

    query_template = Template("""
    <query>
        <number>$qid</number>
        <text>$q_string</text>
    </query>
    """)
    structure_template = Template("""
    <parameters>
    <trecFormat>true</trecFormat>
    <runID>UDInfoW2</runID>
    <count>10000</count>
    $query_body
    </parameters>
    """)
    query_body = ""
    queries = get_queries(args.query_file)
    for qid in queries:
        query_body+=query_template.substitute(qid=qid,q_string=queries[qid])

    with open(args.output_file, 'w') as f:
        f.write(structure_template.substitue(query_body=query_body))



if __name__ == '__main__':
    main()