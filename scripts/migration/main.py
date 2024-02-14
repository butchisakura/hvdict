import os
import xml.etree.ElementTree as ET
import glob
import re
import csv
import sys

def replace_chars(s):
    if not s:
        return s
    s = s.replace("[", "/")
    s = s.replace("]", "/")
    s = s.strip()
    return s

def migrate_data():
    """
    Migration data from xml (old format)
    Output to directory: ./output/*.md
    """
    print("Parsing data.xml...")
    current_dir = os.path.dirname(__file__)
    data_path = os.path.join(current_dir, 'data.xml')
    root = ET.parse(data_path).getroot()
    print("Parsed successfully")
    
    word_properties = ["name", "meaning", "pronunciation", "category"]
    words = []
  
    print("Analyzing data...")
    for w in root.findall("word"):
        word = {}
        for p in word_properties:
            word[p] = w.find(p).text
            if word[p]:
                word[p] = word[p].strip()
        words.append(word)
    hv_words = [w for w in words if len(w["name"]) == 1]
    print("Analyzed data done")
    
    print("Generate internal data ...")

    # Word | Structure | Pronun | Mean | Note | Tag
    for w in hv_words:
        lines = []

        lines.append("# " + w["name"])
        lines.append("")

        # lines.append("## " + "Cấu trúc")

        if w.get("pronunciation"):
            pronuns = w["pronunciation"].split(",")
            lines.append("## Phát âm")
            lines.extend(["* " + replace_chars(p) for p in pronuns if p])
            lines.append("")

        if w.get("meaning"):
            means = w["meaning"].split("\\r\\n")
            lines.append("## Nghĩa")

            for m in means:
                if not m:
                    continue
                if "=" in m:
                    tokens = m.split(" ")
                    if len(tokens) <= 1:
                        tokens = m.split("=")
                    token_parts = [
                        tokens[0],
                        tokens[1]
                    ]
                    for i in range(2, len(tokens)):
                        if not tokens[i]:
                            continue
                        if tokens[i] == "=":
                            token_parts.append("=")
                        else:
                            token_parts.append("[%s](%s.md)" % (tokens[i], tokens[i]))
                    lines.append("* " + " ".join(token_parts))
                else:
                    lines.append("* " + replace_chars(m))
            lines.append("")

        # lines.append("## " + "Ghi chú")

        if w.get("category"):
            categories = w["category"].split(",")
            lines.append("## Tags")
            lines.extend(["* " + replace_chars(c) for c in categories if c])
            lines.append("")

        lines.append("<script>window.HANZI_FIELD='%s';</script>" % w["name"])

        w["template"] = "\n".join(lines)
        # print(template)
    print("Generation done")

    # create output directory if not exist
    output_dir = os.path.join(current_dir, "output")
    if not os.path.exists(output_dir):
        print("Create output directory")
        os.mkdir(output_dir)

    print("Exporting ...")
    for w in hv_words:
        filename = w["name"] + ".md"
        file_path = os.path.join(output_dir, filename)
        # UnicodeEncodeError: 'charmap' codec can't encode character 
        # using utf-8 as encoding
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(w["template"])
        print("created file %s" % filename)
    print("Export done")

    print("Raw Words: %s" % len(words))
    print("HV Words: %s" % len(hv_words))
    print("Migration done")

def normalize_heading(filename, content):
    print("normalize_heading file ", filename)
    lines = content.replace("\r\n", "\n").split("\n")
    for idx in range(len(lines)):
        line = lines[idx]

        # migrate # => ##
        if re.match(r"^# Phát âm$", line):
            line = line.replace("# Phát âm", "## Phát âm")
        if re.match(r"^# Nghĩa$", line):
            line = line.replace("# Nghĩa", "## Nghĩa")
        if re.match(r"^# Tags$", line):
            line = line.replace("# Tags", "## Tags")
        if re.match(r"^# Hình ảnh$", line):
            line = line.replace("# Hình ảnh", "## Hình ảnh")
        if re.match(r"^# Ghi chú$", line):
            line = line.replace("# Ghi chú", "## Ghi chú")

        # overwrite
        lines[idx] = line
    return "\n".join(lines)

