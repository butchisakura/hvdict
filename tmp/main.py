import os
import xml.etree.ElementTree as ET

def replace_chars(s):
    if not s:
        return s
    s = s.replace("[", "/")
    s = s.replace("]", "/")
    return s

if __name__ == "__main__":
    current_dir = os.path.dirname(__file__)
    data_path = os.path.join(current_dir, 'data.xml')
    root = ET.parse(data_path).getroot()
    
    word_properties = ["name", "meaning", "pronunciation", "category"]
    words = []
  
    for w in root.findall("word"):
        word = {}
        for p in word_properties:
            word[p] = w.find(p).text
            if word[p]:
                word[p] = word[p].strip()
        words.append(word)
    hv_words = [w for w in words if len(w["name"]) == 1]
    
    for w in hv_words:
        template = ""

        template += "# " + w["name"] + "\r\n"
        template += "\r\n"

        if w.get("meaning"):
            means = w["meaning"].split("\\r\\n")
            template += "# Nghĩa" + "\r\n"
            for m in means:
                if m:
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
                        template += "* " + " ".join(token_parts) + "\r\n"
                    else:
                        template += "* " + replace_chars(m) + "\r\n"
            template += "\r\n"

        if w.get("pronunciation"):
            pronuns = w["pronunciation"].split(",")
            template += "# Phát âm" + "\r\n"
            template += "\r\n".join(["* " + replace_chars(p) for p in pronuns if p]) + "\r\n"
            template += "\r\n"

        if w.get("category"):
            categories = w["category"].split(",")
            template += "# Tags" + "\r\n"
            template += "\r\n".join(["* " + replace_chars(c) for c in categories if c]) + "\r\n"
            template += "\r\n"

        w["template"] = template
        # print(template)

    for w in hv_words:
        filename = w["name"] + ".md"
        file_path = os.path.join(current_dir, "output", filename)
        with open(file_path, "w") as f:
            f.write(w["template"])
        print("created file %s" % filename)

    print(len(words))
    print(len(hv_words))