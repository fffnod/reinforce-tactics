"""Compatibility shim: the real entry point lives in reinforcetactics.cli.main.

Kept so documented ``python main.py ...`` invocations keep working; the
installed ``reinforce-tactics`` console script targets the package directly.
"""

from reinforcetactics.cli.main import main

if __name__ == "__main__":
    main()
