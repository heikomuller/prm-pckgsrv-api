import unittest

from prmpckgsrv.api import read_index_file


"""MongoDB database and collection used for test purposes."""
INDEX_FILE = './data/index.yaml'


class TestFileServer(unittest.TestCase):

    def test_read_file(self):
        """Test delete file method."""
        packages = read_index_file(INDEX_FILE)
        self.assertEquals(len(packages), 2)


if __name__ == '__main__':
    unittest.main()
