"""
conflict.py — Interactive conflict resolution for the YAIF bot module.
Shared by all bot_actions. Tracks "apply to all" state across a full run.
"""


# ─── Resolution Options ───────────────────────────────────────────────────────

SKIP      = 'skip'
OVERWRITE = 'overwrite'
ABORT     = 'abort'


# ─── State ────────────────────────────────────────────────────────────────────

class ConflictResolver:
    """
    Tracks the user's 'apply to all' choice across the entire bot run.
    Pass a single instance into every bot action so the choice persists.
    """

    def __init__(self, dry_run=False):
        self.dry_run   = dry_run
        self._apply_all = None  # None | SKIP | OVERWRITE

    def resolve(self, kind, name):
        """
        Ask the user what to do when `name` (a role, channel, etc.) already exists.
        Returns one of: SKIP, OVERWRITE, ABORT.

        If the user previously chose 'apply to all', returns that immediately.
        In dry_run mode, always returns SKIP without prompting.
        """
        if self.dry_run:
            print(f"  [dry run] Would conflict with existing {kind} '{name}' — skipping.")
            return SKIP

        if self._apply_all is not None:
            return self._apply_all

        print()
        print(f"  ⚠️  {kind.capitalize()} '{name}' already exists.")
        print("       [s] Skip        [S] Skip all")
        print("       [o] Overwrite   [O] Overwrite all")
        print("       [a] Abort")

        while True:
            choice = input("       > ").strip()

            if choice == 's':
                return SKIP
            elif choice == 'S':
                self._apply_all = SKIP
                return SKIP
            elif choice == 'o':
                return OVERWRITE
            elif choice == 'O':
                self._apply_all = OVERWRITE
                return OVERWRITE
            elif choice == 'a':
                return ABORT
            else:
                print("       Invalid choice. Enter s, S, o, O, or a.")