import importlib.util,tempfile,unittest,time,sqlite3
spec=importlib.util.spec_from_file_location('app','server/app.py');app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
class Tests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.s=app.Store(self.tmp.name+'/db')
 def tearDown(self):self.s.db.close();self.tmp.cleanup()
 def test_once_and_revoke(self):
  code=self.s.issue(1,1)[0];token=self.s.redeem(code);self.assertTrue(self.s.allowed(token));self.assertIsNone(self.s.redeem(code));self.s.revoke(code);self.assertFalse(self.s.allowed(token))
 def test_invalid_expired(self):
  self.assertIsNone(self.s.redeem('bad'));code=self.s.issue(1,1)[0];self.s.db.execute('UPDATE codes SET expires=0');self.s.db.commit();self.assertIsNone(self.s.redeem(code))
 def test_session_expiry(self):
  token=self.s.redeem(self.s.issue(1,1)[0]);self.s.db.execute('UPDATE sessions SET expires=0');self.s.db.commit();self.assertFalse(self.s.allowed(token))
 def test_only_hashes_stored(self):
  c=self.s.issue(1,1)[0];self.assertNotEqual(self.s.db.execute('SELECT hash FROM codes').fetchone()[0],c)
if __name__=='__main__':unittest.main()
