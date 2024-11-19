from labdataranger.disk.dataset.scan.formats.log import parse_log_file
from labdataranger.disk.dataset.scan.formats.tiff import extract_tiff_metadata

# TODO: work with these together
# parse_log_file()
# extract_tiff_metadata()

def test_function():
    test1 = parse_log_file('/not/a/real/file')
    test2 = extract_tiff_metadata('/not/a/real/file')
    print(test1)
    print(test2)
    return
