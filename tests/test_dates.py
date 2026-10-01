"""Independent date arithmetic and non-destructive storage migration checks."""
import json
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from booking_dates import features_from_stay, validate_stay, parse_date
from storage import ReservationStore

class DateTests(unittest.TestCase):
    def test_counts_checkout_excluded_leap_year_and_dst(self):
        fixtures = [
            ('2026-10-01','2026-10-02','2026-10-05',1,10,2,1),
            ('2026-12-01','2026-12-31','2027-01-04',30,12,2,2),
            ('2028-02-01','2028-02-28','2028-03-01',27,2,0,2),
            ('2026-03-01','2026-03-07','2026-03-09',6,3,2,0),
            ('2026-10-30','2026-10-31','2026-11-02',1,10,2,0)]
        for booked,arrival,departure,lead,month,weekend,weekday in fixtures:
            with self.subTest(arrival=arrival):
                result=features_from_stay(dict(booked_on=booked,check_in=arrival,check_out=departure))
                self.assertEqual(result,dict(lead_time=lead,arrival_month=month,stays_in_weekend_nights=weekend,stays_in_week_nights=weekday))

    def test_rejects_invalid_dates_and_contract(self):
        for value in ['2026-02-29','2026-13-01','0001-01-01','2101-01-01','2026-1-02','',None,False]:
            with self.subTest(value=value), self.assertRaises(ValueError): parse_date(value)
        for value in [{},[],{'booked_on':'2026-10-01','check_in':'2026-10-02','check_out':'2026-10-05','extra':1}]:
            with self.assertRaises(ValueError):validate_stay(value)
        self.assertIsNone(validate_stay(None))

    def test_bounds_and_reversed_dates(self):
        for arrival,departure in [('2026-09-30','2026-10-02'),('2026-12-01','2026-12-02'),('2026-10-01','2026-10-01'),('2026-10-05','2026-10-02'),('2026-10-01','2026-11-01')]:
            with self.subTest(arrival=arrival,departure=departure), self.assertRaises(ValueError):
                features_from_stay(dict(booked_on='2026-10-01',check_in=arrival,check_out=departure))
        valid=dict(booked_on='2026-10-01',check_in='2026-11-30',check_out='2026-12-30')
        result=features_from_stay(valid)
        self.assertEqual(result['lead_time'],60)
        self.assertEqual(result['stays_in_weekend_nights']+result['stays_in_week_nights'],30)

    def test_migrates_v1_without_changing_saved_fields(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'legacy.sqlite3'
            with closing(sqlite3.connect(path)) as con, con:
                con.execute('CREATE TABLE reservations (id TEXT PRIMARY KEY, reference TEXT NOT NULL, inputs TEXT NOT NULL, result TEXT NOT NULL, model_sha256 TEXT NOT NULL, source TEXT NOT NULL, status TEXT NOT NULL, revision INTEGER NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)')
                row=('RI-OLD','Hernández',json.dumps({'lead_time':28}),json.dumps({'score':0.398}),'original-sha','example','reviewed',3,'created','updated')
                con.execute('INSERT INTO reservations VALUES (?,?,?,?,?,?,?,?,?,?)',row)
                con.execute('PRAGMA user_version=1')
            records=ReservationStore(path).list()
            self.assertEqual(len(records),1)
            self.assertIsNone(records[0]['stay'])
            self.assertEqual(records[0]['reference'],'Hernández')
            self.assertEqual(records[0]['revision'],3)
            self.assertEqual(records[0]['status'],'reviewed')
            with closing(sqlite3.connect(path)) as con, con:
                self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0],2)
                self.assertEqual(con.execute('SELECT id,reference,inputs,result,model_sha256,source,status,revision,created_at,updated_at FROM reservations').fetchone(),row)
            self.assertEqual(ReservationStore(path).list(),records)

    def test_refuses_future_database_version_without_overwriting_it(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'future.sqlite3'
            with closing(sqlite3.connect(path)) as con, con: con.execute('PRAGMA user_version=99')
            original=path.read_bytes()
            with self.assertRaises(ValueError):ReservationStore(path).list()
            self.assertEqual(path.read_bytes(),original)
