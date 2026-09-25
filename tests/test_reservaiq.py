import unittest,json,hashlib,io
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import numpy as np,pandas as pd,joblib
from core import FEATURES,validate_input,infer
from pipeline import metrics
from app import Handler,public_summary,MODEL_SHA256,AZURE_VERIFIED,PROVENANCE
ROOT=Path(__file__).resolve().parents[1]

class ReservaIQTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary=json.loads((ROOT/'artifacts/summary.json').read_text())
        cls.bundle=joblib.load(ROOT/'artifacts/trained/model.joblib')
        cls.example=cls.summary['examples'][0]['inputs']
    def test_source_integrity(self):
        self.assertEqual(hashlib.sha256((ROOT/'data/hotels.csv').read_bytes()).hexdigest(),self.summary['data']['sha256'])
    def test_partition_separation_and_label_maturity(self):
        all_ids=set();parts={}
        for name,spec in self.summary['data']['splits'].items():
            d=pd.read_csv(ROOT/f'artifacts/splits/{name}.csv');parts[name]=d
            ids=set(d.row_id);self.assertFalse(ids&all_ids);all_ids|=ids
            self.assertTrue((d.booking>=spec['booking_start']).all())
            self.assertTrue((d.booking<spec['booking_end_exclusive']).all())
            self.assertTrue((d.resolved<spec['outcome_known_before']).all())
        self.assertLess(parts['train'].resolved.max(),parts['validation'].booking.min())
        self.assertLess(parts['validation'].resolved.max(),parts['test'].booking.min())
    def test_no_outcome_or_identity_predictors(self):
        banned={'is_canceled','target','reservation_status','reservation_status_date','assigned_room_type','booking_changes','adr','deposit_type','country','agent','company'}
        self.assertFalse(banned&set(FEATURES));self.assertEqual(list(self.bundle['model'].feature_names_in_),FEATURES)
    def test_selection_only_from_validation(self):
        selection=self.summary['selection'];winner=max(selection['candidates'],key=lambda c:c['average_precision'])
        self.assertEqual(winner['name'],selection['selected'])
        best=max(selection['threshold_sweep'],key=lambda x:(x['f1'],x['precision']))
        self.assertAlmostEqual(best['threshold'],self.bundle['threshold'])
    def test_report_matches_predictions(self):
        d=pd.read_csv(ROOT/'artifacts/test_predictions.csv');actual=metrics(d.target,d.score,self.bundle['threshold'])
        for k in ['tp','tn','fp','fn','precision','recall','f1','average_precision','roc_auc']:
            self.assertAlmostEqual(actual[k],self.summary['test'][k],places=10)
    def test_model_roundtrip(self):
        for c in self.summary['examples']:
            self.assertAlmostEqual(infer(self.bundle,c['inputs'])['score'],c['score'],places=12)
    def test_loaded_model_matches_entire_holdout(self):
        frame=pd.read_csv(ROOT/'artifacts/test_predictions.csv',keep_default_na=False)
        predicted=self.bundle['model'].predict_proba(frame[FEATURES])[:,1]
        np.testing.assert_allclose(predicted,frame.score.to_numpy(),rtol=0,atol=1e-12)
    def test_reject_nonfinite_booleans_out_of_scope(self):
        for value in [float('nan'),float('inf'),True,-1,61,1.5,'30']:
            with self.subTest(value=value),self.assertRaises(ValueError):validate_input({**self.example,'lead_time':value})
    def test_reject_unknown_categories_and_extra_columns(self):
        for change in [{'country':'CO'},{'hotel':'Hotel desconocido'},{'stays_in_weekend_nights':0,'stays_in_week_nights':0}]:
            with self.assertRaises(ValueError):validate_input({**self.example,**change})
    def request(self,path,payload,origin=None):
        h=Handler.__new__(Handler);h.path=path;b=json.dumps(payload).encode();h.rfile=io.BytesIO(b)
        h.headers={'Content-Length':str(len(b))};h.server=SimpleNamespace(server_port=8765)
        if origin:h.headers['Origin']=origin
        h.respond=Mock();h.do_POST();return h.respond.call_args.args
    def test_api_single_and_batch(self):
        a=self.request('/api/predict',self.example);b=self.request('/api/batch',[self.example,self.example]);self.assertEqual(a[0],200);self.assertEqual(b[0],200)
        self.assertEqual(b[1]['count'],2);self.assertEqual(a[1]['score'],b[1]['results'][0]['score'])
    def test_api_rejects_bad_payloads(self):
        self.assertEqual(self.request('/api/predict',{})[0],400)
        self.assertEqual(self.request('/api/batch',[])[0],400)
        self.assertEqual(self.request('/api/batch',[self.example]*501)[0],400)
    def test_cross_origin_rejected(self):
        self.assertEqual(self.request('/api/predict',self.example,'https://example.invalid')[0],403)
    def test_cloud_status_is_explicit(self):
        self.assertEqual(public_summary()['azure_verified'],AZURE_VERIFIED)
        if AZURE_VERIFIED:
            self.assertEqual(PROVENANCE['job_status'],'Completed')
            self.assertEqual(PROVENANCE['model_sha256'],MODEL_SHA256)
            record=json.loads((ROOT/'azure/evidence/run.json').read_text())
            self.assertEqual(record['job_name'],PROVENANCE['job_name'])
            self.assertEqual(record['model']['sha256'],MODEL_SHA256)
            self.assertEqual({step['stage'] for step in record['steps']},{'prepare','train','evaluate'})
            self.assertTrue(all(step['status']=='Completed' for step in record['steps']))

    def test_upload_csv_matches_contract(self):
        frame=pd.read_csv(ROOT/'ejemplos-csv/reservas-listas.csv',keep_default_na=False)
        self.assertEqual(list(frame.columns),FEATURES)
        self.assertTrue(1<=len(frame)<=500)
        payload=frame.to_dict(orient='records')
        response=self.request('/api/batch',payload)
        self.assertEqual(response[0],200)
        self.assertEqual(response[1]['count'],len(frame))

if __name__=='__main__':unittest.main(verbosity=2)
