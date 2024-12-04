from labdataranger.disk.dataset.scan.format import dicom, tiff
from labdataranger.disk.dataset.scan.format import extract_metadata

def test_dicom_metadata_extraction():
    result = dicom.extract_metadata("test.dcm")
    assert isinstance(result, dict)
    assert "PatientName" in result

import pytest
from labdataranger.disk.dataset.scan.format.tiff import extract_metadata
from labdataranger.disk.dataset.scan.format.tiff import _convert_value as _convert_value_tiff

def test_convert_value():
    assert _convert_value_tiff("123") == 123  # String to int
    assert _convert_value_tiff("123.45") == 123.45  # String to float
    assert _convert_value_tiff(["1", "2", "3"]) == [1, 2, 3]  # List of strings to integers
    assert _convert_value_tiff(b"binary data") == "binary data"  # Bytes to string
    assert _convert_value_tiff(b"\xff\xd8\xff") == b"\xff\xd8\xff"  # Unreadable bytes remain bytes
    assert _convert_value_tiff({"key": "value"}) == "{'key': 'value'}"  # Dictionary to string (fallback)

def test_tiff_metadata():
    filepath = "tests/files/example.tiff"  # Replace with an actual test file
    metadata = extract_metadata(filepath)
    assert isinstance(metadata, dict)
    assert 'tiff_tags' in metadata
    assert isinstance(metadata['tiff_tags'], dict)

def test_tiff_file_not_found():
    with pytest.raises(FileNotFoundError):
        extract_metadata("nonexistent_file.tiff")

def test_tiff_invalid_file():
    invalid_file = "tests/files/invalid.tiff"  # Replace with an invalid TIFF file
    with pytest.raises(ValueError):
        extract_metadata(invalid_file)

def test_generic_metadata_extraction():
    dicom_result = extract_metadata("test.dcm")
    assert "PatientName" in dicom_result

    tiff_result = extract_metadata("test.tiff")
    assert "tiff_tags" in tiff_result

import unittest
from labdataranger.disk.dataset.scan.format.dicom import extract_metadata as extract_dicom

class TestDICOMExtractor(unittest.TestCase):
    def test_extract_metadata(self):
        filepath = "tests/test_files/example.dcm"
        metadata = extract_dicom(filepath)
        self.assertIsInstance(metadata, dict)
        self.assertIn("PatientName", metadata)  # Adjust keys based on expected output
