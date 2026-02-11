# Standard library
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)

class UnifiedChemicalValidator:
    """
    Validates chemical identifiers against PubChem database.

    Supports two modes:
    - SMILES Retrieval: Name + CAS -> retrieve SMILES from PubChem
    - Full Validation: Name + CAS + SMILES -> validate all three

    Attributes:
        input_path: Path to input CSV or Excel file
        output_folder: Output directory (None=cwd, 'auto', or custom path)
        validation_results: List of validation result dictionaries
        smiles_retrieval_mode: Boolean indicating operational mode
    """

    def __init__(self, input_path: str, output_folder: Optional[str] = None):
        self.input_path = input_path
        self.output_folder = output_folder
        self.validation_results: List[Dict[str, Any]] = []
        self.smiles_retrieval_mode = False

    def normalize_cas(self, cas: Any) -> Optional[str]:
        """
        Normalize CAS number to standard format: XXXXX-XX-X.

        Handles various separator characters (unicode dashes, slashes, spaces)
        and converts them to standard hyphen format.

        Args:
            cas: Raw CAS number, may have non-standard separators or None

        Returns:
            Normalized CAS string in format XXXXX-XX-X, or None if invalid
        """
        if cas is None:
            return None

        cas_str = str(cas).strip()
        if not cas_str:
            return None

        # Handle common missing-value sentinels from dataframes.
        if cas_str.lower() == "nan" or cas_str == "<NA>":
            return None

        # Replace any run of non-digits (unicode dashes, slashes, spaces, etc.) with a single dash
        cas_str = re.sub(r"[^\d]+", "-", cas_str).strip("-")

        digits_only = cas_str.replace("-", "")
        if not digits_only.isdigit() or len(digits_only) < 5:
            return cas_str

        check_digit = digits_only[-1]
        middle = digits_only[-3:-1]
        first = digits_only[:-3]
        return f"{first}-{middle}-{check_digit}"

    def identify_columns(self, df: "pd.DataFrame") -> Tuple[str, str, Optional[str]]:
        """
        Identify Name, CAS, and optionally SMILES columns in the dataframe.

        Sets smiles_retrieval_mode based on whether a SMILES column is found.

        Args:
            df: Input dataframe to scan for column names

        Returns:
            Tuple of (name_col, cas_col, smiles_col) where smiles_col may be None

        Raises:
            ValueError: When Name or CAS columns cannot be found
        """
        name_col = None
        cas_col = None
        smiles_col = None

        for col in df.columns:
            col_lower = str(col).lower()
            if not name_col and 'name' in col_lower:
                name_col = col
            if not cas_col and 'cas' in col_lower and 'cassia' not in col_lower:
                cas_col = col
            if not smiles_col and ('smiles' in col_lower or col_lower == 'smile'):
                smiles_col = col

        if not name_col or not cas_col:
            raise ValueError("Could not find Name or CAS columns")

        # Determine mode based on SMILES column presence
        if smiles_col is None:
            self.smiles_retrieval_mode = True
            logger.info("MODE: SMILES RETRIEVAL - SMILES column not found, will retrieve from PubChem")
        else:
            self.smiles_retrieval_mode = False
            logger.info("MODE: FULL VALIDATION - Name, CAS, and SMILES columns detected")

        return name_col, cas_col, smiles_col

    def query_pubchem_cid_and_inchikey(self, identifier: Optional[str], namespace: str = 'name') -> Tuple[Optional[str], Optional[str]]:
        """
        Query PubChem for CID and InChIKey with rate limiting.

        Args:
            identifier: Chemical identifier string (name, CAS, or SMILES)
            namespace: PubChem namespace to search ('name' or 'smiles')

        Returns:
            Tuple of (cid, inchikey), both None if not found
        """
        if not identifier:
            return None, None

        try:
            import pubchempy as pcp

            time.sleep(0.2)  # Rate limiting
            compounds = pcp.get_compounds(identifier, namespace)
            if compounds:
                compound = compounds[0]
                cid = compound.cid
                inchikey = compound.inchikey if hasattr(compound, 'inchikey') else None
                return cid, inchikey
        except Exception as e:
            logger.debug(f"PubChem query failed for {identifier}: {e}")
            pass

        return None, None

    def get_smiles_from_pubchem(self, cid: str) -> Optional[str]:
        """Retrieve SMILES from PubChem CID."""
        if not cid:
            return None

        try:
            import pubchempy as pcp

            time.sleep(0.2)
            compound = pcp.Compound.from_cid(cid)
            smiles = compound.smiles if hasattr(compound, 'smiles') else None
            return smiles
        except Exception as e:
            logger.warning(f"Failed to retrieve SMILES for CID {cid}: {e}")
            return None

    def retrieve_smiles(self, row_num: int, name: Optional[str], cas: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Retrieve SMILES from PubChem using Name and CAS.

        Queries PubChem by both identifiers and returns the SMILES
        only if both resolve to the same CID.

        Args:
            row_num: Row number for logging
            name: Chemical name
            cas: CAS number (raw, will be normalized)

        Returns:
            Tuple of (smiles, cid_by_name, cid_by_cas, rejection_reason)
        """
        logger.info(f"Retrieving SMILES for row {row_num}...")

        # Query by Name
        cid_by_name, _ = self.query_pubchem_cid_and_inchikey(name, 'name')

        # Query by CAS
        cas_normalized = self.normalize_cas(cas)
        cid_by_cas, _ = self.query_pubchem_cid_and_inchikey(cas_normalized, 'name')
        if not cid_by_cas and cas_normalized:
            cid_by_cas, _ = self.query_pubchem_cid_and_inchikey(
                cas_normalized.replace('-', ''), 'name'
            )

        # Check if both found and match
        if cid_by_name and cid_by_cas:
            if cid_by_name == cid_by_cas:
                smiles = self.get_smiles_from_pubchem(cid_by_name)
                if smiles:
                    return smiles, cid_by_name, cid_by_cas, None
                else:
                    return None, cid_by_name, cid_by_cas, 'complex_chemical_no_smiles'
            else:
                return None, cid_by_name, cid_by_cas, 'pubchem_discordance'
        else:
            return None, cid_by_name, cid_by_cas, 'identifier_not_found'

    def validate_chemical(
        self,
        row_num: int,
        name: Optional[str],
        cas: Optional[str],
        smiles: Optional[str],
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Validate a single chemical's identifiers against PubChem.

        Queries PubChem by name, CAS, and SMILES, then checks that all
        resolved CIDs match. In retrieval mode, fetches SMILES first.

        Args:
            row_num: Row number in the input file
            name: Chemical name
            cas: CAS number (raw)
            smiles: SMILES string (None in retrieval mode)
            progress_callback: Optional callback for GUI live updates

        Returns:
            Dictionary with validation results including status and rejection_reason
        """
        if progress_callback:
            progress_callback(f"Row {row_num}: {name}")

        logger.info(f"Row {row_num}: {name}")

        result = {
            'row_number': row_num,
            'name': name,
            'cas': cas,
            'smiles': smiles,
            'smiles_source': 'input' if smiles else None,
            'cid_by_name': None,
            'cid_by_cas': None,
            'cid_by_smiles': None,
            'inchikey_by_name': None,
            'inchikey_by_cas': None,
            'inchikey_by_smiles': None,
            'validated_cid': None,
            'validated_inchikey': None,
            'validated_canonical_inchikey_14': None,
            'status': 'unknown',
            'rejection_reason': None,
            'exact_duplicate_group': None,
            'stereo_duplicate_group': None
        }

        # Trim strings
        if name and isinstance(name, str):
            name = name.strip()
            result['name'] = name
        if smiles and isinstance(smiles, str):
            smiles = smiles.strip()
            result['smiles'] = smiles

        name_ok = bool(name and str(name).strip())
        cas_ok = bool(cas and str(cas).strip())
        smiles_ok = bool(smiles and str(smiles).strip())

        if self.smiles_retrieval_mode:
            # Retrieval mode: must have BOTH name and cas
            if not (name_ok and cas_ok):
                result['status'] = 'rejected'
                result['rejection_reason'] = 'insufficient_identifiers'
                return result
        else:
            # Full validation mode: must have SMILES and (name OR cas)
            if not (smiles_ok and (name_ok or cas_ok)):
                result['status'] = 'rejected'
                result['rejection_reason'] = 'insufficient_identifiers'
                return result

        # If in SMILES retrieval mode, retrieve SMILES first (only when smiles missing)
        if self.smiles_retrieval_mode and not smiles_ok:
            retrieved_smiles, cid_name, cid_cas, rejection = self.retrieve_smiles(row_num, name, cas)

            if retrieved_smiles:
                result['smiles'] = retrieved_smiles
                result['smiles_source'] = 'pubchem'
                smiles = retrieved_smiles
                smiles_ok = True
            else:
                result['status'] = 'rejected'
                result['rejection_reason'] = rejection
                result['cid_by_name'] = cid_name
                result['cid_by_cas'] = cid_cas
                return result

        # Normalize CAS
        cas_normalized = self.normalize_cas(cas)
        result['cas'] = cas_normalized

        # Query PubChem for all three identifiers

        # Query by Name
        cid_by_name, inchikey_by_name = self.query_pubchem_cid_and_inchikey(name, 'name')
        result['cid_by_name'] = cid_by_name
        result['inchikey_by_name'] = inchikey_by_name

        # Query by CAS
        cid_by_cas, inchikey_by_cas = self.query_pubchem_cid_and_inchikey(cas_normalized, 'name')
        if not cid_by_cas and cas_normalized:
            cid_by_cas, inchikey_by_cas = self.query_pubchem_cid_and_inchikey(
                cas_normalized.replace('-', ''), 'name'
            )
        result['cid_by_cas'] = cid_by_cas
        result['inchikey_by_cas'] = inchikey_by_cas

        # Query by SMILES
        cid_by_smiles, inchikey_by_smiles = self.query_pubchem_cid_and_inchikey(smiles, 'smiles')
        result['cid_by_smiles'] = cid_by_smiles
        result['inchikey_by_smiles'] = inchikey_by_smiles

        # Analyze what we found
        found_cids = {}
        if cid_by_name:
            found_cids['name'] = cid_by_name
        if cid_by_cas:
            found_cids['cas'] = cid_by_cas
        if cid_by_smiles:
            found_cids['smiles'] = cid_by_smiles

        num_found = len(found_cids)

        # Check PubChem consistency
        if num_found == 3:
            if cid_by_name == cid_by_cas == cid_by_smiles:
                result['status'] = 'validated'
                result['validated_cid'] = cid_by_name

                validated_inchikey = inchikey_by_name or inchikey_by_cas or inchikey_by_smiles
                result['validated_inchikey'] = validated_inchikey
                if validated_inchikey:
                    result['validated_canonical_inchikey_14'] = validated_inchikey[:14]
                return result
            else:
                result['status'] = 'rejected'
                result['rejection_reason'] = 'pubchem_discordance'
                return result

        elif num_found == 2:
            unique_cids = set(found_cids.values())
            if len(unique_cids) == 1:
                result['status'] = 'rejected'
                result['rejection_reason'] = 'identifier_not_found'
                return result
            else:
                result['status'] = 'rejected'
                result['rejection_reason'] = 'identifier_not_found_and_pubchem_discordance'
                return result

        else:
            result['status'] = 'rejected'
            result['rejection_reason'] = 'identifier_not_found'
            return result

    def check_exact_duplicates(self) -> bool:
        """
        Check for exact duplicates based on full InChIKey match.

        Keeps the first occurrence as validated, rejects subsequent ones.
        Mutates validation_results in place.

        Returns:
            True (always succeeds)
        """
        logger.info("Checking exact duplicates...")

        validated = [r for r in self.validation_results if r['status'] == 'validated']
        with_inchikey = [r for r in validated if r['validated_inchikey']]

        inchikey_groups = {}
        for chem in with_inchikey:
            inchikey = chem['validated_inchikey']
            inchikey_groups.setdefault(inchikey, []).append(chem)

        duplicate_group_num = 1
        duplicates_found = False

        for inchikey, chems in inchikey_groups.items():
            if len(chems) > 1:
                for i, chem in enumerate(chems):
                    if i == 0:
                        chem['exact_duplicate_group'] = duplicate_group_num
                    else:
                        chem['status'] = 'rejected'
                        chem['rejection_reason'] = 'exact_duplicate'
                        chem['exact_duplicate_group'] = duplicate_group_num
                duplicate_group_num += 1
                duplicates_found = True

        return True

    def check_stereoisomer_duplicates(self) -> bool:
        """
        Check for stereoisomer duplicates based on 14-char canonical InChIKey.

        Keeps the first occurrence, marks subsequent ones as stereo_duplicate.
        Mutates validation_results in place. Must run after check_exact_duplicates.

        Returns:
            True (always succeeds)
        """
        logger.info("Checking stereoisomer duplicates...")

        non_rejected = [r for r in self.validation_results if r['status'] != 'rejected']
        with_canonical = [r for r in non_rejected if r['validated_canonical_inchikey_14']]

        canonical_groups = {}
        for chem in with_canonical:
            canonical = chem['validated_canonical_inchikey_14']
            canonical_groups.setdefault(canonical, []).append(chem)

        duplicate_group_num = 1
        duplicates_found = False

        for canonical, chems in canonical_groups.items():
            if len(chems) > 1:
                for i, chem in enumerate(chems):
                    if i == 0:
                        chem['stereo_duplicate_group'] = duplicate_group_num
                    else:
                        chem['status'] = 'stereo_duplicate'
                        chem['stereo_duplicate_group'] = duplicate_group_num
                duplicate_group_num += 1
                duplicates_found = True

        return True

    def validate_csv(self, progress_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Main validation workflow: read input, validate each row, check duplicates.

        Supports both CSV and Excel (.xlsx/.xls) input files.

        Args:
            progress_callback: Optional callback for GUI live updates

        Returns:
            True if no chemicals were rejected, False otherwise
        """
        logger.info(f"Reading file: {self.input_path}")
        if progress_callback:
            progress_callback(f"Reading file: {self.input_path}")

        try:
            import pandas as pd

            input_path = Path(self.input_path)
            if input_path.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(self.input_path)
            else:
                df = pd.read_csv(self.input_path, encoding='utf-8')
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            if progress_callback:
                progress_callback(f"Error reading file: {e}")
            return False

        logger.info(f"Rows: {len(df)}")

        try:
            name_col, cas_col, smiles_col = self.identify_columns(df)
        except ValueError as e:
            logger.error(f"{e}")
            if progress_callback:
                progress_callback(f"Error: {e}")
            return False

        if smiles_col is None:
            mask_keep = ~(
                df[name_col].isna() & df[cas_col].isna()
            )
        else:
            mask_keep = ~(
                df[name_col].isna() & df[cas_col].isna() & df[smiles_col].isna()
            )
        df = df[mask_keep]

        logger.info(f"Processing {len(df)} chemicals...")

        for idx, row in df.iterrows():
            name_value = row[name_col]
            cas_value = row[cas_col]
            smiles_value = row[smiles_col] if smiles_col else None

            # Trim name if present
            if name_value and isinstance(name_value, str):
                name_value = name_value.strip()

            # Trim SMILES if present
            if smiles_value and isinstance(smiles_value, str):
                smiles_value = smiles_value.strip()

            result = self.validate_chemical(idx + 1, name_value, cas_value, smiles_value, progress_callback)
            self.validation_results.append(result)

        # Check duplicates (order matters!)
        self.check_exact_duplicates()
        self.check_stereoisomer_duplicates()

        # Generate summary for logs
        validated = [r for r in self.validation_results if r['status'] == 'validated']
        stereo_dups = [r for r in self.validation_results if r['status'] == 'stereo_duplicate']
        rejected = [r for r in self.validation_results if r['status'] == 'rejected']

        summary = f"\nValidation Complete:\n  Validated: {len(validated)}\n  Stereo Duplicates: {len(stereo_dups)}\n  Rejected: {len(rejected)}"
        logger.info(summary)
        if progress_callback:
            progress_callback(summary)

        return len(rejected) == 0

    def save_results(self) -> bool:
        """
        Save validation results to Excel with auto-column-width and filters.

        Output is an .xlsx file with auto-filter enabled on all columns
        and column widths adjusted to fit content (capped at 50 chars).

        Returns:
            True if file was saved successfully, False on error
        """
        input_file = Path(self.input_path)
        input_stem = input_file.stem.lower().replace(' ', '_')
        input_stem = re.sub(r'_\d{8}_\d{6}$', '', input_stem)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"validation_results_{input_stem}_{timestamp}.xlsx"

        if self.output_folder is None:
            output_dir = Path.cwd()
            output_file = output_dir / filename
            logger.info(f"Output location: Current directory")
        elif self.output_folder == 'auto':
            output_dir = Path("output") / input_stem
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / filename
            logger.info(f"Output location: Auto subfolder (output/{input_stem}/)")
        else:
            output_dir = Path(self.output_folder)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / filename
            logger.info(f"Output location: Custom folder ({self.output_folder})")

        import pandas as pd
        all_df = pd.DataFrame(self.validation_results)

        column_order = [
            'row_number',
            'name',
            'cas',
            'smiles',
            'smiles_source',
            'cid_by_name',
            'cid_by_cas',
            'cid_by_smiles',
            'inchikey_by_name',
            'inchikey_by_cas',
            'inchikey_by_smiles',
            'validated_cid',
            'validated_inchikey',
            'validated_canonical_inchikey_14',
            'status',
            'rejection_reason',
            'exact_duplicate_group',
            'stereo_duplicate_group'
        ]

        # Ensure all columns exist even if empty
        for col in column_order:
            if col not in all_df.columns:
                all_df[col] = None

        all_df = all_df[column_order]

        # Write to Excel with formatting
        try:
            from openpyxl.utils import get_column_letter

            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                all_df.to_excel(writer, index=False, sheet_name='Validation Results')

                workbook = writer.book
                worksheet = writer.sheets['Validation Results']

                # Auto-filter
                worksheet.auto_filter.ref = worksheet.dimensions

                # Auto-width columns
                for i, col in enumerate(all_df.columns):
                    col_max = all_df[col].astype(str).str.len().max()
                    # col_max is NaN when the column is empty
                    if col_max != col_max:
                        col_max = 0
                    max_len = int(max(col_max, len(col))) + 2
                    # Cap width at 50 chars to avoid super wide columns
                    width = min(max_len, 50)
                    col_letter = get_column_letter(i + 1)
                    worksheet.column_dimensions[col_letter].width = width

            logger.info(f"Results saved to: {output_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return False