def normalize_bullet(filename, content):
    print("normalize_bullet file ", filename)
    lines = content.replace("\r\n", "\n").split("\n")
    for idx in range(len(lines)):
        line = lines[idx]

        # replace + => * 
        if line.startswith("+ "):
            line = "* " + line[2:]

        # strip list item
        if line.startswith("* "):
            line = "* " + line[2:].strip()
        
        # overwrite
        lines[idx] = line
    return "\n".join(lines)

def normalize_structure(filename, content):
    print("normalize_structure file ", filename)
    lines = content.replace("\r\n", "\n").split("\n")

    # cut structure from content
    structure_parts = []
    total_lines = len(lines)
    idx=-1
    while idx < total_lines-1:
        idx = idx+1
        line = lines[idx]
        if line == "## Nghĩa":
            while idx < total_lines-1:
                idx = idx+1
                line = lines[idx]
                # * ... = ...md
                if re.match(r"\*.*=.*\.md", line):
                    structure_parts.append(line)
                    lines[idx] = ""
    
    # paste structure
    content = "\n".join(lines)

    if len(structure_parts) > 0:
        tokens = []
        tokens.append("## Cấu trúc")
        tokens.extend(structure_parts)
        tokens.append("")

        targets = ["## Cấu trúc", "## Phát âm", "## Nghĩa", "## Tags"]
        for target in targets:
            if target in content:
                tokens.append(target)
                tokens.append("")
                content = content.replace(target, "\n".join(tokens))
                break

    return content

def normalize_extra_newline(filename, content):
    # remove extra lines
    # \n 1st on previous line #something
    # \n 2nd, 3rd on current + next lines
    # replace with 2 newline (previous, current)
    print("normalize_extra_newline file ", filename)
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content

def normalize_obsolete_pronun(filename, content):
    # /abc/ => abc
    print("normalize_obsolete_pronun file ", filename)
    content = re.sub(r"/(.+)/", "Hán Việt: \\1", content)
    return content

def normalize():
    current_dir = os.path.dirname(__file__)
    working_dir = current_dir + "../../../src/w/"
    working_dir = os.path.abspath(working_dir)
    os.chdir(working_dir)
    print("Changed working directory")
    
    print("Get all files")
    md_files = glob.glob("*.md")
    print("Number files %s" % len(md_files))

    for f in md_files:
        filename = os.path.basename(f)
        print("Reading file ", filename)
        content = ""
        with open(f, "r", encoding="utf-8") as fp:
            content = fp.read()
        
        content = normalize_heading(filename, content)
        content = normalize_bullet(filename, content)       
        content = normalize_structure(filename, content)
        content = normalize_extra_newline(filename, content)
        content = normalize_obsolete_pronun(filename, content)

        # save as
        print("Saving file ", filename)
        with open(f, "w", encoding="utf-8") as fp:
            fp.write(content)
        print("Done file ", filename)

def get_section(lines, index):
    idx = index
    while idx >= 0:
        line = lines[idx]
        if re.match(r"^#[^#]+", line):
            return "#word"
        if re.match(r"^## Cấu trúc", line):
            return "#struct"
        if re.match(r"^## Phát âm", line):
            return "#pronun"
        if re.match(r"^## Nghĩa", line):
            return "#mean"
        if re.match(r"^## Hình ảnh", line):
            return "#picture"
        if re.match(r"^## Ghi chú", line):
            return "#note"
        if re.match(r"^## Tags", line):
            return "#tag"
        idx = idx - 1   # down from current line to 0
    return "#unknown"

