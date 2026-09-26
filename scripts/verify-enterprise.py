"""Execute the exact tutorial blocks in separate disposable Git/jj sandboxes."""

import re
import subprocess
from pathlib import Path

for lane in ("git", "jj"):
    page = Path(f"docs/enterprise/{lane}.md").read_text()
    blocks = re.findall(r"```sh\n(.*?)```", page, re.S)
    subprocess.run(
        ["bash", "-eu", "-o", "pipefail"], input="\n".join(blocks), text=True, check=True
    )
    print(f"PASS enterprise {lane} tutorial", flush=True)
