#!/usr/bin/env python
"""One-command driver for the complete reproducible analysis pipeline."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(command: list[str]) -> None:
    print('\n' + '=' * 100)
    print(' '.join(command))
    print('=' * 100)
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-root', required=True, help='Frozen exploratory project containing final datasets')
    parser.add_argument('--bootstrap', type=int, default=2000)
    parser.add_argument(
        '--skip-m160',
        action='store_true',
        help='Skip the larger N=1600, m=160 local analysis for a faster smoke reproduction.',
    )
    args = parser.parse_args()

    scripts = Path(__file__).resolve().parent
    python = sys.executable
    common = ['--project-root', args.project_root]

    run([python, str(scripts / '00_check_inputs.py'), *common])
    run([python, str(scripts / '00b_check_response_semantics.py'), *common])

    for n in (100, 400, 1600):
        run([
            python, str(scripts / '01_global_analysis.py'), *common,
            '--N', str(n), '--bootstrap', str(args.bootstrap),
        ])

    # Both linear and nonlinear local controls are part of the final audit.
    for dataset in ('N400_m10', 'N400_m10_T300', 'N1600_m10'):
        run([
            python, str(scripts / '02_local_analysis.py'), *common,
            '--dataset', dataset, '--algorithm', 'both', '--bootstrap', str(args.bootstrap),
        ])

    if not args.skip_m160:
        run([
            python, str(scripts / '02_local_analysis.py'), *common,
            '--dataset', 'N1600_m160', '--algorithm', 'both', '--bootstrap', str(args.bootstrap),
        ])

    run([python, str(scripts / '03_validate_reference_results.py')])
    run([python, str(scripts / '04_make_final_tables.py')])
    run([python, str(scripts / '05_make_final_figures.py')])

    print('\nFinal pipeline completed.')
    print('Audit:   results/final/reference_validation.csv')
    print('Semantics: results/final/response_semantics_audit.csv')
    print('Tables:  results/final/tables/')
    print('Figures: figures/final/')
    if args.skip_m160:
        print('N=1600, m=160 recomputation was skipped (--skip-m160).')


if __name__ == '__main__':
    main()
