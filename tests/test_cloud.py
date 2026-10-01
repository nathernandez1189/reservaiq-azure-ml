"""Cloud persistence contract, transport failures and the shared WSGI API."""
from io import BytesIO
import json
import unittest
from unittest.mock import patch
import uuid
import app
from booking_dates import features_from_stay
from cloud_storage import BlobReservationStore
from cloud_wsgi import application
from storage import ConflictError

class MemoryBlob:
    def __init__(self):
        self.image=None;self.etag=None;self.writes=0;self.before_write=None;self.fail=False
    def read(self): return self.image,self.etag
    def write(self,image,etag):
        if self.before_write:
            hook=self.before_write;self.before_write=None;hook()
        if self.fail: raise OSError('Unavailable')
        if etag!=self.etag: raise ConflictError('Concurrent write')
        self.image=image;self.writes+=1;self.etag=str(self.writes)

class CloudFixture(unittest.TestCase):
    def setUp(self):
        self.blob=MemoryBlob();self.store=BlobReservationStore(self.blob)
        self.stay={'booked_on':'2026-10-01','check_in':'2026-10-02','check_out':'2026-10-05'}
        self.inputs={**app.public_summary()['examples'][0]['inputs'],**features_from_stay(self.stay)}
        self.entry=app.reservation_entry({'inputs':self.inputs,'stay':self.stay,'reference':'Prueba ficticia'})
    def create(self): return self.store.create([self.entry],uuid.uuid4().hex)[0]

class CloudStoreTests(CloudFixture):
    def test_restart_preserves_calendar_inference_and_idempotency(self):
        key=uuid.uuid4().hex
        original=self.store.create([self.entry],key)
        fresh=BlobReservationStore(self.blob)
        self.assertEqual(fresh.list(),original)
        self.assertEqual(fresh.create([self.entry],key),original)
        self.assertEqual(self.blob.writes,1)
        self.assertEqual(fresh.list()[0]['stay'],self.stay)
    def test_reads_health_and_retry_do_not_write(self):
        self.assertEqual(self.store.list(),[]);self.store.check()
        self.assertEqual(self.blob.writes,0)
        self.create();before=self.blob.image
        self.store.list();self.store.check()
        self.assertEqual(self.blob.image,before);self.assertEqual(self.blob.writes,1)
    def test_invalid_batch_rolls_back_before_remote_upload(self):
        saved=self.create();image=self.blob.image
        with self.assertRaises(ValueError):
            self.store.create([self.entry,{**self.entry,'source':'invalid'}],uuid.uuid4().hex)
        self.assertEqual(self.blob.image,image);self.assertEqual(self.store.list(),[saved])
    def test_upload_failure_does_not_claim_success_or_change_snapshot(self):
        saved=self.create();self.blob.fail=True
        with self.assertRaises(OSError): self.create()
        self.assertEqual(self.store.list(),[saved])
    def test_etag_conflict_preserves_other_clients_record(self):
        self.create()
        other=BlobReservationStore(self.blob)
        self.blob.before_write=lambda:other.create([{**self.entry,'reference':'Segundo cliente'}],uuid.uuid4().hex)
        with self.assertRaises(ConflictError): self.create()
        self.assertEqual(len(other.list()),2)
        self.assertIn('Segundo cliente',[x['reference'] for x in other.list()])
    def test_revision_conflict_and_archive_restore(self):
        r=self.create()
        for status in ['reviewed','archived','pending']:
            r=self.store.set_status(r['id'],r['revision'],status)
            self.assertEqual(BlobReservationStore(self.blob).list(),[r])
        with self.assertRaises(ConflictError):self.store.set_status(r['id'],1,'archived')
    def test_full_500_batch_and_snapshot_size_guard(self):
        rows=self.store.create([self.entry]*500,uuid.uuid4().hex)
        self.assertEqual(len(rows),500);self.assertEqual(len(self.store.list()),500)
        with patch('cloud_storage.MAX_SNAPSHOT_BYTES',10):
            with self.assertRaises(OSError): self.store.list()

class WsgiTests(CloudFixture):
    def setUp(self):
        super().setUp()
        self.patcher=patch.object(app,'STORE',self.store);self.patcher.start();self.addCleanup(self.patcher.stop)
        self.origin=patch.object(app,'PUBLIC_ORIGIN','https://example.azurewebsites.net');self.origin.start();self.addCleanup(self.origin.stop)
    def call(self,path,payload=None,method=None,headers=None):
        body=json.dumps(payload).encode() if payload is not None else b''
        env={'REQUEST_METHOD':method or ('POST' if payload is not None else 'GET'),'PATH_INFO':path,'CONTENT_LENGTH':str(len(body)),'wsgi.input':BytesIO(body),**(headers or {})}
        response={}
        def start(status,h):response.update(status=int(status.split()[0]),headers=dict(h))
        response['body']=b''.join(application(env,start))
        return response
    def test_wsgi_roundtrip_save_restart_edit_and_invalid_input(self):
        payload={'inputs':self.inputs,'stay':self.stay,'request_id':uuid.uuid4().hex,'reference':'Prueba web'}
        r=self.call('/api/reservations',payload,headers={'HTTP_ORIGIN':app.PUBLIC_ORIGIN})
        self.assertEqual(r['status'],200,r['body']);saved=json.loads(r['body'])['reservation']
        app.STORE=BlobReservationStore(self.blob)
        self.assertEqual(json.loads(self.call('/api/reservations')['body'])['reservations'],[saved])
        self.assertEqual(self.call('/api/predict',{**self.inputs,'lead_time':61})['status'],400)
        self.assertEqual(self.call('/api/reservations/status',{'id':saved['id'],'revision':1,'status':'reviewed'})['status'],200)
    def test_https_origin_checks_and_static_allowlist(self):
        for h in [{'HTTP_ORIGIN':'https://evil.invalid'},{'HTTP_SEC_FETCH_SITE':'cross-site'}]:
            self.assertEqual(self.call('/api/predict',self.inputs,headers=h)['status'],403)
        self.assertEqual(self.call('/api/predict',self.inputs,headers={'HTTP_ORIGIN':app.PUBLIC_ORIGIN})['status'],200)
        self.assertEqual(self.call('/../app.py')['status'],404)
        self.assertEqual(self.call('/',method='DELETE')['status'],405)
        self.assertEqual(self.call('/',method='HEAD')['body'],b'')
        self.assertEqual(self.call('/api/health')['status'],200)
        self.assertTrue(json.loads(self.call('/api/summary')['body'])['application']['cloud'])
    def test_storage_failure_is_503_no_internal_error(self):
        self.blob.fail=True
        r=self.call('/api/reservations',{'inputs':self.inputs,'request_id':uuid.uuid4().hex})
        self.assertEqual(r['status'],503)
        self.assertNotIn(b'Traceback',r['body']);self.assertEqual(self.store.list(),[])

if __name__=='__main__':unittest.main()
