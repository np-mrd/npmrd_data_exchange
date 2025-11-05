from rdkit import Chem
from rdkit.Chem import AllChem, rdDepictor, inchi
from typing import List, Dict, Optional, Tuple


class MolBlockAligner:
    """
    MolBlockAligner
    ----------------
    A class to align atom indices between two molecular structures
    (given as MOL blocks) and to remap associated NMR shift data
    (13C and 1H) accordingly.

    The workflow includes:
        1. Loading and verifying both MOL blocks.
        2. Creating a topology-based atom index mapping (mol1 → mol2).
        3. Aligning NMR shift data to the new index mapping.
        4. Returning the aligned C and H shift lists.
    """

    def __init__(self, curation_mol_block: str, db_mol_block: str):
        """Initialize by loading and verifying both MOL blocks."""
        self.curation_mol_block = curation_mol_block
        self.db_mol_block = db_mol_block

        self.curation_mol = self._load_mol_block(curation_mol_block, label="curation_mol_block")
        self.db_mol = self._load_mol_block(db_mol_block, label="db_mol_block")

        # Verification ensures molecules are valid and structurally comparable
        self._verify_molecule(self.curation_mol, label="curation_mol_block")
        self._verify_molecule(self.db_mol, label="db_mol_block")

        # Verify that both mol block align with the same structure
        self._confirm_inchikeys_match()

        # Create deterministic 3D coordinates for reproducibility
        AllChem.EmbedMolecule(self.curation_mol, AllChem.ETKDG())
        AllChem.EmbedMolecule(self.db_mol, AllChem.ETKDG())

        # Build mapping between the two molecules (mol1 → mol2)
        self.mol1_to_mol2 = self._create_index_map()

    # -------------------------------------------------------------------------
    # INTERNAL STEPS
    # -------------------------------------------------------------------------
    def _load_mol_block(self, mol_block: str, label: str) -> Chem.Mol:
        """Convert MOL block string to RDKit Mol object."""
        mol = Chem.MolFromMolBlock(mol_block, removeHs=False)
        if mol is None:
            raise ValueError(f"Error: Unable to parse MOL block for {label}.")
        return mol

    def _verify_molecule(self, mol: Chem.Mol, label: str):
        """Verify that a molecule loaded correctly and contains atoms."""
        if mol is None:
            raise ValueError(f"Molecule '{label}' failed to load (None returned).")
        num_atoms = mol.GetNumAtoms()
        if num_atoms == 0:
            raise ValueError(f"Molecule '{label}' contains 0 atoms.")
        print(f"SUCCESS: Molecule '{label}' successfully loaded with {num_atoms} atoms.")

    def _create_index_map(self) -> Dict[int, int]:
        """Wrapper for get_mol1_to_mol2_index_map logic."""
        return self.get_mol1_to_mol2_index_map(self.curation_mol, self.db_mol)

    def _confirm_inchikeys_match(self):
        """Confirm inchikey result from both mol blocks is the same"""
        inchikey_curation = inchi.MolToInchiKey(self.curation_mol)
        inchikey_db = inchi.MolToInchiKey(self.db_mol)
        if inchikey_curation != inchikey_db:
            raise ValueError(
                f"Molecules do not represent the same structure:\n"
                f"  curation_mol InChIKey: {inchikey_curation}\n"
                f"  db_mol InChIKey: {inchikey_db}"
            )

    # -------------------------------------------------------------------------
    # CORE MAPPING FUNCTION (original logic preserved)
    # -------------------------------------------------------------------------
    def get_mol1_to_mol2_index_map(self, mol1: Chem.Mol, mol2: Chem.Mol) -> Dict[int, int]:
        """
        Align mol2 onto mol1 and generate an atom index mapping (mol1 -> mol2)
        based on **2D structural topology** (not accounting for 3D coordinates).

        Since both molecules are assumed to originate from SMILES (without
        meaningful 3D coordinates), this function uses RDKit’s 2D depiction
        layout to achieve a deterministic and topology-based alignment.

        ABOUT ATOM INDEXING
        ----------------------
        RDKit internally indexes atoms starting at **0** (Python-style indexing).
        However, exported MOL blocks, as well as most per-atom property lists
        (e.g., NMR chemical shift tables, partial charge lists), use **1-based indexing**.
        To keep this consistent with external data and file formats, this function
        returns a **1-based atom index mapping** — meaning atom index `0` in RDKit
        becomes `1` in the returned dictionary.

        Example:
            RDKit atom index 0 → MOL index 1
            RDKit atom index 1 → MOL index 2
            ...

        The mapping therefore directly aligns with how atoms are numbered in
        exported 3D MOL blocks and related property lists.


        ---
        HOW IT WORKS
        -------------
        1. **Adds hydrogens consistently** to both molecules to ensure atom
        counts and bond structures match.
        2. **Generates 2D coordinates** (instead of 3D embedding) using
        RDKit’s `Compute2DCoords` — this gives reproducible, flattened
        coordinates that reflect molecular topology.
        3. **Finds a substructure match** to map atoms in mol1 → mol2 using
        graph connectivity (bond topology).
        4. **Aligns mol2 to mol1 in 2D coordinate space** using the derived
        atom mapping.
        5. **Returns a mapping dictionary** whose indices start at **1** to
        match the numbering convention used in human-readable molecular
        formats (like MOL/SDF blocks), even though RDKit uses 0-based
        indices internally.

        ---
        WHY 2D ALIGNMENT?
        -----------------
        - More deterministic and reproducible than 3D embedding.
        - Not dependent on stochastic force-field geometry optimization.
        - Ideal when molecules share the same structure but lack explicit
        3D conformation (e.g., both loaded from SMILES).

        ---
        Args:
            mol1 (Chem.Mol): Reference molecule.
            mol2 (Chem.Mol): Molecule to align onto mol1.

        Returns:
            tuple:
                mol1_to_mol2 (dict):
                    Mapping of **mol1 atom indices → mol2 atom indices**,
                    but with numbering starting from **1** (human-readable).
                    Example: `{1: 1, 2: 2, 3: 3, ...}`
        """
        mol1_copy = Chem.AddHs(Chem.Mol(mol1))
        mol2_copy = Chem.AddHs(Chem.Mol(mol2))

        rdDepictor.Compute2DCoords(mol1_copy)
        rdDepictor.Compute2DCoords(mol2_copy)

        substruct_match = mol2_copy.GetSubstructMatch(mol1_copy)
        if not substruct_match or len(substruct_match) != mol1_copy.GetNumAtoms():
            raise ValueError(
                "Failed to establish full one-to-one atom correspondence between molecules."
            )

        return {mol1_idx + 1: mol2_idx + 1 for mol1_idx, mol2_idx in enumerate(substruct_match)}

    # -------------------------------------------------------------------------
    # CORE SHIFT ALIGNMENT FUNCTION (original logic preserved)
    # -------------------------------------------------------------------------
    def align_npmrd_curator_shifts(
        self,
        c_shifts: Optional[List[Dict]] = None,
        h_shifts: Optional[List[Dict]] = None,
    ) -> List[Dict]:
        """
        Remap the RDKit atom indices in NMR shift lists according to a 1-based
        atom index mapping derived from `get_mol1_to_mol2_index_map`.
        """
        mol1_to_mol2 = self.mol1_to_mol2
        remapped_shifts = []

        # --- 13C shifts ---
        if c_shifts:
            for entry in c_shifts:
                old_idx = entry["rdkit_index"]
                new_idx = mol1_to_mol2.get(old_idx)
                if new_idx is not None:
                    new_entry = entry.copy()
                    new_entry["rdkit_index"] = new_idx
                    remapped_shifts.append(new_entry)

        # --- 1H shifts ---
        if h_shifts:
            for entry in h_shifts:
                old_indices = entry["rdkit_index"]
                if not isinstance(old_indices, list):
                    old_indices = [old_indices]
                new_indices = [mol1_to_mol2[i] for i in old_indices if i in mol1_to_mol2]
                if new_indices:
                    new_entry = entry.copy()
                    new_entry["rdkit_index"] = new_indices[0] if len(new_indices) == 1 else new_indices
                    remapped_shifts.append(new_entry)

        return remapped_shifts

    # -------------------------------------------------------------------------
    # MAIN PUBLIC PIPELINE ENTRYPOINT
    # -------------------------------------------------------------------------
    def align(
        self,
        c_values: Optional[List[Dict]] = None,
        h_values: Optional[List[Dict]] = None
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Run the full alignment pipeline:
            1. Verify and load molecules.
            2. Create atom index mapping.
            3. Align C and H shift lists.
            4. Return the remapped lists.
        """
        print("[INFO] Starting alignment process...")

        c_aligned = []
        h_aligned = []

        if c_values:
            print("[INFO] Aligning 13C shifts...")
            c_aligned = self.align_npmrd_curator_shifts(c_shifts=c_values)
            print(f"SUCCESS: 13C shifts aligned: {len(c_aligned)} entries.")

        if h_values:
            print("[INFO] Aligning 1H shifts...")
            h_aligned = self.align_npmrd_curator_shifts(h_shifts=h_values)
            print(f"SUCCESS: 1H shifts aligned: {len(h_aligned)} entries.")

        print("SUCCESS: Alignment complete.")
        return c_aligned, h_aligned



# -------------------------------------------------------------------------
# Example Usage
# -------------------------------------------------------------------------
# if __name__ == "__main__":
#     example_curation_block = """<MOL BLOCK STRING>"""
#     example_db_block = """<MOL BLOCK STRING>"""

#     example_c_values = [{"rdkit_index": 1, "shift": 23.5}, {"rdkit_index": 2, "shift": 24.1}]
#     example_h_values = [{"rdkit_index": [3, 4], "shift": 1.25}, {"rdkit_index": 5, "shift": 1.67}]

#     aligner = MolBlockAligner(example_curation_block, example_db_block)
#     c_result, h_result = aligner.align(example_c_values, example_h_values)

#     print("\nAligned 13C shifts:", c_result)
#     print("Aligned 1H shifts:", h_result)