def export_csv():
    current_dir = os.path.dirname(__file__)
    working_dir = current_dir + "../../../src/w/"
    working_dir = os.path.abspath(working_dir)

    md_files = glob.glob(working_dir + "/*.md")
    print("Number files %s" % len(md_files))

    header_row = ["word", "pronun", "mean", "structure"]
    rows = []

    for f in md_files:
        filename = os.path.basename(f)
        print("Reading file ", filename)

        content = ""
        with open(f, "r", encoding="utf-8") as fp:
            content = fp.read()
        
        data_word = ""
        data_structure = ""
        data_pronun = ""
        data_mean = ""
        data_means_parts = []

        # 0:word 1:structure 2:mean
        section = 0
        lines = content.split("\n")
        for idx in range(len(lines)):
            # ignore empty line
            if not lines[idx].strip():
                continue

            # ignore script
            if lines[idx].startswith("<script"):
                continue

            section = get_section(lines, idx)

            # get one
            if not data_word and section == "#word":
                data_word = lines[idx][2:]
                continue

            # get one
            if not data_structure and section == "#struct":
                if lines[idx] == "## Cấu trúc":
                    continue
                # * x = [y](y.md) [z](z.md) [t](t.md)
                # re.findall(r"\[([^]]+)\]", data)
                parts = re.findall(r"\[([^]]+)\]", lines[idx][2:])
                data_structure = " ".join(parts)
                continue
            
            # get one
            if not data_pronun and section == "#pronun":
                if lines[idx] == "## Phát âm":
                    continue
                data_pronun = lines[idx][2:].replace("Hán Việt: ", "")
                continue

            # get multiple
            if section == "#mean":
                if lines[idx] == "## Nghĩa":
                    continue
                # accumulate item then re-overwrite
                data_means_parts.append(lines[idx][2:])

                # encode newline to safe for csv
                data_mean = "\n".join(data_means_parts).replace("\n", "\\n")
                continue

        row = [data_word, data_pronun, data_mean, data_structure]
        rows.append(row)

    output_dir = os.path.join(current_dir, "output")
    if not os.path.exists(output_dir):
        print("creating output directory ", output_dir)
        os.mkdir(output_dir)

    print("exporting num rows=", len(rows))
    filepath = os.path.join(output_dir, "export.csv")
    with open(filepath, "w", encoding="utf-8", newline='') as f:
        # delimiter: using , will generate "" if content has comma (current used)
        # Google sheet: using function ARRAYFORMULA(SUBSTITUDE(C1:C,"\n", CHAR(10))
        # + char(10) will generate new line
        # + avoid copy to origin column, just show only on new column
        writer = csv.writer(f, delimiter=",", escapechar=' ')
        writer.writerow(header_row)
        writer.writerows(rows)
    print("export done")

def import_csv():
    # headers: STT,Hán Việt,Phát âm,Nghĩa,Cấu trúc,0,1,2,3,4,5,6,7,8,9
    # data: 4,時,thời,giờ,日 寺,日,寺,,,,,,,,
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, "output", "import.csv")
    if not os.path.exists(file_path):
        print("File not existed: ", file_path)
        return
    
    with open(file_path, "r", encoding="utf-8") as fp:
        rows = csv.reader(fp, delimiter=",")
        row_idx = 0
        for row in rows:
            # ignore header
            if row_idx == 0:
                row_idx = row_idx + 1
                continue
            
            data_word = row[1]

            parts = []
            parts.append("# " + data_word)
            parts.append("")

            if row[4]:
                parts.append("## Cấu trúc")
                tokens = row[4].split(" ")
                tokens = ["[%s](%s.md)" % (s.strip(), s.strip()) for s in tokens]
                parts.append("* %s = %s" % (data_word, " ".join(tokens)))
                parts.append("")

            if row[2]:
                parts.append("## Phát âm")
                tokens = row[2].split(",")
                tokens = ["* Hán Việt: " + t.strip() for t in tokens]
                parts.extend(tokens)
                parts.append("")

            if row[3]:
                parts.append("## Nghĩa")
                tokens = row[3].split(",")
                tokens = ["* " + t.strip() for t in tokens]
                parts.extend(tokens)
                parts.append("")

            parts.append("<script>window.HANZI_FIELD='%s';</script>" % data_word)

            content = "\n".join(parts)
            content = content.replace("\\n", "\n")

            export_filename = data_word + ".md"
            export_file = os.path.join(current_dir, "output", export_filename)
            with open(export_file, "w", encoding="utf-8") as wp:
                wp.write(content)
            print("Import & output file ", export_filename)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("action is required: migrate | normalize | export | import")
        exit(1)
    action = sys.argv[1]
    action_mapping = {
        "migrate": migrate_data,
        "normalize": normalize,
        "export": export_csv,
        "import": import_csv
    }
    action_mapping[action]()
    # migrate_data()
    # normalize()
    # export_csv()
    # import_csv()
