import nibabel as nib

def extract_nifti_metadata(filepath):
    """
    Extracts metadata from a NIfTI file.
    """
    img = nib.load(filepath)
    header = img.header

    metadata = {
        "shape": header.get_data_shape(),
        "affine": header.get_best_affine().tolist(),
        "voxel_size": header.get_zooms(),
        "data_type": header.get_data_dtype().name,
        "description": header.get("descrip", "").decode("utf-8") if "descrip" in header else ""
    }

    return metadata

