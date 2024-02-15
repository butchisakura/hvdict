import os
import xml.etree.ElementTree as ET
import glob
import re
import csv
import sys
import base64

HASH_WORD = "#word"
HASH_STRUCT = "#struct"
HASH_PRONUN = "#pronun"
HASH_MEAN = "#mean"
HASH_PICTURE = "#picture"
HASH_NOTE = "#note"
HASH_TAG = "#tag"

SECTION_WORD = "## Word"
SECTION_STRUCT = "## Cấu trúc"
SECTION_PRONUN = "## Phát âm"
SECTION_MEAN = "## Nghĩa"
SECTION_PICTURE = "## Hình ảnh"
SECTION_NOTE = "## Ghi chú"
SECTION_TAG = "## Tags"

def encode_base64(str):
    # call decode to remove b''
    return base64.b64encode(str.encode("utf-8")).decode("ascii")

def decode_base64(str):
    # call decode to remove b''
    return base64.b64decode(str).decode("utf-8")

def replace_chars(s):
    if not s:
        return s
    # anh huong den image markdown
    # s = s.replace("[", "/")
    # s = s.replace("]", "/")
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

    # Word | Pronun | Mean | Picture | Note | Tag | Structure
    for w in hv_words:
        lines = []

        # Word
        lines.append("# " + w["name"])
        lines.append("")

        # lines.append("## " + "Cấu trúc")

        if w.get("pronunciation"):
            pronuns = w["pronunciation"].split(",")
            lines.append(SECTION_PRONUN)
            lines.extend(["* " + replace_chars(p) for p in pronuns if p])
            lines.append("")

        if w.get("meaning"):
            means = w["meaning"].split("\\r\\n")
            lines.append(SECTION_MEAN)

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
            lines.append(SECTION_TAG)
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
            line = line.replace("# Phát âm", SECTION_PRONUN)
        if re.match(r"^# Nghĩa$", line):
            line = line.replace("# Nghĩa", SECTION_MEAN)
        if re.match(r"^# Tags$", line):
            line = line.replace("# Tags", SECTION_TAG)
        if re.match(r"^# Hình ảnh$", line):
            line = line.replace("# Hình ảnh", SECTION_PICTURE)
        if re.match(r"^# Ghi chú$", line):
            line = line.replace("# Ghi chú", SECTION_NOTE)

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
        tokens.append(SECTION_STRUCT)
        tokens.extend(structure_parts)
        tokens.append("")

        targets = [SECTION_STRUCT, SECTION_PRONUN, SECTION_MEAN, SECTION_TAG]
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

def get_section_hash(lines, index):
    idx = index
    while idx >= 0:
        line = lines[idx]
        if re.match(r"^#[^#]+", line):
            return HASH_WORD
        if re.match(r"^" + SECTION_STRUCT, line):
            return HASH_STRUCT
        if re.match(r"^" + SECTION_PRONUN, line):
            return HASH_PRONUN
        if re.match(r"^" + SECTION_MEAN, line):
            return HASH_MEAN
        if re.match(r"^" + SECTION_PICTURE, line):
            return HASH_PICTURE
        if re.match(r"^" + SECTION_NOTE, line):
            return HASH_NOTE
        if re.match(r"^" + SECTION_TAG, line):
            return HASH_TAG
        idx = idx - 1   # down from current line to 0
    return "#unknown"

