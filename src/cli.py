"""Command-line interface for the NCTP Chemical Validator."""

# Standard library
import argparse
import logging
import sys
from pathlib import Path

# Local
from src.validator import UnifiedChemicalValidator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def main():
    """
    Parse CLI arguments and run the validation workflow.

    Validates a CSV or Excel file of chemical identifiers against PubChem,
    then saves results to an Excel file regardless of validation outcome.
    """
    parser = argparse.ArgumentParser(
        description='Unified Chemical Validator - handles both Name+CAS and Name+CAS+SMILES inputs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  Name + CAS only:        Retrieves SMILES from PubChem, then validates
  Name + CAS + SMILES:    Validates all three identifiers directly

Output folder options:
  (no flag)              Save to current directory
  --output-folder        Auto subfolder: output/{input_name}/
  --output-folder PATH   Save to custom folder PATH
        """
    )
    parser.add_argument('input_file', help='Input file path (CSV or Excel)')
    parser.add_argument(
        '--output-folder',
        nargs='?',
        const='auto',
        default=None,
        metavar='PATH',
        help='Output folder location (optional: use flag alone for auto subfolder, or specify custom path)'
    )

    args = parser.parse_args()

    if not Path(args.input_file).exists():
        logger.error(f"Not found: {args.input_file}")
        sys.exit(1)

    logger.info("=" * 70)
    logger.info("UNIFIED CHEMICAL VALIDATOR (CLI)")
    logger.info("=" * 70)

    validator = UnifiedChemicalValidator(args.input_file, args.output_folder)
    success = validator.validate_csv()

    # Always save results — rejected rows still need to appear in output
    validator.save_results()

    if success:
        logger.info("Validation complete — all chemicals passed.")
        sys.exit(0)
    else:
        logger.warning("Validation complete — some chemicals were rejected. See output file.")
        sys.exit(1)


if __name__ == "__main__":
    main()
