"""Exercise persistence through the real HTTP API with an isolated database."""
import hashlib
import json
from pathlib import Path
import tempfile
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import uuid
import app
from storage import ReservationStore
from booking_dates import features_from_stay

class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)/'reservations.sqlite3'
        self.store = ReservationStore(self.path)
        self.patcher = patch.object(app, 'STORE', self.store)
        self.patcher.start()
        self.server = app.ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'
        self.inputs = app.public_summary()['examples'][0]['inputs']
        self.hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (app.ROOT/'artifacts').rglob('*') if p.is_file()}

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()
        self.patcher.stop(); self.tmp.cleanup()
        for path, digest in self.hashes.items():
            self.assertEqual(hashlib.sha256(Path(path).read_bytes()).hexdigest(), digest, 'User saves must not change model evidence')

    def request(self, route, data=None, origin=None):
        headers = {'Content-Type':'application/json'}
        if origin: headers['Origin'] = origin
        request = Request(self.url+route, data=None if data is None else json.dumps(data).encode('utf-8'), headers=headers)
        try:
            with urlopen(request, timeout=20) as response:
                return response.status, json.loads(response.read())
        except HTTPError as response:
            return response.code, json.loads(response.read())

    def payload(self, **changes):
        return dict(inputs=self.inputs, reference='Prueba Hernández', source='manual', request_id=uuid.uuid4().hex, **changes)

    def create(self):
        status, data = self.request('/api/reservations', self.payload())
        self.assertEqual(status,200,data)
        return data['reservation']

    def test_persists_across_store_and_http_server_restart(self):
        saved=self.create()
        self.server.shutdown(); self.server.server_close(); self.thread.join()
        app.STORE = ReservationStore(self.path)
        self.server = app.ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True);self.thread.start()
        self.url=f'http://127.0.0.1:{self.server.server_port}'
        status,data=self.request('/api/reservations')
        self.assertEqual(status,200)
        self.assertEqual(data['reservations'],[saved])
        self.assertEqual(saved['inputs'],self.inputs)
        self.assertEqual(saved['result'],app.infer(app.BUNDLE,self.inputs))
        self.assertEqual(saved['model_sha256'],app.MODEL_SHA256)

    def test_duplicate_retries_are_idempotent_even_concurrently(self):
        payload=self.payload()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _: self.request('/api/reservations',payload),range(2)))
        self.assertTrue(all(status==200 for status,_ in results),results)
        self.assertEqual(results[0][1],results[1][1])
        self.assertEqual(len(self.store.list()),1)
        payload['reference']='Otra referencia'
        self.assertEqual(self.request('/api/reservations',payload)[0],409)
        self.assertEqual(len(self.store.list()),1)

    def test_edit_recalculates_same_record_and_blocks_stale_write(self):
        saved=self.create()
        changed={**saved['inputs'],'lead_time':7}
        payload={'id':saved['id'],'revision':saved['revision'],'inputs':changed,'reference':'Cambio de escenario'}
        status,response=self.request('/api/reservations/update',payload)
        updated=response['reservation']
        self.assertEqual(status,200)
        self.assertEqual(updated['created_at'],saved['created_at'])
        self.assertEqual(updated['id'],saved['id'])
        self.assertEqual(updated['revision'],2)
        self.assertEqual(updated['result'],app.infer(app.BUNDLE,changed))
        self.assertNotEqual(updated['result']['score'],saved['result']['score'])
        self.assertEqual(self.request('/api/reservations/update',payload)[0],409)
        self.assertEqual(self.store.list(),[updated])

    def test_review_archive_restore_and_conflicts(self):
        record=self.create()
        stale={'id':record['id'],'revision':1,'status':'archived'}
        for desired in ('reviewed','archived','pending'):
            status,data=self.request('/api/reservations/status',{'id':record['id'],'revision':record['revision'],'status':desired})
            self.assertEqual(status,200,data);record=data['reservation'];self.assertEqual(record['status'],desired)
            if desired=='archived':
                self.assertEqual(self.request('/api/reservations/update',{'id':record['id'],'revision':record['revision'],'inputs':record['inputs']})[0],409)
        self.assertEqual(self.request('/api/reservations/status',stale)[0],409)
        self.assertEqual(len(self.store.list()),1)

    def test_invalid_batch_is_atomic_and_valid_batch_is_retryable(self):
        first=self.create()
        data={'rows':[self.inputs,{**self.inputs,'lead_time':61}], 'request_id':uuid.uuid4().hex}
        status,response=self.request('/api/reservations/batch',data)
        self.assertEqual(status,400);self.assertIn('Fila 2',response['error'])
        self.assertEqual(self.store.list(),[first])
        data['rows']=[self.inputs,self.inputs]
        status,response=self.request('/api/reservations/batch',data)
        self.assertEqual(status,200);self.assertEqual(response['count'],2)
        self.assertEqual(self.request('/api/reservations/batch',data)[1],response)
        self.assertEqual(len(self.store.list()),3)
        self.assertEqual({r['source'] for r in response['reservations']},{'csv'})

    def test_analysis_does_not_save_and_bad_requests_do_not_save(self):
        self.assertEqual(self.request('/api/predict',self.inputs)[0],200)
        self.assertEqual(self.request('/api/batch',[self.inputs])[0],200)
        for change in ({'reference':'a'*81},{'reference':'bad\nreference'},{'source':'invented'},{'request_id':'short'},{'inputs':{**self.inputs,'lead_time':True}}):
            with self.subTest(change=change):
                payload=self.payload();payload.update(change)
                self.assertEqual(self.request('/api/reservations',payload)[0],400)
        self.assertEqual(self.request('/api/reservations',self.payload(),origin='https://external.invalid')[0],403)
        self.assertEqual(self.store.list(),[])

    def test_storage_rolls_back_mid_batch_failure(self):
        first=self.create()
        good=app.reservation_entry(self.payload())
        with self.assertRaises(ValueError):
            self.store.create([good,{**good,'source':'invalid'}],uuid.uuid4().hex)
        self.assertEqual(self.store.list(),[first])

    def test_maximum_batch_of_500_is_saved_completely(self):
        status,response=self.request('/api/reservations/batch',{'rows':[self.inputs]*500,'request_id':uuid.uuid4().hex})
        self.assertEqual(status,200,response)
        self.assertEqual(response['count'],500)
        self.assertEqual(len({r['id'] for r in response['reservations']}),500)
        self.assertEqual(len(self.store.list()),500)

    def test_calendar_predict_save_edit_and_restart_preserve_dates(self):
        stay={'booked_on':'2026-10-01','check_in':'2026-10-02','check_out':'2026-10-05'}
        inputs={**self.inputs,**features_from_stay(stay)}
        status,prediction=self.request('/api/predict',{'inputs':inputs,'stay':stay})
        self.assertEqual(status,200,prediction)
        self.assertEqual(prediction,self.request('/api/predict',inputs)[1])
        self.assertEqual(self.store.list(),[])
        payload=self.payload();payload.update(inputs=inputs,stay=stay)
        status,data=self.request('/api/reservations',payload)
        self.assertEqual(status,200,data)
        saved=data['reservation']
        self.assertEqual(saved['stay'],stay)
        self.assertEqual(ReservationStore(self.path).list(),[saved])
        self.server.shutdown();self.server.server_close();self.thread.join()
        app.STORE=ReservationStore(self.path)
        self.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
        self.thread=Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.url=f'http://127.0.0.1:{self.server.server_port}'
        self.assertEqual(self.request('/api/reservations')[1]['reservations'],[saved])
        edited={**stay,'check_out':'2026-10-06'}
        status,data=self.request('/api/reservations/update',{'id':saved['id'],'revision':1,'inputs':{**inputs,**features_from_stay(edited)},'stay':edited,'reference':'Nueva salida'})
        self.assertEqual(status,200,data)
        self.assertEqual(data['reservation']['stay'],edited)
        self.assertEqual(data['reservation']['id'],saved['id'])
        self.assertEqual(data['reservation']['revision'],2)
        self.assertEqual(len(self.store.list()),1)

    def test_calendar_rejects_inconsistent_or_invalid_metadata_without_saving(self):
        stay={'booked_on':'2026-10-01','check_in':'2026-10-02','check_out':'2026-10-05'}
        inputs={**self.inputs,**features_from_stay(stay)}
        cases=[({**inputs,'lead_time':2},stay),
               (inputs,{**stay,'check_out':'2026-10-02'}),
               (inputs,{**stay,'check_out':'2026-02-29'}),
               (inputs,{**stay,'check_in':'2026-12-05'}),
               (inputs,{**stay,'extra':True})]
        for values,dates in cases:
            with self.subTest(dates=dates):
                payload=self.payload();payload.update(inputs=values,stay=dates)
                self.assertEqual(self.request('/api/predict',{'inputs':values,'stay':dates})[0],400)
                self.assertEqual(self.request('/api/reservations',payload)[0],400)
        self.assertEqual(self.store.list(),[])

    def test_batch_limit_and_unknown_record(self):
        for rows in ([],[self.inputs]*501):
            self.assertEqual(self.request('/api/reservations/batch',{'rows':rows,'request_id':uuid.uuid4().hex})[0],400)
        self.assertEqual(self.request('/api/reservations/status',{'id':'unknown','revision':1,'status':'reviewed'})[0],404)
        self.assertEqual(self.store.list(),[])

if __name__=='__main__':unittest.main()
