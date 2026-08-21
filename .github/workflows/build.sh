#!/bin/bash
# Builds the Persian manual with the same pinned prebuilt toolchain used for
# local QA (mdbook 0.4.34 + mdbook-toc 0.14.1 via abdnh/mdbook-binaries, plus
# mdbook-admonish 1.20.0 from its GitHub release).
set -e

cd "$HOME"
git clone --depth 1 https://github.com/abdnh/mdbook-binaries.git
export PATH="$HOME/mdbook-binaries:$PATH"

if [ ! -x "$HOME/mdbook-binaries/mdbook-admonish" ]; then
    curl -sL https://github.com/tommilligan/mdbook-admonish/releases/download/v1.20.0/mdbook-admonish-v1.20.0-x86_64-unknown-linux-gnu.tar.gz \
        | tar xz -C "$HOME/mdbook-binaries"
fi

# linkcheck is version-sensitive; internal links are covered by tools/fa/check.py
rm -f "$HOME/mdbook-binaries/mdbook-linkcheck"

cd "$GITHUB_WORKSPACE"
mdbook build
