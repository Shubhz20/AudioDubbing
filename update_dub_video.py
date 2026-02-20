with open("dub_video.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "import subprocess" in line:
        new_lines.append(line)
        new_lines.append("import os\n")
        new_lines.append("os.environ['COQUI_TOS_AGREED'] = '1'\n")
        continue
    if "import os\n" == line and "os.environ" not in lines[0]:
        continue # skip duplicate os
    new_lines.append(line)

with open("dub_video.py", "w") as f:
    f.writelines(new_lines)

# Final sync utility scripts updated