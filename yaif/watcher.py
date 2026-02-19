"""
YAIF file watcher — monitors a .yaif file and regenerates output on change.
Uses simple polling (no external dependencies).
"""

import time
import os
import sys
from pathlib import Path

from .parser import YAIFParser, YAIFParseError
from .generators import GENERATORS, FILE_EXTENSIONS


def watch(filepath: str, target: str, output: str = None, interval: float = 1.0):
    """Watch a .yaif file and regenerate on change."""
    path      = Path(filepath)
    generator = GENERATORS[target]
    parser    = YAIFParser()
    last_mtime = 0.0

    print(f"Watching {filepath} for changes (target: {target})...")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            try:
                mtime = os.path.getmtime(path)
            except FileNotFoundError:
                print(f"File not found: {filepath} — waiting...", end='\r')
                time.sleep(interval)
                continue

            if mtime != last_mtime:
                last_mtime = mtime
                timestamp  = time.strftime('%H:%M:%S')

                try:
                    interfaces, enums, config = parser.parse_file(filepath)
                    result = generator.generate(interfaces, enums, config)

                    summary = f"{len(interfaces)} interface(s), {len(enums)} enum(s)"

                    if output:
                        Path(output).write_text(result, encoding="utf-8")
                        print(f"[{timestamp}] Regenerated {output} ({summary})")
                    else:
                        print(f"[{timestamp}] Parsed {summary}")
                        print(f"--- Generated {target} ---\n")
                        print(result)

                except YAIFParseError as e:
                    print(f"[{timestamp}] Parse error: {e}")
                except Exception as e:
                    print(f"[{timestamp}] Error: {e}")

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\nStopped watching.")