import os
import unittest

if __name__ == '__main__':
    loader = unittest.TestLoader()
    cwd = os.getcwd()
    suite = loader.discover(cwd)
    runner = unittest.TextTestRunner()
    runner.run(suite)
