## aartzzUtils
*[Licensed under the GNU General Public License v3.0](LICENSE)*

Plugin for exteraGram aimed to port legacy functions, that removed in newer telegram versions for some reason.

[![Channel](https://img.shields.io/badge/Channel-Telegram-blue.svg)](https://t.me/fossSquad)
[![Download](https://img.shields.io/badge/Download-latest-green.svg)](https://nightly.link/fossSquad/aartzzUtils/workflows/build/main?preview)

> [!WARNING]  
> Plugin in alpha test, except bugs.

### Screenshots
| | |
|---|---|
| <img src="docs/images/1.png" width="140"/> | <img src="docs/images/2.png" width="140"/> |
| Settings | legacy chat UI port |

### Building

**Requirements**
- Python 3.x

```bash
git clone https://github.com/fossSquad/aartzzUtils.git
cd aartzzUtils

python3 -m venv .venv
source .venv/bin/activate

# build plugin
elyb build -v -nf
```

Output will be at `builds` folder.

### Dev builds
Latest dev builds are available as CI artifacts.

### Credits
- [@lostywolfer](https://github.com/lostyawolfer) — concept
- [exteraGram](https://github.com/exteraSquad/exteraGram) — plugin runtime
