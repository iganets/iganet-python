import unittest
import pyiganet

class TestBSpline1d(unittest.TestCase):

    def test_create(self):
        bspline = UniformBSpline(1, 1, 10)

if __name__ == '__main__':
    unittest.main()
