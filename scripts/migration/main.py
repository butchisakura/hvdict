import os
import xml.etree.ElementTree as ET
import glob
import re

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
        if re.match(r"^# Chú giải$", line):
            line = line.replace("# Chú giải", "## Chú giải")

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
        
        # remove extra lines
        content = re.sub(r"\n{2,}+", "\n", content)

        # save as
        print("Saving file ", filename)
        with open(f, "w", encoding="utf-8") as fp:
            fp.write(content)
        print("Done file ", filename)

if __name__ == "__main__":
    # migrate_data()
    normalize()