def export_csv():
    current_dir = os.path.dirname(__file__)
    working_dir = current_dir + "../../../src/w/"
    working_dir = os.path.abspath(working_dir)

    md_files = glob.glob(working_dir + "/*.md")
    print("Number files %s" % len(md_files))

    # Word | Pronun | Mean | Picture | Note | Tag | Structure
    header_row = [
       "#word",
        HASH_PRONUN,
        HASH_MEAN,
        HASH_PICTURE,
        HASH_NOTE,
        HASH_TAG,
        HASH_STRUCT
    ]

    rows = []
    for f in md_files:
        filename = os.path.basename(f)
        print("Reading file ", filename)

        content = ""
        with open(f, "r", encoding="utf-8") as fp:
            content = fp.read()
        
        data_word = ""
        data_structure = ""
        data_pronun_parts = []       
        data_mean_parts = []
        data_picture_parts = []
        data_note_parts = []
        data_tag_parts = []

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

            section_hash = get_section_hash(lines, idx)

            # Word: single
            if not data_word and section_hash == HASH_WORD:
                data_word = lines[idx][2:]
                continue

            # Struct: single
            if not data_structure and section_hash == HASH_STRUCT:
                if lines[idx] == SECTION_STRUCT:
                    continue
                # * x = [y](y.md) [z](z.md) [t](t.md)
                # re.findall(r"\[([^]]+)\]", data)
                parts = re.findall(r"\[([^]]+)\]", lines[idx][2:])
                data_structure = " ".join(parts)
                continue
            
            # Pronun: array
            if section_hash == HASH_PRONUN:
                if lines[idx] == SECTION_PRONUN:
                    continue
                data_pronun_parts.append(lines[idx][2:])
                continue

            # Mean: array
            if section_hash == HASH_MEAN:
                if lines[idx] == SECTION_MEAN:
                    continue
                # accumulate item then re-overwrite
                data_mean_parts.append(lines[idx][2:])
                continue

            # Picture: array
            if section_hash == HASH_PICTURE:
                if lines[idx] == SECTION_PICTURE:
                    continue
                # accumulate item then re-overwrite
                data_picture_parts.append(lines[idx][2:])
                continue
            
            # Note: array
            if section_hash == HASH_NOTE:
                if lines[idx] == SECTION_NOTE:
                    continue
                # accumulate item then re-overwrite
                data_note_parts.append(lines[idx][2:])
                continue

            # Tag: array
            if section_hash == HASH_TAG:
                if lines[idx] == SECTION_TAG:
                    continue
                # accumulate item then re-overwrite
                data_tag_parts.append(lines[idx][2:])
                continue


        # Word | Pronun | Mean | Picture | Note | Tag | Structure
        row = [
            data_word, 
            "\n".join(data_pronun_parts).replace("\n", "\\n"),
            "\n".join(data_mean_parts).replace("\n", "\\n"), 
            encode_base64("\n".join(data_picture_parts).replace("\n", "\\n")), 
            "\n".join(data_note_parts).replace("\n", "\\n"), 
            "\n".join(data_tag_parts).replace("\n", "\\n"), 
            data_structure
        ]
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
    # headers: Date,Hán Việt,Phát âm,Nghĩa,Ghi chú,Tag,Cấu trúc,0,1,2,3,4,5,6,7,8,9
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, "output", "import.csv")
    if not os.path.exists(file_path):
        print("File not existed: ", file_path)
        return
    
    with open(file_path, "r", encoding="utf-8") as fp:
        rows = csv.reader(fp, delimiter=",")
        row_idx = -1
        for row in rows:
            row_idx = row_idx + 1
            
            # ignore header
            if row_idx == 0:
                print("ignore idx ", row_idx)
                row_idx = row_idx + 1
                continue
            
            # ignore empty line
            if not row[1]:
                print("ignore empty line, idx ", row_idx)
                continue

            # 0: date
            # 1: word
            # 2: pronun
            # 3: mean
            # 4: picture
            # 5: note
            # 6: tag
            # 7: struct
            parts = []

            data_word = row[1]
            parts.append("# " + data_word)
            parts.append("")

            if row[2]:
                parts.append(SECTION_PRONUN)
                tokens = row[2].split("\\n")
                tokens = ["* Hán Việt: " + t.strip() for t in tokens]
                parts.extend(tokens)
                parts.append("")

            if row[3]:
                parts.append(SECTION_MEAN)
                tokens = row[3].split("\\n")
                tokens = ["* " + t.strip() for t in tokens]
                parts.extend(tokens)
                parts.append("")

            if row[4]:
                parts.append(SECTION_PICTURE)
                picture_data = decode_base64(row[4])
                tokens = picture_data.split("\\n")
                tokens = ["* " + t.strip() for t in tokens if t.strip()]
                parts.extend(tokens)
                parts.append("")

            if row[5]:
                parts.append(SECTION_NOTE)
                tokens = row[5].split("\\n")
                tokens = ["* " + t.strip() for t in tokens]
                parts.extend(tokens)
                parts.append("")

            if row[6]:
                parts.append(SECTION_TAG)
                tokens = row[6].split("\\n")
                tokens = ["* " + t.strip() for t in tokens]
                parts.extend(tokens)
                parts.append("")

            if row[7]:
                parts.append(SECTION_STRUCT)
                tokens = row[7].split(" ")
                tokens = ["[%s](%s.md)" % (s.strip(), s.strip()) for s in tokens if s.strip()]
                parts.append("* %s = %s" % (data_word, " ".join(tokens)))
                parts.append("")

            parts.append("<script>window.HANZI_FIELD='%s';</script>" % data_word)

            content = "\n".join(parts)
            content = content.replace("\\n", "\n")

            export_filename = data_word + ".md"
            export_file = os.path.join(current_dir, "output", export_filename)
            with open(export_file, "w", encoding="utf-8") as wp:
                wp.write(content)
            print("Import & output file ", export_filename)

def cli():
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

if __name__ == "__main__":
    # cli()
    # migrate_data()
    # normalize()
    export_csv()
    # import_csv()
